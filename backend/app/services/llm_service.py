# backend/app/services/llm_service.py
import httpx
import json
from app.config import settings

class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.deepseek_model

    async def ask_ai(self, prompt: str, system_prompt: str = "你是一个专业的旅行规划专家"):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"} # 强制返回JSON
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
            result = response.json()
            return json.loads(result['choices'][0]['message']['content'])

llm_service = LLMService()