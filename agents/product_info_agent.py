import json
import re
from google.adk.agents import BaseAgent
from pydantic import BaseModel
from typing import List
from google.genai import types
from google.adk.events import Event
from vertexai.preview.generative_models import GenerativeModel


class ProductInfoAgentInputs(BaseModel):
    raw_description: str

class ProductInfo(BaseModel):
    name: str
    description: str
    features: List[str]
    target_audience: str

class ProductInfoAgentOutputs(BaseModel):
    product: ProductInfo

class ProductInfoAgent(BaseAgent):
    
    name: str = "product_info_agent"

    def __init__(self, name="product_info_agent"):
        super().__init__(name=name)
        object.__setattr__(self, "_model", GenerativeModel("gemini-2.0-flash-001"))

    async def _run_async_impl(self, ctx):
        # ✅ Access user message properly
        events = ctx.session.events
        if events and events[0].content and events[0].content.parts:
            raw_text = events[0].content.parts[0].text
        else:
            raw_text = "[No input received]"

        print("Product description", raw_text)

        prompt = f"""
        Extract structured product info from the following description:
        ---
        {raw_text}
        ---
        Return JSON in this format:
        {{
            "name": "...",
            "description": "...",
            "features": ["...", "..."],
            "target_audience": "..."
        }}
        """

        response = None
        try:
            response = self._model.generate_content(prompt)
            data = response.text.strip()

            if data.startswith("```json"):
                data = re.sub(r"^```json", "", data).strip()
            if data.endswith("```"):
                data = re.sub(r"```$", "", data).strip()

            parsed = json.loads(data)

            result_str = (
                f"📦 name: {parsed.get('name')}\n"
                f"📝 description: {parsed.get('description')}\n"
                f"🔧 features: {', '.join(parsed.get('features', []))}\n"
                f"🎯 target_audience: {parsed.get('target_audience')}"
            )
            ctx.session.state["product_info"] = parsed
            yield Event(author=self.name, content=types.Content(parts=[types.Part(text=result_str)]))

        except Exception as e:
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"❌ Error: {e}\nRaw Response: {response.text.strip()}")])
            )