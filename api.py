from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import agents.agent
from google.genai import types
from fastapi.responses import JSONResponse
from google.genai.types import Content



app = FastAPI()

USER_ID = "demo-user"
SESSION_ID = "demo-session"
APP_NAME = "adcampaign-461015"
session_service = InMemorySessionService();


class CampaignRequest(BaseModel):
    description: str  # Only product description is needed

@app.post("/generate_campaign")
async def generate_campaign(request: CampaignRequest):
    await session_service.create_session(user_id=USER_ID, session_id=SESSION_ID,app_name=APP_NAME)
    runner = Runner(agent=agents.agent.root_agent,app_name=APP_NAME,session_service=session_service)
    content = types.Content(role="user", parts=[{"text": request.description}])
    event_stream = runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        )
    
    full_response = ""
    for event in event_stream:
        if isinstance(event.content, Content):
            # ADK Content object: extract the text parts
            for part in event.content.parts:
                if isinstance(part, dict) and "text" in part:
                    full_response += part["text"] + "\n"
                elif isinstance(part, str):
                    full_response += part + "\n"
        elif isinstance(event.content, dict):
            # Fallback for raw dicts
            if "text" in event.content:
                full_response += event.content["text"] + "\n"
            elif "output" in event.content:
                full_response += event.content["output"] + "\n"


    return JSONResponse(content={"output": full_response})
    
    