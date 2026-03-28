#weather_agent.py
from app.services.amap_service import amap_service


class WeatherQueryAgent:
    async def run(self, city: str):
        try:
            return await amap_service.get_weather(city)
        except Exception as exc:
            print(f"[WeatherAgent] 天气服务异常，已跳过天气数据: city={city}, error={exc}")
            return []
