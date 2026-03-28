// frontend/src/types/index.ts

export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location: Location
  visit_duration: number
  description: string
  ticket_price: number
  is_indoor: boolean
  typecode: string
  image_url?: string
}

export interface Hotel {
  name: string
  address: string
  location: Location
  price_per_night: number
  total_price: number
  accommodation_type: string
  dist_to_attractions_km: number
  image_url?: string
}

export interface MealRecommendation {
  meal_type: string   // 早餐 / 午餐 / 晚餐
  name: string
  address: string
  location: Location
  dist_to_attractions_km: number
  suggestion: string
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: string
  night_temp: string
  wind_direction: string
  wind_power: string
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total: number
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  weather_note: string
  transportation: string
  accommodation: string
  hotel: Hotel | null
  attractions: Attraction[]
  meals: MealRecommendation[]
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  hotels: Hotel[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget: Budget | null
}

export interface TripPlanRequest {
  city: string
  start_date: string
  end_date: string
  days: number
  preferences: string
  budget: string
  transportation: string
  accommodation: string
}

export interface StreamProgress {
  progress: number
  status: string
  result?: TripPlan
}