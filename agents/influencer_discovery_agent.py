from google.adk.agents import BaseAgent
from pydantic import BaseModel
from typing import List
import requests
import yaml
import json
from google.adk.events import Event
from google.genai.types import Content,Part

# ==== Input and Output Schemas ====

class ProductInput(BaseModel):
    name: str
    features: List[str]
    target_audience: str

class InfluencerDiscoveryInputs(BaseModel):
    product: ProductInput
    mentions: List[str]

class InfluencerProfile(BaseModel):
    username: str
    followers_count: int
    bio: str
    match_score: float
    relevance_reason: str
    handle: str

class InfluencerDiscoveryOutputs(BaseModel):
    influencers: List[InfluencerProfile]

# ==== Agent Definition ====

class InfluencerDiscoveryAgent(BaseAgent):
    name: str = "influencer_discovery_agent"
    inputs: InfluencerDiscoveryInputs = None
    outputs: InfluencerDiscoveryOutputs = None

    async def _run_async_impl(self, ctx):
        product = ctx.session.state.get("product_info")
        metrics = ctx.session.state.get("social_metrics")

        if not product or not metrics:
            raise ValueError("Missing product_info or social_metrics in session state")

        # Load Twitter credentials
        with open("agents/config/twitter.yml", "r") as f:
            config = yaml.safe_load(f)
        bearer_token = config["twitter"]["bearer_token"]

        mentions = metrics.get("mentions", {})
        influencers = []
        use_mock_data = True

        if use_mock_data:
            print("⚠️ Using mock influencers from file...")
            with open("agents/config/influencers.json", "r") as f:
                raw = json.load(f)
                for r in raw:
                    profile = InfluencerProfile(
                        username=r["username"],
                        followers_count=r["followers_count"],
                        bio=r["bio"],
                        match_score=r["match_score"],
                        relevance_reason=r["relevance_reason"],
                        handle=r["handle"]
                    )
                    influencers.append(profile)
        else:
            for username in mentions:
                username = username.strip("@:")  # clean formatting from mentions
                user_data = self.lookup_user_by_username(username, bearer_token)
                if not user_data:
                    continue

                match_score, reason = self.calculate_match_score(product, user_data)
                profile = InfluencerProfile(
                    username=username,
                    followers_count=user_data.get("public_metrics", {}).get("followers_count", 0),
                    bio=user_data.get("description", ""),
                    match_score=match_score,
                    relevance_reason=reason
                )
                influencers.append(profile)
        
        
        influencers = sorted(influencers, key=lambda x: x.match_score, reverse=True)
        ctx.session.state["influencers"] = [i.dict() for i in influencers]

        result_str = "\n".join(
            [f"@{i.username} ({i.followers_count} followers) - Score: {i.match_score:.2f} - {i.relevance_reason}" for i in influencers[:5]]
        ) or "No relevant influencers found."

        yield Event(
            author=self.name,
            content=Content(parts=[Part(text=f"📢 Generated Ad Campaigns:\n{result_str}")])
        )

    def lookup_user_by_username(self, username: str, bearer_token: str) -> dict:
        url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=description,public_metrics"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")
        else:
            print(f"Failed to fetch user {username}: {response.text}")
            return None

    def calculate_match_score(self, product: ProductInput, user_data: dict) -> (float, str):
        bio = user_data.get("description", "").lower()
        keywords = [product.name.lower()] + [f.lower() for f in product.features]

        score = 0
        matched = []
        for kw in keywords:
            if kw in bio:
                score += 1
                matched.append(kw)

        followers = user_data.get("public_metrics", {}).get("followers_count", 0)
        if followers > 10000:
            score += 1  # boost for popularity

        reason = f"Matched keywords: {', '.join(matched)}; Followers: {followers}"
        return score, reason
