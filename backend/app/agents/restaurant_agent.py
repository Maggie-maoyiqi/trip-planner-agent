import json
from app.services.amap_service import amap_service
from app.services.llm_service import llm_service

class RestaurantAgent:
    def __init__(self):
        self.name = "餐饮推荐专家"

    async def run(self, city: str, preferences: str):
        # 1. 搜索当地早餐和特色菜（POI搜索）
        # 搜索词设为“早餐”或“特色餐饮”
        raw_restaurants = await amap_service.search_poi(f"{city}特色早餐", city)
        
        # 2. 让 AI 筛选符合偏好的餐厅并预估人均消费
        system_prompt = "你是一个美食博主。请从 POI 列表中筛选出 5 家最值得去的早餐厅或当地特色餐厅，并估算人均价格。"
        user_prompt = f"城市：{city}\n偏好：{preferences}\n餐厅列表：{json.dumps(raw_restaurants[:10], ensure_ascii=False)}"
        
        # 期望返回: {"restaurants": [{"name":..., "address":..., "avg_price":..., "description":...}]}
        result = await llm_service.ask_ai(user_prompt, system_prompt)
        return result.get("restaurants", [])