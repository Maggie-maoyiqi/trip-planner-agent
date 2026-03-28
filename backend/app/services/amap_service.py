from typing import Any, Dict, List, Optional

import httpx

from app.config import settings


class AMapService:
    """高德地图服务类"""

    def __init__(self):
        self.api_key = settings.amap_api_key
        self.base_url = "https://restapi.amap.com/v3"

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{path}",
                params={**params, "key": self.api_key, "output": "json"},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                raise ValueError(f"AMap API failed on {path}: {data}")
            return data

    def _parse_polyline(self, polyline: str) -> List[Dict[str, float]]:
        points: List[Dict[str, float]] = []
        if not polyline:
            return points
        for pair in polyline.split(";"):
            lng_lat = pair.split(",")
            if len(lng_lat) != 2:
                continue
            points.append({
                "longitude": float(lng_lat[0]),
                "latitude": float(lng_lat[1]),
            })
        return points

    async def get_city_code(self, city_name: str) -> Optional[str]:
        try:
            data = await self._get(
                "config/district",
                {"keywords": city_name, "subdistrict": 0},
            )
            districts = data.get("districts", [])
            return districts[0].get("adcode") if districts else None
        except Exception as exc:
            print(f"[AMap] 获取城市编码失败: city={city_name}, error={exc}")
            return None

    async def search_poi(self, keywords: str, city: str, offset: int = 20) -> List[Dict[str, Any]]:
        data = await self._get(
            "place/text",
            {
                "keywords": keywords,
                "city": city,
                "offset": offset,
                "page": 1,
                "citylimit": "true",
            },
        )
        results = data.get("pois", [])

        formatted_results = []
        for poi in results:
            location = poi.get("location", "").split(",")
            formatted_results.append({
                "name": poi.get("name", ""),
                "address": poi.get("address", ""),
                "longitude": float(location[0]) if len(location) > 0 and location[0] else 0,
                "latitude": float(location[1]) if len(location) > 1 and location[1] else 0,
                "type": poi.get("type", ""),
                "typecode": poi.get("typecode", ""),
                "pname": poi.get("pname", ""),
                "cityname": poi.get("cityname", ""),
                "adname": poi.get("adname", ""),
                "tel": poi.get("tel", ""),
                "business_area": poi.get("business_area", ""),
            })
        return formatted_results

    async def get_weather(self, city: str) -> List[Dict[str, Any]]:
        city_code = await self.get_city_code(city)
        weather_queries = []
        if city_code:
            weather_queries.append({"city": city_code, "extensions": "all"})
        weather_queries.append({"city": city, "extensions": "all"})
        if city_code:
            weather_queries.append({"city": city_code, "extensions": "base"})
        weather_queries.append({"city": city, "extensions": "base"})

        last_error: Exception | None = None
        for params in weather_queries:
            try:
                data = await self._get("weather/weatherInfo", params)
                if params["extensions"] == "all":
                    formatted = self._format_forecast_weather(data)
                else:
                    formatted = self._format_live_weather(data)
                if formatted:
                    return formatted
            except Exception as exc:
                last_error = exc
                print(f"[AMap] 天气查询尝试失败: params={params}, error={exc}")

        print(f"[AMap] 天气查询全部失败，已降级为空天气: city={city}, adcode={city_code}, error={last_error}")
        return []

    def _format_forecast_weather(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                "wind_power": cast.get("daypower", ""),
            })
        return formatted_weather

    def _format_live_weather(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        lives = data.get("lives", [])
        if not lives:
            return []
        live = lives[0]
        return [{
            "date": live.get("reporttime", "").split(" ")[0],
            "day_weather": live.get("weather", ""),
            "night_weather": live.get("weather", ""),
            "day_temp": live.get("temperature", "0"),
            "night_temp": live.get("temperature", "0"),
            "wind_direction": live.get("winddirection", ""),
            "wind_power": live.get("windpower", ""),
        }]

    async def route_plan(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        city: str,
        preferred_mode: str,
    ) -> Dict[str, Any]:
        origin_str = f"{origin['longitude']},{origin['latitude']}"
        destination_str = f"{destination['longitude']},{destination['latitude']}"
        preferred_mode = preferred_mode or "公交"

        if preferred_mode == "自驾":
            return await self._driving_route(origin_str, destination_str)
        if preferred_mode == "骑行":
            return await self._riding_route(origin_str, destination_str)

        walking = await self._walking_route(origin_str, destination_str)
        if walking.get("distance_km", 0) <= 1.5:
            return walking

        transit = await self._transit_route(origin_str, destination_str, city)
        if transit:
            return transit

        return walking if preferred_mode == "公交" else await self._driving_route(origin_str, destination_str)

    async def _walking_route(self, origin: str, destination: str) -> Dict[str, Any]:
        data = await self._get(
            "direction/walking",
            {"origin": origin, "destination": destination},
        )
        paths = data.get("route", {}).get("paths", [])
        if not paths:
            return self._empty_route("步行")
        path = paths[0]
        return {
            "mode": "步行",
            "distance_km": round(float(path.get("distance", 0)) / 1000, 2),
            "duration_minutes": round(float(path.get("duration", 0)) / 60),
            "instruction": "，".join(
                step.get("instruction", "") for step in path.get("steps", [])[:3] if step.get("instruction")
            ),
            "polyline": self._parse_polyline(path.get("steps", [{}])[0].get("polyline", "")) if path.get("steps") else [],
        }

    async def _driving_route(self, origin: str, destination: str) -> Dict[str, Any]:
        data = await self._get(
            "direction/driving",
            {"origin": origin, "destination": destination, "strategy": 0},
        )
        paths = data.get("route", {}).get("paths", [])
        if not paths:
            return self._empty_route("驾车")
        path = paths[0]
        polyline: List[Dict[str, float]] = []
        instructions = []
        for step in path.get("steps", [])[:3]:
            instructions.append(step.get("instruction", ""))
            polyline.extend(self._parse_polyline(step.get("polyline", "")))
        return {
            "mode": "驾车",
            "distance_km": round(float(path.get("distance", 0)) / 1000, 2),
            "duration_minutes": round(float(path.get("duration", 0)) / 60),
            "instruction": "，".join(filter(None, instructions)),
            "polyline": polyline,
        }

    async def _riding_route(self, origin: str, destination: str) -> Dict[str, Any]:
        data = await self._get(
            "direction/bicycling",
            {"origin": origin, "destination": destination},
        )
        paths = data.get("data", {}).get("paths", [])
        if not paths:
            return self._empty_route("骑行")
        path = paths[0]
        return {
            "mode": "骑行",
            "distance_km": round(float(path.get("distance", 0)) / 1000, 2),
            "duration_minutes": round(float(path.get("duration", 0)) / 60),
            "instruction": "，".join(
                step.get("instruction", "") for step in path.get("steps", [])[:3] if step.get("instruction")
            ),
            "polyline": self._parse_polyline(path.get("steps", [{}])[0].get("polyline", "")) if path.get("steps") else [],
        }

    async def _transit_route(self, origin: str, destination: str, city: str) -> Optional[Dict[str, Any]]:
        city_code = await self.get_city_code(city)
        if not city_code:
            return None
        data = await self._get(
            "direction/transit/integrated",
            {
                "origin": origin,
                "destination": destination,
                "city": city_code,
                "strategy": 0,
            },
        )
        transits = data.get("route", {}).get("transits", [])
        if not transits:
            return None
        transit = transits[0]
        segments = transit.get("segments", [])
        instructions = []
        polyline: List[Dict[str, float]] = []
        for segment in segments[:3]:
            walking = segment.get("walking", {})
            for step in walking.get("steps", [])[:2]:
                instructions.append(step.get("instruction", ""))
                polyline.extend(self._parse_polyline(step.get("polyline", "")))
            bus = segment.get("bus", {}).get("buslines", [])
            if bus:
                instructions.append(f"乘坐{bus[0].get('name', '公交')}")
                polyline.extend(self._parse_polyline(bus[0].get("polyline", "")))
        return {
            "mode": "公交",
            "distance_km": round(float(transit.get("distance", 0)) / 1000, 2),
            "duration_minutes": round(float(transit.get("duration", 0)) / 60),
            "instruction": "，".join(filter(None, instructions[:4])),
            "polyline": polyline,
        }

    def _empty_route(self, mode: str) -> Dict[str, Any]:
        return {
            "mode": mode,
            "distance_km": 0.0,
            "duration_minutes": 0,
            "instruction": "",
            "polyline": [],
        }


amap_service = AMapService()
