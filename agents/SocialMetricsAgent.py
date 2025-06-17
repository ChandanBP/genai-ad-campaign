# agents/social_metrics_agent.py

from google.adk.agents import BaseAgent
from pydantic import BaseModel
from typing import List, Dict
import yaml
import json
import requests
import time
from google.adk.events import Event
from google.genai.types import Content,Part

class ProductInput(BaseModel):
    name: str = ''
    description: str
    features: List[str]
    target_audience: str


class SocialMetricsInputs(BaseModel):
    product: ProductInput


class SocialMetricsOutputs(BaseModel):
    tweet_count: int
    hashtags: Dict[str, int]
    mentions: Dict[str, int]


MOCK_DATA = True

class SocialMetricsAgent(BaseAgent):
    name:str = "social_metrics_agent"
    inputs: SocialMetricsInputs = None
    outputs: SocialMetricsOutputs = None

    def __init__(self, name="product_info_agent"):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx):
        with open("agents/config/twitter.yml", "r") as f:
            config = yaml.safe_load(f)

        bearer_token = config["twitter"]["bearer_token"]
        product = ctx.session.state.get("product_info")

        print("product**********",product)
        if not product:
            # Optionally fail gracefully
            raise ValueError("No product info found in session state")

        keywords = product['features'] + [product['name']]
        query = " OR ".join(keywords)

        if MOCK_DATA:
            with open("agents/config/twitter_mentions.json") as f:
                metrics = json.load(f)
        else:
            tweets = self.search_twitter(query, bearer_token)
            metrics = self.extract_metrics(tweets)
        
        ctx.session.state["social_metrics"] = metrics
        # ✅ Yield readable summary for downstream agent
        summary_str = (
            f"📊 Social Metrics:\n"
            + "\n".join([f"- {k}: {v}" for k, v in metrics.items()])
        )
        yield Event(
            author=self.name,
            content=Content(parts=[Part(text=summary_str)])
        )
    
    def search_twitter(self, query: str, bearer_token: str, max_tweets: int = 50) -> list:
        print(f"\n🔍 Searching Twitter for query: {query}\n")
        
        headers = {
            "Authorization": f"Bearer {bearer_token}"
        }
        
        url = "https://api.twitter.com/2/tweets/search/recent"
        
        params = {
            "query": query,
            "max_results": 25,  # Max per page (10–100 depending on tier)
            "tweet.fields": "author_id,created_at,text",
        }

        tweets = []
        next_token = None
        attempts = 0

        while len(tweets) < max_tweets and attempts < 5:
            if next_token:
                params["next_token"] = next_token

            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Twitter API error {response.status_code}: {response.text}")
                break

            data = response.json()
            print(f"✅ Batch fetched: {len(data.get('data', []))} tweets")

            tweets.extend(data.get("data", []))

            # Stop if there's no next page
            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break

            time.sleep(1)  # Be polite to the API
            attempts += 1

        print(f"📊 Total tweets collected: {len(tweets)}\n")
        return tweets

    def extract_metrics(self, tweets):
        hashtags, mentions = {}, {}
        for tweet in tweets:
            for word in tweet["text"].split():
                if word.startswith("#"):
                    hashtags[word] = hashtags.get(word, 0) + 1
                elif word.startswith("@"):
                    mentions[word] = mentions.get(word, 0) + 1
        return {
            "tweet_count": len(tweets),
            "hashtags": hashtags,
            "mentions": mentions
        }
