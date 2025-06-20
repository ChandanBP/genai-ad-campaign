# 🧠 GenAI-Powered Influencer Ad Campaign Generator

## 🚀 Project Overview

This project automates the generation of influencer-driven ad campaigns using Google Cloud's Vertex AI and the Agent Development Kit (ADK). It takes a **product description** as input and produces a personalized marketing campaign, complete with:

- Identified and ranked influencers
- Social media metric insights
- AI-generated ad copy
- AI-generated product image
- AI-generated product video
- Campaign assets folder in GCS

## 🧩 Key Features

- 🧠 **GenAI Agents Orchestration** using Google’s Agent Development Kit
- 🧍‍♀️ **Influencer Discovery** via semantic search and profile filtering
- 📊 **Social Metrics Analysis** using platform metadata
- ✍️ **Ad Content Generation** powered by Gemini Pro
- 🖼️ **Product Image Generation** with Imagen
- 🎬 **Video Generation** using Veo
- ☁️ **Automated Export** to Google Cloud Storage
- 🌐 **REST API** exposed via FastAPI and deployed on Cloud Run

## 🏗️ Architecture

![Architecture Diagram](assets/architecture.png)

### Components:

- `influencer_discovery_agent`: Identifies relevant influencers.
- `social_metrics_agent`: Fetches engagement metrics for ranked influencers.
- `ad_content_generator`: Crafts marketing content based on product + influencer data.
- `orchestrator_agent`: Manages sequential execution using `SequentialAgent`.

**Cloud Services Used:**

- Vertex AI (Gemini, Imagen, Veo)
- Cloud Run (API deployment)
- Artifact Registry (Docker image)
- GCS (for campaign export)
- ADK v1.2.1

## 📦 Technologies Used

- Python 3.10
- [Google Agent Development Kit (ADK)](https://github.com/google/agent-development-kit)
- FastAPI
- Vertex AI Gemini / Imagen / Veo
- GCS for asset management
- Docker + Cloud Run

## 🌐 Live API Endpoint


### Sample cURL Request

```bash
curl --location 'https://adk-agent-api-757787387443.us-central1.run.app/generate_campaign' \
--header 'Content-Type: application/json' \
--data '{
  "description": "A new vegan protein bar packed with 25g protein, zero sugar, and high fiber, designed for fitness enthusiasts and millennials."
}'


How to Run Locally
Step 1: Install ADK
pip install google-adk

Step 2: Run the agent-based app
adk run agents

Step 3: Or run the FastAPI server
uvicorn api:app --host 0.0.0.0 --port 8000


Git Repo: https://github.com/ChandanBP/genai-ad-campaign


NOTE: Twitter API are used to fetch real time social media data, however since the account used is free tier,
number of api hits are limited and mock data has been used. We can replace the twitter account credentials which
has abundant api limits and run the project.


Given the above situation, right now the mock data is for protein bar data and api hit from postman will generate
ad content related to health only.

We need to replace twitter api credentials, to get more api credits and hence experience real time data along with
ad content.