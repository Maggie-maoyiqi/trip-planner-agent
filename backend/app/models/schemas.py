# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# ─────────────────────────────────────────
# 请求模型
# ─────────────────────────────────────────

class TripPlanRequest(BaseModel):
    city: str = Field(..., description="目的地城市")
    start_date: str = Field(..., description="出发日期 YYYY-MM-DD")
    end_date: str = Field(..., description="返回日期 YYYY-MM-DD")
    days: int = Field(..., ge=1, le=14, description="行程天数")
    preferences: str = Field(default="景点 旅游", description="游玩偏好，如：历史文化、自然风光")
    budget: str = Field(default="中等", description="预算描述，如：经济、中等、豪华")
    transportation: str = Field(default="公交", description="交通方式，如：飞机、高铁、自驾")
    accommodation: str = Field(default="舒适", description="住宿类型，如：经济、舒适、豪华")

# ─────────────────────────────────────────
# 基础地理模型
# ─────────────────────────────────────────

class Location(BaseModel):
    longitude: float = Field(default=0.0)
    latitude: float = Field(default=0.0)

# ─────────────────────────────────────────
# 景点
# ─────────────────────────────────────────

class Attraction(BaseModel):
    name: str
    address: str = ""
    location: Location = Field(default_factory=Location)
    visit_duration: int = Field(default=120, description="建议游览时间（分钟）")
    description: str = ""
    ticket_price: float = Field(default=0.0, description="门票价格（元）")
    is_indoor: bool = Field(default=False)
    typecode: str = Field(default="")
    image_url: Optional[str] = None
    best_visit_time: str = Field(default="", description="适合游玩时段")
    llm_reason: str = Field(default="", description="LLM 推荐理由")

# ─────────────────────────────────────────
# 酒店
# ─────────────────────────────────────────

class Hotel(BaseModel):
    name: str
    address: str = ""
    location: Location = Field(default_factory=Location)
    price_per_night: float = Field(default=0.0, description="每晚价格（元）")
    total_price: float = Field(default=0.0, description="总住宿费用（元）")
    accommodation_type: str = Field(default="", description="住宿类型")
    dist_to_attractions_km: float = Field(default=0.0, description="距当日景点中心距离（km）")
    image_url: Optional[str] = None

# ─────────────────────────────────────────
# 餐厅 / 每餐推荐
# ─────────────────────────────────────────

class MealRecommendation(BaseModel):
    meal_type: str = Field(..., description="早餐 / 午餐 / 晚餐")
    name: str
    address: str = ""
    location: Location = Field(default_factory=Location)
    dist_to_attractions_km: float = Field(default=0.0)
    suggestion: str = Field(default="")
    estimated_cost_per_person: float = Field(default=0.0, description="预估人均消费")

# ─────────────────────────────────────────
# 天气
# ─────────────────────────────────────────

class WeatherInfo(BaseModel):
    date: str
    day_weather: str = ""
    night_weather: str = ""
    day_temp: str = "0"
    night_temp: str = "0"
    wind_direction: str = ""
    wind_power: str = ""

# ─────────────────────────────────────────
# 预算明细
# ─────────────────────────────────────────

class Budget(BaseModel):
    total_attractions: float = Field(default=0.0, description="景点门票合计")
    total_hotels: float = Field(default=0.0, description="住宿费用合计")
    total_meals: float = Field(default=0.0, description="餐饮费用合计")
    total_transportation: float = Field(default=0.0, description="交通费用合计")
    total: float = Field(default=0.0, description="总费用估算")


class DailyScheduleItem(BaseModel):
    time_slot: str = Field(default="", description="上午/午餐/下午/晚餐/晚上")
    start_time: str = Field(default="", description="建议开始时间")
    end_time: str = Field(default="", description="建议结束时间")
    item_type: str = Field(default="", description="attraction/meal/hotel/rest")
    title: str = Field(default="")
    reference_name: str = Field(default="", description="对应景点/餐厅/酒店名称")
    duration_minutes: int = Field(default=0)
    estimated_cost: float = Field(default=0.0)
    note: str = Field(default="")


class RouteSegment(BaseModel):
    from_name: str = Field(default="")
    to_name: str = Field(default="")
    mode: str = Field(default="", description="步行/驾车/公交/骑行")
    distance_km: float = Field(default=0.0)
    duration_minutes: int = Field(default=0)
    instruction: str = Field(default="")
    polyline: List[Location] = Field(default_factory=list)

# ─────────────────────────────────────────
# 每日行程
# ─────────────────────────────────────────

class DayPlan(BaseModel):
    date: str = Field(..., description="如：第1天")
    day_index: int = Field(default=0)
    description: str = ""
    weather_note: str = Field(default="", description="天气提示，恶劣天气时说明")
    clothing_recommendation: str = Field(default="", description="穿衣建议")
    transportation: str = ""
    accommodation: str = Field(default="", description="当晚住宿名称")
    hotel: Optional[Hotel] = None
    attractions: List[Attraction] = Field(default_factory=list)
    meals: List[MealRecommendation] = Field(default_factory=list)
    schedule: List[DailyScheduleItem] = Field(default_factory=list)
    route_segments: List[RouteSegment] = Field(default_factory=list)

# ─────────────────────────────────────────
# 完整行程计划（API 响应）
# ─────────────────────────────────────────

class TripPlan(BaseModel):
    city: str
    start_date: str
    end_date: str
    days: List[DayPlan] = Field(default_factory=list)
    hotels: List[Hotel] = Field(default_factory=list, description="推荐酒店列表（供前端展示）")
    weather_info: List[WeatherInfo] = Field(default_factory=list)
    overall_suggestions: str = ""
    budget: Optional[Budget] = None
