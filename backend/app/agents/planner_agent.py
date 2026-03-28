# backend/app/agents/planner_agent.py
import math
from typing import List, Dict, Any, Tuple, Optional
from app.agents.hotel_agent import HotelAgent, haversine
from app.services.amap_service import amap_service

# 天气关键词 → 是否恶劣
BAD_WEATHER_KEYWORDS = ["雨", "雪", "大风", "暴", "雷", "冰雹", "沙尘"]

def is_bad_weather(weather: Dict) -> bool:
    combined = weather.get("day_weather", "") + weather.get("night_weather", "")
    wind = weather.get("wind_power", "0")
    try:
        wind_level = int(str(wind).replace("≥", "").split("-")[0])
    except Exception:
        wind_level = 0
    return (
        any(kw in combined for kw in BAD_WEATHER_KEYWORDS)
        or wind_level >= 5
    )

def centroid(points: List[Dict]) -> Tuple[float, float]:
    """计算一组 POI 的地理中心"""
    if not points:
        return (0.0, 0.0)
    lat = sum(p["latitude"] for p in points) / len(points)
    lng = sum(p["longitude"] for p in points) / len(points)
    return (lat, lng)

def cluster_by_proximity(
    attractions: List[Dict], days: int, per_day: int = 3
) -> List[List[Dict]]:
    """
    贪心地理聚类：
    1. 选第一个未分配景点作为当天"锚点"
    2. 找离锚点最近的 (per_day-1) 个未分配景点，组成当天
    3. 重复直到 days 天分配完毕
    """
    pool = list(attractions)  # 浅拷贝
    clusters: List[List[Dict]] = []

    for _ in range(days):
        if not pool:
            clusters.append([])
            continue

        anchor = pool.pop(0)
        day_group = [anchor]

        # 按距离锚点排序剩余景点
        pool.sort(key=lambda p: haversine(
            anchor["latitude"], anchor["longitude"],
            p["latitude"], p["longitude"]
        ))

        # 取最近的 (per_day-1) 个
        for _ in range(per_day - 1):
            if pool:
                day_group.append(pool.pop(0))

        clusters.append(day_group)

    return clusters

def nearest_neighbour_sort(
    attractions: List[Dict], start: Tuple[float, float]
) -> List[Dict]:
    """
    从 start 坐标出发，每次走最近的未访问景点（贪心 TSP）
    """
    remaining = list(attractions)
    ordered = []
    current = start

    while remaining:
        remaining.sort(key=lambda p: haversine(
            current[0], current[1], p["latitude"], p["longitude"]
        ))
        nxt = remaining.pop(0)
        ordered.append(nxt)
        current = (nxt["latitude"], nxt["longitude"])

    return ordered

class PlannerAgent:
    """
    智能规划器：
    1. 景点按地理聚类分天
    2. 恶劣天气自动换室内景点
    3. 酒店搜索基于当天+次日景点中心
    4. 餐厅搜索基于当天景点中心，按评分+距离排序
    5. 当天游览顺序做最近邻优化
    """

    def __init__(self):
        self.hotel_agent = HotelAgent()

    async def run(
        self,
        city: str,
        days: int,
        start_date: str,
        end_date: str,
        all_attractions: List[Dict],   # flat pool from AttractionSearchAgent
        weather: List[Dict],           # from WeatherQueryAgent
        transportation: str,
        accommodation: str,
        preferences: str,
        budget: str,
    ) -> Dict[str, Any]:

        # ── Step 1: 分离室内/室外景点 ─────────────────────────────────
        outdoor = [a for a in all_attractions if not a.get("is_indoor")]
        indoor  = [a for a in all_attractions if a.get("is_indoor")]

        # ── Step 2: 室外景点按地理聚类分天 ────────────────────────────
        clusters = cluster_by_proximity(outdoor, days, per_day=3)

        # ── Step 3: 天气过滤 ──────────────────────────────────────────
        # 如果某天天气恶劣，把当天景点替换为室内景点（若有）
        indoor_pool = list(indoor)
        for i, day_weather in enumerate(weather[:days]):
            if is_bad_weather(day_weather) and indoor_pool:
                # 保留已有室内景点，用室内池补充
                current_outdoor = [a for a in clusters[i] if not a.get("is_indoor")]
                needed = max(0, 3 - len([a for a in clusters[i] if a.get("is_indoor")]))
                replacements = indoor_pool[:needed]
                indoor_pool = indoor_pool[needed:]
                # 把室外替换为室内，保留已有室内
                clusters[i] = [a for a in clusters[i] if a.get("is_indoor")] + replacements
                # 把被换出的室外景点放回大池末尾（给其他天用）
                # （简单策略：直接丢弃，避免复杂度过高）

        # ── Step 4: 计算每天景点中心 ──────────────────────────────────
        centroids = [centroid(day) for day in clusters]

        # ── Step 5: 每天搜酒店（考虑今天 + 明天中心） ─────────────────
        day_hotels: List[Dict] = []
        for i in range(days):
            next_c = centroids[i + 1] if i + 1 < days else None
            hotels = await self.hotel_agent.search_near(
                city=city,
                accommodation=accommodation,
                centroid=centroids[i],
                next_centroid=next_c,
                days=1,  # 每天计算单日价格，total 在外层乘
            )
            day_hotels.append(hotels[0] if hotels else None)

        # ── Step 6: 每天搜餐厅（按评分 + 距中心距离） ─────────────────
        day_meals: List[List[Dict]] = []
        for i in range(days):
            meals = await self._search_restaurants(city, centroids[i])
            day_meals.append(meals)

        # ── Step 7: 每天景点排序（最近邻，从酒店出发） ────────────────
        for i, day_group in enumerate(clusters):
            hotel = day_hotels[i]
            if hotel:
                start_pos = (hotel["latitude"], hotel["longitude"])
            elif i == 0:
                start_pos = centroids[0]
            else:
                start_pos = centroids[i - 1]
            clusters[i] = nearest_neighbour_sort(day_group, start_pos)

        # ── Step 8: 拼装每日行程 ──────────────────────────────────────
        day_plans = []
        for i in range(days):
            day_weather = weather[i] if i < len(weather) else {}
            hotel = day_hotels[i]
            bad = is_bad_weather(day_weather) if day_weather else False

            weather_tip = ""
            if bad:
                w = day_weather.get("day_weather", "")
                weather_tip = f"今日{w}，已为您优先安排室内景点。"

            day_plans.append({
                "date": f"第{i+1}天",
                "day_index": i,
                "description": (
                    f"第{i+1}天畅游{city}，体验{preferences}相关景点。"
                    + weather_tip
                ),
                "transportation": transportation,
                "accommodation": hotel["name"] if hotel else "",
                "hotel": hotel,
                "attractions": clusters[i],
                "meals": day_meals[i],
                "weather_note": weather_tip,
            })

        # ── Step 9: 预算汇总 ──────────────────────────────────────────
        total_tickets = sum(
            a.get("ticket_price", 0)
            for day in clusters for a in day
        )
        # 酒店：每晚价格 × 天数（用第一家酒店的单价，或 0）
        hotel_unit = day_hotels[0]["price_per_night"] if day_hotels and day_hotels[0] else 400.0
        hotel_cost = hotel_unit * days

        meal_cost = 150.0 * days   # 每天餐饮估算 150 元
        transport_cost = self._transport_cost(transportation, days)

        budget_detail = {
            "total_attractions": round(total_tickets, 2),
            "total_hotels":      round(hotel_cost, 2),
            "total_meals":       round(meal_cost, 2),
            "total_transportation": round(transport_cost, 2),
            "total": round(total_tickets + hotel_cost + meal_cost + transport_cost, 2),
        }

        # 所有推荐酒店（去重，供前端展示）
        all_hotels = [h for h in day_hotels if h]

        return {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "days": day_plans,
            "hotels": all_hotels,
            "weather_info": weather,
            "overall_suggestions": (
                f"建议{preferences}爱好者重点关注已规划景点，"
                f"行程已按地理就近原则排列，{transportation}出行最为便捷。"
            ),
            "budget": budget_detail,
        }

    async def _search_restaurants(
        self, city: str, day_centroid: Tuple[float, float]
    ) -> List[Dict]:
        """
        搜索当地特色餐厅，按 rating 优先，然后按距离中心排序
        返回三餐（早/午/晚）各一家推荐
        """
        pois = await amap_service.search_poi(
            keywords="特色餐厅 美食",
            city=city
        )
        pois = [p for p in pois if p["longitude"] != 0]

        # AMap POI 没有直接 rating，用距中心距离作为主排序
        # 同时用 typecode 判断是否本地特色（061 系列为餐饮）
        scored = []
        for p in pois:
            dist = haversine(
                day_centroid[0], day_centroid[1],
                p["latitude"], p["longitude"]
            )
            # 假设 typecode 061xxx = 餐饮，优先
            is_food = p.get("typecode", "").startswith("06")
            scored.append({
                **p,
                "_dist": dist,
                "_priority": 0 if is_food else 1,
            })

        scored.sort(key=lambda x: (x["_priority"], x["_dist"]))

        meals = []
        meal_types = ["早餐", "午餐", "晚餐"]
        for idx, mt in enumerate(meal_types):
            if idx < len(scored):
                r = scored[idx]
                meals.append({
                    "meal_type": mt,
                    "name": r["name"],
                    "address": r["address"],
                    "longitude": r["longitude"],
                    "latitude": r["latitude"],
                    "dist_to_attractions_km": round(r["_dist"], 2),
                    "suggestion": f"推荐{city}本地特色，距当日景点约 {r['_dist']:.1f} km",
                })
            else:
                meals.append({
                    "meal_type": mt,
                    "name": f"{city}本地特色餐厅",
                    "address": "",
                    "longitude": 0,
                    "latitude": 0,
                    "dist_to_attractions_km": 0,
                    "suggestion": f"可询问酒店前台推荐附近{mt}",
                })

        return meals

    def _transport_cost(self, transportation: str, days: int) -> float:
        base = {"飞机": 1200, "高铁": 600, "自驾": 400, "公交": 100}
        for k, v in base.items():
            if k in transportation:
                return v + days * 50
        return 200 + days * 50