import time
import os
from google import genai
from google.genai import types
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import urllib.request


class VideoGenerator:
    def __init__(self, project_id, location, credentials_path):
        self.project_id = project_id
        self.location = location
        self.credentials_path = credentials_path
        self.client = self._init_client()

    def _init_client(self):
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        #creds.refresh(Request())
        return genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

    def generate_video(self, prompt: str, influencer_handle: str, output_gcs: str = "", duration_seconds: int = 8):
        #model = "veo-3.0-generate-preview"
        model = "veo-2.0-generate-001"
        
        campaign_dir = "campaign_assets"
        os.makedirs(campaign_dir, exist_ok=True)
        local_path = f"{campaign_dir}/{influencer_handle.strip('@')}_ad_video.mp4"

        operation = self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                output_gcs_uri="gs://adcampaign-461015-veo-output",
                number_of_videos=1,
                duration_seconds=duration_seconds,
                person_generation="allow_adult",
                enhance_prompt=True,
                generate_audio=False,
            ),
        )

        print("⏳ Waiting for Veo video generation to complete...")
        elapsed = 0
        MAX_WAIT_MINUTES = 6
        POLL_INTERVAL_SECONDS = 10
        
        
        while not operation.done:
            if elapsed > MAX_WAIT_MINUTES * 60:
                raise TimeoutError("⏱️ Veo video generation timed out after 5 minutes.")

            print(f"⏳ Waiting for Veo... Elapsed: {elapsed}s")
            time.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS
            operation = self.client.operations.get(operation)
            print(".", end="", flush=True)

        # Once the operation is done
        if operation.response and operation.result.generated_videos:
            video_uri = operation.result.generated_videos[0].video.uri
            print(f"\n✅ Video URI: {video_uri}")

            if video_uri.startswith("https://") and local_path:
                urllib.request.urlretrieve(video_uri, local_path)
                print(f"📥 Downloaded video to {local_path}")
                return local_path
            else:
                return video_uri
        else:
            raise RuntimeError("❌ Video generation failed.",operation.error)

        
