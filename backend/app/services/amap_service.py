# backend/app/services/amap_service.py
import httpx
from typing import Dict, List, Any, Optional
from app.config import settings

class AMapService:
    """高德地图服务类"""
    
    def __init__(self):
        self.api_key = settings.amap_api_key
        self.base_url = "https://restapi.amap.com/v3"
    
    async def get_city_code(self, city_name: str) -> Optional[str]:
        """
        根据城市名称获取城市代码（adcode）
        
        Args:
            city_name: 城市名称，如"北京"、"澳门"
        
        Returns:
            城市代码，如"110000"
        """
        url = f"{self.base_url}/config/district"
        params = {
            "keywords": city_name,
            "key": self.api_key,
            "subdistrict": 0,
            "output": "json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") != "1":
                print(f"获取城市代码失败: {data}")
                return None
            
            districts = data.get("districts", [])
            if districts:
                return districts[0].get("adcode")
            
            return None
    
    async def search_poi(self, keywords: str, city: str) -> List[Dict[str, Any]]:
        """搜索POI（兴趣点）"""
        url = f"{self.base_url}/place/text"
        params = {
            "keywords": keywords,
            "city": city,
            "key": self.api_key,
            "output": "json",
            "offset": 20
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") != "1":
                print(f"搜索失败: {data}")
                return []
            
            results = data.get("pois", [])
            
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
        # 先获取城市代码
        city_code = await self.get_city_code(city)
        
        if not city_code:
            print(f"无法获取{city}的城市代码")
            return []
        
        # 使用城市代码查询天气
        url = f"{self.base_url}/weather/weatherInfo"
        params = {
            "city": city_code,
            "key": self.api_key,
            "extensions": "all",
            "output": "json"
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