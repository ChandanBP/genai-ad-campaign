# agents/simple_agent.py
from google.adk.agents import BaseAgent
from google.genai import types
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext

class SimpleAgent(BaseAgent):
    name: str = "simple_agent"
    description: str = "Processes input from session state and stores a processed message."

    async def _run_async_impl(self, ctx:InvocationContext):
        events = ctx.session.events
        if events and events[0].content and events[0].content.parts:
            user_input = events[0].content.parts[0].text
        else:
            user_input = "[No input received]"


        # Yield an event. The content of this event will become the `ctx.step_input`
        # for the *next* agent in the `SequentialAgent`'s `sub_agents` list.
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"SimpleAgent completed. Processed data: {user_input}")])
        )
        print(f"--- {self.name} finished ---")