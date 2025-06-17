# main.py
from google.adk.agents.sequential_agent import SequentialAgent

# Import your custom agents
from agents.product_info_agent import ProductInfoAgent
from agents.SocialMetricsAgent import SocialMetricsAgent
from agents.influencer_discovery_agent import InfluencerDiscoveryAgent
from agents.ad_content_generator_agent import AdContentGenerator


# --- ADK Application Setup ---
APP_NAME = "ad_campaign_app"

# 1. Define the root_agent (SequentialAgent) directly with instances of sub-agents
#    Since we're not using AgentApp for global registration, we provide instances.
root_agent = SequentialAgent(
    name="AdCampaignPipeline", # Name is still useful for logging/identification
    description="Sequential pipeline to generate a personalized ad campaign.",
    sub_agents=[
        ProductInfoAgent(), # Pass an instance of SimpleAgent
        SocialMetricsAgent(),
        InfluencerDiscoveryAgent(),
        AdContentGenerator(),
    ],
)