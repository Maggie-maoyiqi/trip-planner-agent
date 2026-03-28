from typing import Any, Dict, List, Optional, Tuple

from app.agents.hotel_agent import HotelAgent, haversine
from app.services.amap_service import amap_service
from app.services.llm_service import llm_service


BAD_WEATHER_KEYWORDS = ["雨", "雪", "大风", "暴", "雷", "冰雹", "沙尘"]
TIME_SLOT_LIMITS = {"上午": 180, "下午": 240, "晚上": 180}
DEFAULT_TIMES = {
    "上午": ("09:00", "12:00"),
    "午餐": ("12:15", "13:15"),
    "下午": ("13:45", "17:45"),
    "晚餐": ("18:15", "19:30"),
    "晚上": ("19:45", "21:45"),
}


def is_bad_weather(weather: Dict[str, Any]) -> bool:
    combined = weather.get("day_weather", "") + weather.get("night_weather", "")
    wind = weather.get("wind_power", "0")
    try:
        wind_level = int(str(wind).replace("≥", "").split("-")[0])
    except Exception:
        wind_level = 0
    return any(kw in combined for kw in BAD_WEATHER_KEYWORDS) or wind_level >= 5


def centroid(points: List[Dict[str, Any]]) -> Tuple[float, float]:
    if not points:
        return (0.0, 0.0)
    lat = sum(p["latitude"] for p in points) / len(points)
    lng = sum(p["longitude"] for p in points) / len(points)
    return (lat, lng)


def nearest_neighbour_sort(attractions: List[Dict[str, Any]], start: Tuple[float, float]) -> List[Dict[str, Any]]:
    remaining = list(attractions)
    ordered: List[Dict[str, Any]] = []
    current = start
    while remaining:
        remaining.sort(
            key=lambda p: haversine(current[0], current[1], p["latitude"], p["longitude"])
        )
        nxt = remaining.pop(0)
        ordered.append(nxt)
        current = (nxt["latitude"], nxt["longitude"])
    return ordered


def cluster_by_proximity(attractions: List[Dict[str, Any]], days: int) -> List[List[Dict[str, Any]]]:
    pool = list(attractions)
    clusters: List[List[Dict[str, Any]]] = []

    for _ in range(days):
        if not pool:
            clusters.append([])
            continue

        anchor = pool.pop(0)
        day_group = [anchor]
        pool.sort(
            key=lambda p: haversine(
                anchor["latitude"],
                anchor["longitude"],
                p["latitude"],
                p["longitude"],
            )
        )

        while pool and len(day_group) < 4:
            candidate = pool[0]
            current_duration = sum(item.get("visit_duration", 120) for item in day_group)
            if current_duration + candidate.get("visit_duration", 120) > sum(TIME_SLOT_LIMITS.values()) and len(day_group) >= 2:
                break
            day_group.append(pool.pop(0))

        clusters.append(day_group)

    while len(clusters) < days:
        clusters.append([])
    return clusters


class PlannerAgent:
    def __init__(self):
        self.hotel_agent = HotelAgent()

    async def run(
        self,
        city: str,
        days: int,
        start_date: str,
        end_date: str,
        all_attractions: List[Dict[str, Any]],
        weather: List[Dict[str, Any]],
        transportation: str,
        accommodation: str,
        preferences: str,
        budget: str,
    ) -> Dict[str, Any]:
        selected_attractions = self._pick_attractions_for_days(all_attractions, days, weather)
        day_groups = self._group_attractions_by_day(selected_attractions, days, weather)
        centroids = [centroid(day) for day in day_groups]

        day_meals: List[List[Dict[str, Any]]] = []
        for i, day_group in enumerate(day_groups):
            meals = await self._search_restaurants(
                city=city,
                day_index=i,
                budget=budget,
                preferences=preferences,
                day_attractions=day_group,
            )
            day_meals.append(meals)

        day_hotels: List[Optional[Dict[str, Any]]] = []
        for i in range(days):
            next_c = centroids[i + 1] if i + 1 < days else None
            hotels = await self.hotel_agent.search_near(
                city=city,
                accommodation=accommodation,
                centroid=centroids[i],
                next_centroid=next_c,
                days=1,
            )
            day_hotels.append(hotels[0] if hotels else None)

        day_plans = []
        for i in range(days):
            hotel = day_hotels[i]
            ordered_attractions = self._order_day(day_groups[i], hotel, centroids[i - 1] if i > 0 else None)
            llm_plan = await self._build_daily_schedule(
                city=city,
                preferences=preferences,
                transportation=transportation,
                weather=weather[i] if i < len(weather) else {},
                attractions=ordered_attractions,
                meals=day_meals[i],
            )
            route_segments = await self._build_route_segments(
                city=city,
                transportation=transportation,
                hotel=hotel,
                attractions=ordered_attractions,
                meals=day_meals[i],
            )

            weather_note = ""
            if i < len(weather) and is_bad_weather(weather[i]):
                weather_note = f"今日{weather[i].get('day_weather', '')}，已优先压缩室外停留时间。"

            day_plans.append({
                "date": f"第{i + 1}天",
                "day_index": i,
                "description": llm_plan.get("day_summary") or f"第{i + 1}天围绕{preferences}主题展开游玩。",
                "weather_note": weather_note,
                "clothing_recommendation": llm_plan.get("clothing_recommendation", self._fallback_clothing(weather[i] if i < len(weather) else {})),
                "transportation": transportation,
                "accommodation": hotel["name"] if hotel else "",
                "hotel": hotel,
                "attractions": ordered_attractions,
                "meals": day_meals[i],
                "schedule": self._normalize_schedule(llm_plan.get("schedule", []), ordered_attractions, day_meals[i], hotel),
                "route_segments": route_segments,
            })

        all_hotels = [h for h in day_hotels if h]
        budget_detail = self._build_budget(day_plans, transportation)

        return {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "days": day_plans,
            "hotels": all_hotels,
            "weather_info": weather,
            "overall_suggestions": self._overall_suggestions(preferences, transportation, day_plans),
            "budget": budget_detail,
        }

    def _pick_attractions_for_days(
        self,
        all_attractions: List[Dict[str, Any]],
        days: int,
        weather: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        desired = min(len(all_attractions), days * 4)
        if desired == 0:
            return []
        bad_days = sum(1 for day in weather[:days] if is_bad_weather(day))
        indoor = [a for a in all_attractions if a.get("is_indoor")]
        outdoor = [a for a in all_attractions if not a.get("is_indoor")]
        selected: List[Dict[str, Any]] = []
        indoor_quota = min(len(indoor), max(bad_days * 2, days))

        for attraction in indoor[:indoor_quota]:
            selected.append(attraction)
        for attraction in outdoor:
            if len(selected) >= desired:
                break
            selected.append(attraction)
        for attraction in indoor[indoor_quota:]:
            if len(selected) >= desired:
                break
            selected.append(attraction)
        return selected[:desired]

    def _group_attractions_by_day(
        self,
        attractions: List[Dict[str, Any]],
        days: int,
        weather: List[Dict[str, Any]],
    ) -> List[List[Dict[str, Any]]]:
        indoor = [item for item in attractions if item.get("is_indoor")]
        outdoor = [item for item in attractions if not item.get("is_indoor")]
        outdoor_clusters = cluster_by_proximity(outdoor, days)
        indoor_clusters = cluster_by_proximity(indoor, days)
        groups: List[List[Dict[str, Any]]] = []

        for day_idx in range(days):
            prefer_indoor = day_idx < len(weather) and is_bad_weather(weather[day_idx])
            primary = indoor_clusters[day_idx] if prefer_indoor else outdoor_clusters[day_idx]
            secondary = outdoor_clusters[day_idx] if prefer_indoor else indoor_clusters[day_idx]
            merged: List[Dict[str, Any]] = []
            slot_budget = sum(TIME_SLOT_LIMITS.values())
            for item in primary + secondary:
                if any(existing["name"] == item["name"] for existing in merged):
                    continue
                duration = int(item.get("visit_duration", 120))
                if merged and slot_budget - duration < 60:
                    continue
                merged.append(item)
                slot_budget -= duration
                if len(merged) >= 4:
                    break
            groups.append(merged)
        return groups

    def _order_day(
        self,
        attractions: List[Dict[str, Any]],
        hotel: Optional[Dict[str, Any]],
        previous_centroid: Optional[Tuple[float, float]],
    ) -> List[Dict[str, Any]]:
        if not attractions:
            return []
        if hotel:
            start = (hotel["latitude"], hotel["longitude"])
        elif previous_centroid:
            start = previous_centroid
        else:
            start = (attractions[0]["latitude"], attractions[0]["longitude"])
        return nearest_neighbour_sort(attractions, start)

    async def _search_restaurants(
        self,
        city: str,
        day_index: int,
        budget: str,
        preferences: str,
        day_attractions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        center = centroid(day_attractions)
        pois = await amap_service.search_poi("特色餐厅 美食 早餐 晚餐", city, offset=20)
        scored: List[Dict[str, Any]] = []
        for poi in pois:
            if poi["longitude"] == 0 or poi["latitude"] == 0:
                continue
            dist = haversine(center[0], center[1], poi["latitude"], poi["longitude"])
            scored.append({
                **poi,
                "dist_to_attractions_km": round(dist, 2),
            })
        scored.sort(key=lambda item: item["dist_to_attractions_km"])

        try:
            llm_result = await llm_service.choose_restaurants(
                city=city,
                budget=budget,
                preferences=preferences,
                day_context={
                    "day_index": day_index + 1,
                    "attractions": [item["name"] for item in day_attractions],
                },
                candidates=scored[:12],
            )
            meals = []
            chosen_names = {meal.get("name"): meal for meal in llm_result.get("meals", []) if meal.get("name")}
            for poi in scored:
                if poi["name"] not in chosen_names:
                    continue
                llm_item = chosen_names[poi["name"]]
                meals.append({
                    "meal_type": llm_item.get("meal_type", "用餐"),
                    "name": poi["name"],
                    "address": poi.get("address", ""),
                    "longitude": poi.get("longitude", 0.0),
                    "latitude": poi.get("latitude", 0.0),
                    "dist_to_attractions_km": poi.get("dist_to_attractions_km", 0.0),
                    "suggestion": llm_item.get("suggestion", "适合作为当天行程衔接用餐点。"),
                    "estimated_cost_per_person": float(llm_item.get("estimated_cost_per_person", self._fallback_meal_cost(budget))),
                })
            if meals:
                return meals[:3]
        except Exception:
            pass

        meal_types = ["早餐", "午餐", "晚餐"]
        return [
            {
                "meal_type": meal_types[i],
                "name": poi["name"],
                "address": poi.get("address", ""),
                "longitude": poi.get("longitude", 0.0),
                "latitude": poi.get("latitude", 0.0),
                "dist_to_attractions_km": poi.get("dist_to_attractions_km", 0.0),
                "suggestion": f"{meal_types[i]}可安排在此，距离当天主要景点较近。",
                "estimated_cost_per_person": self._fallback_meal_cost(budget),
            }
            for i, poi in enumerate(scored[:3])
        ]

    async def _build_daily_schedule(
        self,
        city: str,
        preferences: str,
        transportation: str,
        weather: Dict[str, Any],
        attractions: List[Dict[str, Any]],
        meals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        try:
            location_context = self._build_location_context(attractions, meals)
            return await llm_service.build_daily_plan(
                city=city,
                preferences=preferences,
                transportation=transportation,
                weather=weather,
                attractions=attractions,
                meals=meals,
                location_context=location_context,
            )
        except Exception:
            return {
                "day_summary": f"围绕{preferences}安排白天景点与餐饮，尽量减少折返。",
                "clothing_recommendation": self._fallback_clothing(weather),
                "schedule": [],
            }

    def _build_location_context(
        self,
        attractions: List[Dict[str, Any]],
        meals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        points = [
            {
                "name": item["name"],
                "type": "attraction",
                "longitude": item["longitude"],
                "latitude": item["latitude"],
            }
            for item in attractions
        ] + [
            {
                "name": item["name"],
                "type": "meal",
                "longitude": item["longitude"],
                "latitude": item["latitude"],
            }
            for item in meals
        ]

        pair_distances = []
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                a = points[i]
                b = points[j]
                pair_distances.append({
                    "from": a["name"],
                    "to": b["name"],
                    "distance_km": round(
                        haversine(a["latitude"], a["longitude"], b["latitude"], b["longitude"]),
                        2,
                    ),
                })
        pair_distances.sort(key=lambda item: item["distance_km"])
        return {
            "points": points,
            "closest_pairs": pair_distances[:8],
            "farthest_pairs": pair_distances[-5:],
        }

    def _normalize_schedule(
        self,
        schedule: List[Dict[str, Any]],
        attractions: List[Dict[str, Any]],
        meals: List[Dict[str, Any]],
        hotel: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if schedule:
            return schedule

        generated: List[Dict[str, Any]] = []
        ordered_pairs: List[Tuple[str, Optional[Dict[str, Any]]]] = []
        for idx, slot in enumerate(["上午", "下午", "晚上"]):
            attraction = attractions[idx] if idx < len(attractions) else None
            ordered_pairs.append((slot, attraction))

        for slot, attraction in ordered_pairs:
            start, end = DEFAULT_TIMES[slot]
            if attraction:
                generated.append({
                    "time_slot": slot,
                    "start_time": start,
                    "end_time": end,
                    "item_type": "attraction",
                    "title": f"{slot}游览 {attraction['name']}",
                    "reference_name": attraction["name"],
                    "duration_minutes": attraction.get("visit_duration", 120),
                    "estimated_cost": attraction.get("ticket_price", 0.0),
                    "note": attraction.get("llm_reason", ""),
                })
            else:
                generated.append({
                    "time_slot": slot,
                    "start_time": start,
                    "end_time": end,
                    "item_type": "rest",
                    "title": f"{slot}自由活动或休息",
                    "reference_name": "",
                    "duration_minutes": 60,
                    "estimated_cost": 0.0,
                    "note": "保留弹性时间，减少赶路。",
                })

        meal_time_map = {"早餐": "早餐", "午餐": "午餐", "晚餐": "晚餐"}
        for meal in meals:
            time_slot = meal_time_map.get(meal.get("meal_type", ""), "")
            if not time_slot:
                continue
            start, end = DEFAULT_TIMES.get(time_slot, ("12:00", "13:00"))
            generated.append({
                "time_slot": time_slot,
                "start_time": start,
                "end_time": end,
                "item_type": "meal",
                "title": f"{time_slot} {meal['name']}",
                "reference_name": meal["name"],
                "duration_minutes": 60,
                "estimated_cost": meal.get("estimated_cost_per_person", 0.0),
                "note": meal.get("suggestion", ""),
            })

        if hotel:
            generated.append({
                "time_slot": "住宿",
                "start_time": "21:45",
                "end_time": "次日",
                "item_type": "hotel",
                "title": f"入住 {hotel['name']}",
                "reference_name": hotel["name"],
                "duration_minutes": 0,
                "estimated_cost": hotel.get("price_per_night", 0.0),
                "note": "结束当天行程后回酒店休息。",
            })
        return generated

    async def _build_route_segments(
        self,
        city: str,
        transportation: str,
        hotel: Optional[Dict[str, Any]],
        attractions: List[Dict[str, Any]],
        meals: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        points: List[Dict[str, Any]] = []
        if hotel:
            points.append({"name": hotel["name"], "longitude": hotel["longitude"], "latitude": hotel["latitude"]})

        breakfast = next((meal for meal in meals if meal.get("meal_type") == "早餐"), None)
        lunch = next((meal for meal in meals if meal.get("meal_type") == "午餐"), None)
        dinner = next((meal for meal in meals if meal.get("meal_type") == "晚餐"), None)
        if breakfast:
            points.append({"name": breakfast["name"], "longitude": breakfast["longitude"], "latitude": breakfast["latitude"]})
        if attractions:
            points.append({"name": attractions[0]["name"], "longitude": attractions[0]["longitude"], "latitude": attractions[0]["latitude"]})
        if lunch:
            points.append({"name": lunch["name"], "longitude": lunch["longitude"], "latitude": lunch["latitude"]})
        if len(attractions) > 1:
            for attraction in attractions[1:]:
                points.append({"name": attraction["name"], "longitude": attraction["longitude"], "latitude": attraction["latitude"]})
        if dinner:
            points.append({"name": dinner["name"], "longitude": dinner["longitude"], "latitude": dinner["latitude"]})
        if hotel:
            points.append({"name": hotel["name"], "longitude": hotel["longitude"], "latitude": hotel["latitude"]})

        compact_points: List[Dict[str, Any]] = []
        for point in points:
            if compact_points and compact_points[-1]["name"] == point["name"]:
                continue
            compact_points.append(point)

        segments: List[Dict[str, Any]] = []
        for i in range(len(compact_points) - 1):
            origin = compact_points[i]
            destination = compact_points[i + 1]
            try:
                route = await amap_service.route_plan(origin, destination, city, transportation)
            except Exception:
                route = {"mode": transportation, "distance_km": 0.0, "duration_minutes": 0, "instruction": "", "polyline": []}
            segments.append({
                "from_name": origin["name"],
                "to_name": destination["name"],
                "mode": route.get("mode", transportation),
                "distance_km": route.get("distance_km", 0.0),
                "duration_minutes": route.get("duration_minutes", 0),
                "instruction": route.get("instruction", ""),
                "polyline": route.get("polyline", []),
            })
        return segments

    def _build_budget(self, day_plans: List[Dict[str, Any]], transportation: str) -> Dict[str, float]:
        total_tickets = sum(
            attraction.get("ticket_price", 0.0)
            for day in day_plans
            for attraction in day.get("attractions", [])
        )
        total_hotels = sum(day.get("hotel", {}).get("price_per_night", 0.0) for day in day_plans if day.get("hotel"))
        total_meals = sum(
            meal.get("estimated_cost_per_person", 0.0)
            for day in day_plans
            for meal in day.get("meals", [])
        )
        total_transportation = sum(
            self._transport_cost_by_segment(segment, transportation)
            for day in day_plans
            for segment in day.get("route_segments", [])
        )
        total = total_tickets + total_hotels + total_meals + total_transportation
        return {
            "total_attractions": round(total_tickets, 2),
            "total_hotels": round(total_hotels, 2),
            "total_meals": round(total_meals, 2),
            "total_transportation": round(total_transportation, 2),
            "total": round(total, 2),
        }

    def _transport_cost_by_segment(self, segment: Dict[str, Any], transportation: str) -> float:
        distance = float(segment.get("distance_km", 0.0))
        mode = segment.get("mode") or transportation
        if mode == "步行":
            return 0.0
        if mode == "公交":
            return 3.0 + distance * 0.5
        if mode == "驾车" or transportation == "自驾":
            return distance * 1.2
        if mode == "骑行":
            return distance * 0.3
        return distance * 0.8

    def _overall_suggestions(self, preferences: str, transportation: str, day_plans: List[Dict[str, Any]]) -> str:
        indoor_days = sum(1 for day in day_plans if "室外停留时间" in day.get("weather_note", ""))
        return (
            f"已先用景点 agent 拉取候选，再由 LLM 筛出更值得去的景点，并按{preferences}主题生成每日时段。"
            f" 酒店保持在路线之后再搜索，城市内通勤使用高德补足{transportation}方案。"
            f" {'天气波动天数较多，建议优先关注室内备选。' if indoor_days else '整体行程节奏较均衡，适合首次到访。'}"
        )

    def _fallback_clothing(self, weather: Dict[str, Any]) -> str:
        try:
            day_temp = int(str(weather.get("day_temp", "25")))
        except Exception:
            day_temp = 25
        day_weather = weather.get("day_weather", "")
        if "雨" in day_weather:
            return "建议穿轻薄防水外套，搭配防滑鞋，并随身带伞。"
        if day_temp >= 30:
            return "建议穿透气短袖、轻薄长裤，并做好防晒补水。"
        if day_temp >= 20:
            return "建议穿薄外套或长袖，步行多的话尽量选择舒适运动鞋。"
        return "建议穿保暖外套与舒适步行鞋，早晚注意加衣。"

    def _fallback_meal_cost(self, budget: str) -> float:
        if budget == "豪华":
            return 180.0
        if budget == "经济":
            return 45.0
        return 90.0
