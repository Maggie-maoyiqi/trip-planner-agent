# backend/app/agents/attraction_agent.py
import math
from typing import List, Dict, Any
from app.services.amap_service import amap_service
from app.services.unsplash_service import unsplash_service

# typecodes that indicate indoor venues
INDOOR_TYPECODES = {
    "141",  # 博物馆
    "142",  # 美术馆/展览馆
    "143",  # 科技馆/文化馆
    "150",  # 购物中心/商场
    "160",  # 电影院/剧院
    "170",  # 温泉/SPA（室内）
}

class AttractionSearchAgent:
    """返回景点池（flat list），由 PlannerAgent 负责聚类分天"""

    async def run(self, city: str, preferences: str, days: int) -> List[Dict[str, Any]]:
        needed = days * 5  # 多搜一些，给 planner 选择空间

        pois = await amap_service.search_poi(
            keywords=preferences or "景点 旅游 公园",
            city=city
        )

        # 补充室内景点（无论天气如何都能用）
        indoor_pois = await amap_service.search_poi(
            keywords="博物馆 展览馆 美术馆 科技馆",
            city=city
        )

        # 合并去重
        seen = {p["name"] for p in pois}
        for p in indoor_pois:
            if p["name"] not in seen and p["longitude"] != 0:
                pois.append(p)
                seen.add(p["name"])

        # 过滤掉没有坐标的
        pois = [p for p in pois if p["longitude"] != 0 and p["latitude"] != 0]

        # 丰富数据：加图片、判断室内外、估算门票
        enriched = []
        for poi in pois[:needed]:
            is_indoor = any(
                poi.get("typecode", "").startswith(code)
                for code in INDOOR_TYPECODES
            )
            image_url = await unsplash_service.get_photo_url(
                f"{poi['name']} {city}"
            )
            enriched.append({
                "name": poi["name"],
                "address": poi["address"],
                "longitude": poi["longitude"],
                "latitude": poi["latitude"],
                "typecode": poi.get("typecode", ""),
                "is_indoor": is_indoor,
                "description": f"{poi['name']}，{city}知名游览地。",
                "ticket_price": self._estimate_ticket(poi),
                "visit_duration": 90 if is_indoor else 120,
                "image_url": image_url or "",
            })

        return enriched

    def _estimate_ticket(self, poi: Dict) -> float:
        code = poi.get("typecode", "")
        if code.startswith("141"):  return 0.0    # 博物馆多为免费
        if code.startswith("142"):  return 30.0   # 美术馆
        if code.startswith("110"):  return 80.0   # 景区
        if code.startswith("140"):  return 30.0   # 公园
        return 0.0