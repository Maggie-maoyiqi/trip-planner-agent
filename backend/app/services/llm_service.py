import json
from typing import Any, Dict, List

import httpx

from app.config import settings


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.model = settings.deepseek_model

    async def ask_ai(
        self,
        prompt: str,
        system_prompt: str = "你是一个专业的旅行规划专家",
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)

    async def rank_attractions(
        self,
        city: str,
        preferences: str,
        days: int,
        weather: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prompt = f"""
请你为城市旅行做景点筛选，输出 JSON。
城市：{city}
偏好：{preferences}
旅行天数：{days}
天气：{json.dumps(weather[:days], ensure_ascii=False)}
候选景点：{json.dumps(candidates[: min(len(candidates), days * 8)], ensure_ascii=False)}

请返回：
{{
  "summary": "整体推荐逻辑",
  "attractions": [
    {{
      "name": "景点名",
      "ticket_price": 0,
      "visit_duration": 120,
      "best_visit_time": "上午/下午/晚上",
      "llm_reason": "为什么值得去",
      "crowd_level": "高/中/低"
    }}
  ]
}}

要求：
1. 选出最值得安排的 {days * 4} 个以内景点。
2. 优先选择该城市热门、代表性强、适合游客首次体验的景点。
3. 合理估算门票与游玩时长，免费请填 0。
4. 只从候选列表中选，不要编造新景点。
"""
        return await self.ask_ai(prompt)

    async def choose_restaurants(
        self,
        city: str,
        budget: str,
        preferences: str,
        day_context: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prompt = f"""
请为一日行程挑选餐厅并预估消费，输出 JSON。
城市：{city}
预算：{budget}
用户偏好：{preferences}
当天上下文：{json.dumps(day_context, ensure_ascii=False)}
候选餐厅：{json.dumps(candidates[:12], ensure_ascii=False)}

返回格式：
{{
  "meals": [
    {{
      "meal_type": "早餐/午餐/晚餐",
      "name": "餐厅名",
      "estimated_cost_per_person": 0,
      "suggestion": "推荐理由"
    }}
  ]
}}

要求：
1. 从候选中各选 1 家，合计最多 3 家。
2. 结合预算给出合理人均估算。
3. 午餐尽量靠近午后景点，晚餐尽量靠近傍晚景点或酒店。
"""
        return await self.ask_ai(prompt, system_prompt="你是一个熟悉本地美食与旅行行程衔接的美食规划师")

    async def build_daily_plan(
        self,
        city: str,
        preferences: str,
        transportation: str,
        weather: Dict[str, Any],
        attractions: List[Dict[str, Any]],
        meals: List[Dict[str, Any]],
        location_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
请基于给定景点和餐厅，为一天旅行生成时段安排，输出 JSON。
城市：{city}
偏好：{preferences}
市内交通偏好：{transportation}
天气：{json.dumps(weather, ensure_ascii=False)}
景点：{json.dumps(attractions, ensure_ascii=False)}
餐厅：{json.dumps(meals, ensure_ascii=False)}
位置关系：{json.dumps(location_context, ensure_ascii=False)}

时间预算：
- 上午可游玩约 3 小时
- 下午可游玩约 4 小时
- 晚上可游玩约 3 小时或休息

返回格式：
{{
  "day_summary": "这一天如何安排",
  "clothing_recommendation": "穿衣建议",
  "schedule": [
    {{
      "time_slot": "上午/午餐/下午/晚餐/晚上",
      "start_time": "09:00",
      "end_time": "11:30",
      "item_type": "attraction/meal/rest",
      "title": "安排标题",
      "reference_name": "对应景点/餐厅名，没有则为空",
      "duration_minutes": 150,
      "estimated_cost": 0,
      "note": "安排理由"
    }}
  ]
}}

要求：
1. 安排顺序应符合常见出游节奏，不要时间重叠。
2. 优先把热门景点放进白天，夜景类可安排晚上。
3. 必须显式考虑点位之间的位置关系，距离近的景点和餐厅尽量安排在同一时段或相邻时段，尽量减少跨城折返。
4. 如果两个景点直线距离明显较远，应避免连续安排，除非它们是当天最重要景点。
5. 如果天气不佳，说明如何调整节奏或优先室内景点。
6. 不要新增未提供的景点或餐厅。
"""
        return await self.ask_ai(prompt)


llm_service = LLMService()
