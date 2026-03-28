# backend/app/api/routes/trip.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import TripPlanRequest, TripPlan, Attraction, Location, Hotel, MealRecommendation
from app.agents.trip_planner import trip_planner

router = APIRouter(prefix="/api/trip", tags=["旅行规划"])


def _dict_to_attraction(a: dict) -> Attraction:
    return Attraction(
        name=a.get("name", ""),
        address=a.get("address", ""),
        location=Location(
            longitude=a.get("longitude", 0.0),
            latitude=a.get("latitude", 0.0),
        ),
        visit_duration=a.get("visit_duration", 120),
        description=a.get("description", ""),
        ticket_price=a.get("ticket_price", 0.0),
        is_indoor=a.get("is_indoor", False),
        typecode=a.get("typecode", ""),
        image_url=a.get("image_url"),
    )

def _dict_to_hotel(h: dict) -> Hotel:
    return Hotel(
        name=h.get("name", ""),
        address=h.get("address", ""),
        location=Location(
            longitude=h.get("longitude", 0.0),
            latitude=h.get("latitude", 0.0),
        ),
        price_per_night=h.get("price_per_night", 0.0),
        total_price=h.get("total_price", 0.0),
        accommodation_type=h.get("accommodation_type", ""),
        dist_to_attractions_km=h.get("dist_to_attractions_km", 0.0),
        image_url=h.get("image_url"),
    )

def _dict_to_meal(m: dict) -> MealRecommendation:
    return MealRecommendation(
        meal_type=m.get("meal_type", ""),
        name=m.get("name", ""),
        address=m.get("address", ""),
        location=Location(
            longitude=m.get("longitude", 0.0),
            latitude=m.get("latitude", 0.0),
        ),
        dist_to_attractions_km=m.get("dist_to_attractions_km", 0.0),
        suggestion=m.get("suggestion", ""),
    )

def _build_trip_plan(raw: dict) -> TripPlan:
    """把 PlannerAgent 返回的原始 dict 转换成 TripPlan Pydantic 模型"""
    from app.models.schemas import DayPlan, WeatherInfo, Budget

    days = []
    for d in raw.get("days", []):
        hotel_dict = d.get("hotel")
        days.append(DayPlan(
            date=d.get("date", ""),
            day_index=d.get("day_index", 0),
            description=d.get("description", ""),
            weather_note=d.get("weather_note", ""),
            transportation=d.get("transportation", ""),
            accommodation=d.get("accommodation", ""),
            hotel=_dict_to_hotel(hotel_dict) if hotel_dict else None,
            attractions=[_dict_to_attraction(a) for a in d.get("attractions", [])],
            meals=[_dict_to_meal(m) for m in d.get("meals", [])],
        ))

    weather_info = [
        WeatherInfo(
            date=w.get("date", ""),
            day_weather=w.get("day_weather", ""),
            night_weather=w.get("night_weather", ""),
            day_temp=str(w.get("day_temp", "0")),
            night_temp=str(w.get("night_temp", "0")),
            wind_direction=w.get("wind_direction", ""),
            wind_power=str(w.get("wind_power", "")),
        )
        for w in raw.get("weather_info", [])
    ]

    b = raw.get("budget", {})
    budget = Budget(
        total_attractions=b.get("total_attractions", 0.0),
        total_hotels=b.get("total_hotels", 0.0),
        total_meals=b.get("total_meals", 0.0),
        total_transportation=b.get("total_transportation", 0.0),
        total=b.get("total", 0.0),
    )

    return TripPlan(
        city=raw.get("city", ""),
        start_date=raw.get("start_date", ""),
        end_date=raw.get("end_date", ""),
        days=days,
        hotels=[_dict_to_hotel(h) for h in raw.get("hotels", [])],
        weather_info=weather_info,
        overall_suggestions=raw.get("overall_suggestions", ""),
        budget=budget,
    )


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """生成完整旅行计划（同步，等待所有 agent 完成后返回）"""
    try:
        print(f"收到请求: {request.city}, {request.days}天, {request.preferences}")
        raw = await trip_planner.plan(request)
        return _build_trip_plan(raw)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成计划失败: {str(e)}")


@router.post("/stream")
async def stream_trip_plan(request: TripPlanRequest):
    """
    SSE 流式接口，实时推送进度。
    前端用 EventSource 或 fetch+ReadableStream 接收。
    每条消息格式：data: {"progress": 0~100, "status": "...", "result": {...}}
    result 只在 progress=100 时出现。
    """
    async def event_generator():
        try:
            async for chunk in trip_planner.plan_with_progress(request):
                yield chunk
        except Exception as e:
            import json, traceback
            traceback.print_exc()
            yield f'data: {json.dumps({"progress": -1, "status": f"错误: {str(e)}"}, ensure_ascii=False)}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # 关闭 nginx 缓冲，保证实时推送
        },
    )


@router.get("/test")
async def test_route():
    return {"message": "Trip router is working!"}