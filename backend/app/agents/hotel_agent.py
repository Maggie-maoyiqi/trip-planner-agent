# backend/app/agents/hotel_agent.py
import math
from typing import List, Dict, Any, Tuple, Optional
from app.services.amap_service import amap_service
from app.services.unsplash_service import unsplash_service

PRICE_MAP = {
    "豪华": 1400.0, "五星": 1400.0,
    "舒适": 550.0,  "四星": 550.0,
    "经济": 200.0,  "三星": 200.0,
    "快捷": 160.0,  "连锁": 160.0,
    "民宿": 280.0,
    "青年旅舍": 100.0, "青旅": 100.0,
}

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """返回两点距离，单位 km"""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

class HotelAgent:
    """根据指定坐标中心搜索并评分酒店"""

    async def search_near(
        self,
        city: str,
        accommodation: str,
        centroid: Tuple[float, float],       # (lat, lng) of today's attractions
        next_centroid: Optional[Tuple[float, float]],  # tomorrow's centroid (can be None)
        days: int,
    ) -> List[Dict[str, Any]]:
        """
        返回评分排序后的前3家酒店。
        score = 0.6 * (1 / dist_today_km) + 0.4 * (1 / dist_tomorrow_km) - price_factor
        """
        pois = await amap_service.search_poi(
            keywords=f"{accommodation} 酒店",
            city=city
        )
        pois = [p for p in pois if p["longitude"] != 0]

        price_per_night = self._estimate_price(accommodation)
        image_url = await unsplash_service.get_photo_url(
            f"{accommodation} hotel {city}"
        )

        scored = []
        for poi in pois:
            hlat, hlng = poi["latitude"], poi["longitude"]
            dist_today = haversine(centroid[0], centroid[1], hlat, hlng)
            dist_today = max(dist_today, 0.1)  # avoid div/0

            score = 0.6 / dist_today

            if next_centroid:
                dist_next = haversine(next_centroid[0], next_centroid[1], hlat, hlng)
                dist_next = max(dist_next, 0.1)
                score += 0.4 / dist_next

            scored.append({
                "name": poi["name"],
                "address": poi["address"],
                "longitude": hlng,
                "latitude": hlat,
                "price_per_night": price_per_night,
                "total_price": round(price_per_night * days, 2),
                "accommodation_type": accommodation,
                "dist_to_attractions_km": round(dist_today, 2),
                "image_url": image_url or "",
                "_score": score,
            })

        scored.sort(key=lambda x: x["_score"], reverse=True)
        # 清理内部字段
        for h in scored:
            h.pop("_score", None)

        return scored[:3]

    def _estimate_price(self, accommodation: str) -> float:
        for key, price in PRICE_MAP.items():
            if key in accommodation:
                return price
        return 400.0