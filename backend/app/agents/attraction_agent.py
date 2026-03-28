from typing import Any, Dict, List

from app.services.amap_service import amap_service
from app.services.llm_service import llm_service
from app.services.unsplash_service import unsplash_service


INDOOR_TYPECODES = {
    "141",
    "142",
    "143",
    "150",
    "160",
    "170",
}


class AttractionSearchAgent:
    """先搜候选景点，再用 LLM 精选热门景点并补足估算信息"""

    async def run(
        self,
        city: str,
        preferences: str,
        days: int,
        weather: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        weather = weather or []
        raw_candidates = await self._collect_candidates(city, preferences, days)
        if not raw_candidates:
            return []

        ranked = await self._rank_with_llm(city, preferences, days, weather, raw_candidates)
        image_cache: Dict[str, str] = {}
        enriched: List[Dict[str, Any]] = []

        for poi in ranked:
            image_url = image_cache.get(poi["name"])
            if image_url is None:
                image_url = await unsplash_service.get_photo_url(f"{poi['name']} {city}") or ""
                image_cache[poi["name"]] = image_url

            poi["image_url"] = image_url
            enriched.append(poi)

        return enriched

    async def _collect_candidates(self, city: str, preferences: str, days: int) -> List[Dict[str, Any]]:
        search_keywords = [
            preferences or "景点 旅游",
            f"{city} 热门景点",
            f"{city} 必去景点",
            "博物馆 展览馆 美术馆 科技馆",
            "公园 古镇 地标 夜景",
        ]
        merged: List[Dict[str, Any]] = []
        seen = set()
        limit = max(days * 8, 16)

        for keyword in search_keywords:
            pois = await amap_service.search_poi(keyword, city, offset=20)
            for poi in pois:
                if poi["longitude"] == 0 or poi["latitude"] == 0:
                    continue
                key = (poi["name"], poi["address"])
                if key in seen:
                    continue
                seen.add(key)
                merged.append(poi)
                if len(merged) >= limit:
                    return merged
        return merged

    async def _rank_with_llm(
        self,
        city: str,
        preferences: str,
        days: int,
        weather: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        fallback = [self._fallback_enrich(poi) for poi in candidates[: days * 4]]
        try:
            result = await llm_service.rank_attractions(city, preferences, days, weather, candidates)
            chosen = result.get("attractions", [])
            chosen_map = {item.get("name"): item for item in chosen if item.get("name")}
            enriched = []
            for poi in candidates:
                llm_item = chosen_map.get(poi["name"])
                if not llm_item:
                    continue
                enriched.append(self._merge_llm_fields(poi, llm_item))
            return enriched or fallback
        except Exception:
            return fallback

    def _merge_llm_fields(self, poi: Dict[str, Any], llm_item: Dict[str, Any]) -> Dict[str, Any]:
        is_indoor = any(
            poi.get("typecode", "").startswith(code)
            for code in INDOOR_TYPECODES
        )
        return {
            "name": poi["name"],
            "address": poi.get("address", ""),
            "longitude": poi.get("longitude", 0.0),
            "latitude": poi.get("latitude", 0.0),
            "typecode": poi.get("typecode", ""),
            "is_indoor": is_indoor,
            "description": f"{poi['name']}，{poi.get('adname') or city_safe_name(poi)}值得体验的代表性景点。",
            "ticket_price": float(llm_item.get("ticket_price", self._estimate_ticket(poi))),
            "visit_duration": int(llm_item.get("visit_duration", 120)),
            "best_visit_time": llm_item.get("best_visit_time", ""),
            "llm_reason": llm_item.get("llm_reason", ""),
        }

    def _fallback_enrich(self, poi: Dict[str, Any]) -> Dict[str, Any]:
        is_indoor = any(
            poi.get("typecode", "").startswith(code)
            for code in INDOOR_TYPECODES
        )
        return {
            "name": poi["name"],
            "address": poi.get("address", ""),
            "longitude": poi.get("longitude", 0.0),
            "latitude": poi.get("latitude", 0.0),
            "typecode": poi.get("typecode", ""),
            "is_indoor": is_indoor,
            "description": f"{poi['name']}是当地值得考虑的热门去处。",
            "ticket_price": self._estimate_ticket(poi),
            "visit_duration": 90 if is_indoor else 120,
            "best_visit_time": "白天",
            "llm_reason": "根据景点类型与通用旅行经验做出的保守推荐。",
            "image_url": "",
        }

    def _estimate_ticket(self, poi: Dict[str, Any]) -> float:
        code = poi.get("typecode", "")
        if code.startswith("141"):
            return 0.0
        if code.startswith("142"):
            return 30.0
        if code.startswith("110"):
            return 80.0
        if code.startswith("140"):
            return 20.0
        return 0.0


def city_safe_name(poi: Dict[str, Any]) -> str:
    return poi.get("cityname") or poi.get("pname") or "当地"
