# backend/app/api/routes/trip.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import json

from app.models.schemas import TripPlanRequest, TripPlan
from app.services.amap_service import amap_service
from app.services.unsplash_service import unsplash_service

router = APIRouter(prefix="/api/trip", tags=["旅行规划"])


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """
    生成旅行计划
    
    Args:
        request: 用户请求，包含城市、日期、偏好等
    
    Returns:
        完整的旅行计划
    """
    try:
        print(f"收到请求: {request.city}, {request.days}天")
        
        # ========== 1. 搜索景点 ==========
        print("正在搜索景点...")
        attractions_data = await amap_service.search_poi(
            keywords=request.preferences,
            city=request.city
        )
        print(f"找到 {len(attractions_data)} 个景点")
        
        # ========== 2. 查询天气 ==========
        print("正在查询天气...")
        weather_data = await amap_service.get_weather(request.city)
        print(f"获取到 {len(weather_data)} 天天气")
        
        # ========== 3. 搜索酒店 ==========
        print("正在搜索酒店...")
        hotels_data = await amap_service.search_poi(
            keywords=request.accommodation,
            city=request.city
        )
        print(f"找到 {len(hotels_data)} 家酒店")
        
        # ========== 4. 构建行程计划（模拟） ==========
        # 这里先用模拟数据，后续会接入 LLM
        
        # 创建示例景点
        from app.models.schemas import Attraction, Location, DayPlan, WeatherInfo, Budget
        
        # 转换景点数据
        attractions = []
        for idx, a in enumerate(attractions_data[:3]):  # 只取前3个景点
            attraction = Attraction(
                name=a["name"],
                address=a["address"],
                location=Location(
                    longitude=a["longitude"],
                    latitude=a["latitude"]
                ),
                visit_duration=120,  # 默认2小时
                description=f"{a['name']}是{request.city}的著名景点，值得一游。",
                ticket_price=50 + idx * 10  # 模拟门票价格
            )
            attractions.append(attraction)
        
        # 转换天气数据
        weather_info = []
        for w in weather_data:
            weather = WeatherInfo(
                date=w["date"],
                day_weather=w["day_weather"],
                night_weather=w["night_weather"],
                day_temp=w["day_temp"],
                night_temp=w["night_temp"],
                wind_direction=w["wind_direction"],
                wind_power=w["wind_power"]
            )
            weather_info.append(weather)
        
        # 创建每日行程
        days = []
        for i in range(min(request.days, 3)):  # 最多3天
            day = DayPlan(
                date=f"第{i+1}天",
                day_index=i,
                description=f"第{i+1}天在{request.city}的精彩行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=attractions
            )
            days.append(day)
        
        # 创建预算
        budget = Budget(
            total_attractions=sum(a.ticket_price for a in attractions),
            total_hotels=800,  # 模拟酒店费用
            total_meals=300,   # 模拟餐饮费用
            total_transportation=200,  # 模拟交通费用
            total=sum(a.ticket_price for a in attractions) + 800 + 300 + 200
        )
        
        # 创建完整计划
        trip_plan = TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=weather_info,
            overall_suggestions=f"建议{request.preferences}爱好者重点关注故宫、天坛等景点。{request.budget}预算可以玩得很舒服。",
            budget=budget
        )
        
        # ========== 5. 为景点添加图片 ==========
        print("正在获取景点图片...")
        for day in trip_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    image_url = await unsplash_service.get_photo_url(
                        f"{attraction.name} {request.city}"
                    )
                    attraction.image_url = image_url
        
        print("旅行计划生成完成！")
        return trip_plan
        
    except Exception as e:
        print(f"生成计划失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成计划失败: {str(e)}")
    
@router.get("/test")
async def test_route():
    """测试路由是否正常工作的接口"""
    return {"message": "Trip router is working!"}