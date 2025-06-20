# agents/ad_content_generator_agent.py

from google.adk.agents import BaseAgent
from google.cloud import storage
from agents.video_generator import VideoGenerator
from google.oauth2 import service_account
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.vision_models import ImageGenerationModel
from vertexai.generative_models import GenerativeModel
import os
import base64
import shutil
from google.genai import types
from google.adk.events import Event
from moviepy import ImageClip,TextClip,CompositeVideoClip, ColorClip

class AdAsset(BaseModel):
    ad_text: str
    image_path: Optional[str] = None
    video_script: Optional[str] = None
    video_path: Optional[str] = None

class ProductInfo(BaseModel):
    name: str
    features: List[str]
    target_audience: str


class InfluencerProfile(BaseModel):
    handle: str
    bio: str


class AdContentGeneratorInputs(BaseModel):
    product: ProductInfo
    influencers: List[InfluencerProfile]


class AdContentGeneratorOutputs(BaseModel):
    ads: Dict[str, AdAsset] = Field(
        ..., description="Generated ad copy per influencer handle"
    )


class AdContentGenerator(BaseAgent):
    name:str = "ad_content_generator"

    def generate_video_from_script(self, script: str, image_path: str, influencer_handle: str) -> str:
        # Text settings
        duration = 10  # Placeholder: 10 seconds

        # Load image background
        background = ImageClip(image_path,duration=duration)

        # Add script text
        text = TextClip(text="Go Vegan", color='white', size=background.size, method='caption',font_size=36,duration=duration)

        # Composite video
        video = CompositeVideoClip([background, text])
        video_path = f"campaign_assets/{influencer_handle}_ad_video.mp4"
        video.write_videofile(video_path, fps=24)

        return video_path
    
    def generate_image(self, prompt: str, save_path: str):
        model = GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(prompt, generation_config={"image": True})
        image_data = response.candidates[0].image
        image_bytes = base64.b64decode(image_data)
        with open(save_path, "wb") as f:
            f.write(image_bytes)

    def upload_to_gcs(self, local_path: str, bucket_name: str, destination_blob_name: str) -> str:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        blob.make_public()
        print(f"Uploaded {local_path} to GCS: {blob.public_url}")
        return blob.public_url

    def generate_ad_content(self, product, influencers):
        if isinstance(product, dict):
            product = ProductInfo(**product)

        # Load Vertex credentials
        credentials = service_account.Credentials.from_service_account_file(
            'agents/config/vertexai.json'
        )

        vertexai.init(
            project="adcampaign-461015",
            location="us-central1"
        )

        model = GenerativeModel("gemini-2.0-flash-001")
        image_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        video_generator = VideoGenerator(
            project_id="adcampaign-461015",
            location="us-central1",
            credentials_path='agents/config/vertexai.json'
        )

        ads = {}
        campaign_dir = f"campaigns/{product.name.replace(' ', '_')}"
        os.makedirs(campaign_dir, exist_ok=True)
        for influencer in influencers:
            prompt = (
                f"You are a creative ad copywriter. Your task is to generate a short, punchy ad for {product.name}. "
                f"The product is designed for {product.target_audience} and offers features like {', '.join(product.features)}.\n"
                f"The ad should match the tone of the influencer @{influencer.handle} — here is their bio: \"{influencer.bio}\".\n"
                f"Keep the tone natural and compelling. End with a strong call to action."
            )

            response = model.generate_content(prompt)
            ad_text = response.text.strip()
            
            # Image Generation Prompt
            image_prompt = f"Create a vibrant promotional image for {product.name} featuring {', '.join(product.features)} for {product.target_audience}."
            image_gcs_url = None
            try:
                img_response = image_model.generate_images(prompt=image_prompt, number_of_images=1)
                image = img_response.images[0]
                image_path = f"campaign_assets/{influencer.handle.strip('@')}_ad_image.png"
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)

                image_gcs_path = f"campaign_assets/{product.name.replace(' ', '_')}/{influencer.handle.strip('@')}_ad_image.png"
                image_gcs_url = self.upload_to_gcs(image_path, bucket_name="adcampaign-461015-image-output", destination_blob_name=image_gcs_path)
            except Exception as e:
                print(f"⚠️ Image generation failed for {influencer.handle}: {e}")
                image_path = None

            # video generation
            # Video Script Prompt
            video_prompt = (
                f"Write a short 8 second video ad script for {product.name}. "
                f"The product features are: {', '.join(product.features)}. "
                f"Target audience: {product.target_audience}. "
                f"Style it for social media (Instagram Reels, TikTok). "
                f"Tone should match the influencer @{influencer.handle} whose bio is: '{influencer.bio}'. "
                f"Include visual actions, music suggestions, and captions if possible."
            )

            try:
                video_path = video_generator.generate_video(
                    prompt=video_prompt,
                    influencer_handle=influencer.handle
                )
            except Exception as e:
                print(f"⚠️ Video generation failed for {influencer.handle}: {e}")
                video_path =  self.generate_video_fallback(prompt,influencer.handle,image_path)

            # If URL (HTTPS), download it locally
            if video_path.startswith("https://"):
                import urllib.request
                video_path = f"campaign_assets/{influencer.handle}/{influencer.handle}_ad_video.mp4"
                urllib.request.urlretrieve(video_path, video_path)
            

            ads[influencer.handle] = {
                "ad_text": ad_text,
                "image_path": image_gcs_url,
                "video_script": video_prompt,
                "video_path":video_path
            }

        return ads

    def generate_video_fallback(self, script: str, influencer_handle: str, image_path: str = None) -> str:

        duration = 10
        background = ImageClip(image_path, duration=duration) if image_path else ColorClip(size=(1280, 720), color=(0, 0, 0), duration=duration)
        text = TextClip(script, fontsize=32, color='white', method='caption', size=background.size, duration=duration)
        video = CompositeVideoClip([background, text])
        path = f"campaign_assets/{influencer_handle.strip('@')}_fallback_video.mp4"
        video.write_videofile(path, fps=24)
        return path

    async def _run_async_impl(self, ctx):
        product = ctx.session.state.get("product_info")
        influencers_data = ctx.session.state["influencers"]

        if not product or not influencers_data:
            raise ValueError("Missing product_info or influencers in session state")

        influencers = []
        for data in influencers_data:
            influencers.append(InfluencerProfile(**data))

        ads = self.generate_ad_content(product, influencers)
        summary = "\n".join([
            f"📣 Ad for @{handle}:\n📝 {content['ad_text']}\n📷 {content['image_path']}\n🎬 {content['video_path']}"
            for handle, content in ads.items()
        ]) or "No ad content generated."

        yield Event(author=self.name, content=types.Content(parts=[types.Part(text=summary)]))
    
    def export_campaign_assets(influencer_handle, ad_text, image_path, video_path):
        folder = f"campaign_assets/{influencer_handle}"
        os.makedirs(folder, exist_ok=True)

        with open(f"{folder}/ad_text.txt", "w") as f:
            f.write(ad_text)

        shutil.move(image_path, f"{folder}/ad_image.png")
        shutil.move(video_path, f"{folder}/ad_video.mp4")

        print(f"📁 Assets saved for @{influencer_handle}")