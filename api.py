from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import agents.agent
from google.genai import types
from fastapi.responses import JSONResponse



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
        if event.content and "text" in event.content:
            full_response += event.content["text"]

    return JSONResponse(content={"output": full_response})
    
    