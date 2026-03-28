# backend/app/agents/trip_planner.py
import asyncio, json
from typing import AsyncGenerator, Dict, Any

from app.agents.attraction_agent import AttractionSearchAgent
from app.agents.weather_agent import WeatherQueryAgent
from app.agents.planner_agent import PlannerAgent
from app.models.schemas import TripPlanRequest

class TripPlannerOrchestrator:
    def __init__(self):
        self.attraction_agent = AttractionSearchAgent()
        self.weather_agent    = WeatherQueryAgent()
        self.planner_agent    = PlannerAgent()  # PlannerAgent owns HotelAgent now

    async def plan(self, request: TripPlanRequest) -> Dict[str, Any]:
        # 景点 + 天气 并行（酒店/餐厅 由 PlannerAgent 按需搜索）
        attractions, weather = await asyncio.gather(
            self.attraction_agent.run(request.city, request.preferences, request.days),
            self.weather_agent.run(request.city),
        )
        return await self.planner_agent.run(
            city=request.city,
            days=request.days,
            start_date=request.start_date,
            end_date=request.end_date,
            all_attractions=attractions,
            weather=weather,
            transportation=request.transportation,
            accommodation=request.accommodation,
            preferences=request.preferences,
            budget=request.budget,
        )

    async def plan_with_progress(self, request: TripPlanRequest) -> AsyncGenerator[str, None]:
        yield 'data: {"progress": 10, "status": "正在搜索景点..."}\n\n'
        attractions = await self.attraction_agent.run(
            request.city, request.preferences, request.days
        )

        yield 'data: {"progress": 35, "status": "查询天气中..."}\n\n'
        weather = await self.weather_agent.run(request.city)

        yield 'data: {"progress": 55, "status": "智能聚类规划行程..."}\n\n'
        # PlannerAgent 内部会搜酒店+餐厅，进度在这里无法细分，
        # 前端可在 55~90 段显示一个假进度动画
        plan = await self.planner_agent.run(
            city=request.city,
            days=request.days,
            start_date=request.start_date,
            end_date=request.end_date,
            all_attractions=attractions,
            weather=weather,
            transportation=request.transportation,
            accommodation=request.accommodation,
            preferences=request.preferences,
            budget=request.budget,
        )

        yield f'data: {{"progress": 100, "status": "完成！", "result": {json.dumps(plan, ensure_ascii=False)}}}\n\n'

trip_planner = TripPlannerOrchestrator()