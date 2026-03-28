#weather_agent.py
from app.services.amap_service import amap_service


class WeatherQueryAgent:
    async def run(self, city: str):
        return await amap_service.get_weather(city)