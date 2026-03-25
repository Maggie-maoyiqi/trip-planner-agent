# backend/app/services/amap_service.py
import httpx
from typing import Dict, List, Any, Optional
from app.config import settings

class AMapService:
    """高德地图服务类"""
    
    def __init__(self):
        self.api_key = settings.amap_api_key
        self.base_url = "https://restapi.amap.com/v3"
    
    async def search_poi(self, keywords: str, city: str) -> List[Dict[str, Any]]:
        """
        搜索POI（兴趣点），如景点、酒店、餐厅
        
        Args:
            keywords: 搜索关键词，如"景点"、"酒店"
            city: 城市名称，如"北京"
        
        Returns:
            搜索结果列表
        """
        url = f"{self.base_url}/place/text"
        params = {
            "keywords": keywords,
            "city": city,
            "key": self.api_key,
            "output": "json",
            "offset": 20  # 最多返回20条结果
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") != "1":
                print(f"搜索失败: {data}")
                return []
            
            results = data.get("pois", [])
            
            # 转换为统一格式
            formatted_results = []
            for poi in results:
                location = poi.get("location", "").split(",")
                formatted_results.append({
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "longitude": float(location[0]) if len(location) > 0 else 0,
                    "latitude": float(location[1]) if len(location) > 1 else 0,
                    "type": poi.get("type", ""),
                    "typecode": poi.get("typecode", ""),
                    "pname": poi.get("pname", ""),
                    "cityname": poi.get("cityname", ""),
                    "adname": poi.get("adname", "")
                })
            
            return formatted_results
    
    async def get_weather(self, city: str) -> List[Dict[str, Any]]:
        """
        查询天气信息
        
        Args:
            city: 城市名称
        
        Returns:
            天气预报列表
        """
        url = f"{self.base_url}/weather/weatherInfo"
        params = {
            "city": city,
            "key": self.api_key,
            "extensions": "all"  # 返回未来几天的预报
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") != "1":
                print(f"天气查询失败: {data}")
                return []
            
            forecasts = data.get("forecasts", [])
            if not forecasts:
                return []
            
            # 获取未来几天的天气预报
            casts = forecasts[0].get("casts", [])
            
            formatted_weather = []
            for cast in casts:
                formatted_weather.append({
                    "date": cast.get("date", ""),
                    "day_weather": cast.get("dayweather", ""),
                    "night_weather": cast.get("nightweather", ""),
                    "day_temp": cast.get("daytemp", "0"),
                    "night_temp": cast.get("nighttemp", "0"),
                    "wind_direction": cast.get("daywind", ""),
                    "wind_power": cast.get("daypower", "")
                })
            
            return formatted_weather

# 创建全局实例
amap_service = AMapService()