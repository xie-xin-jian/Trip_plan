// 类型定义

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
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating: string
  distance: string
  type: string
  estimated_cost?: number
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
  transportation: string
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface TransportationOption {
  transport_type: string
  transport_name: string
  departure_time: string
  arrival_time: string
  duration: string
  departure_station: string
  arrival_station: string
  price_economy: number
  price_business?: number
  seats_available: string
}

export interface RoundTripTransportation {
  departure_city: string
  destination_city: string
  outbound: TransportationOption[]
  return_trip: TransportationOption[]
  total_transport_budget: number
}

export interface TripFormData {
  city: string
  departure_city?: string
  preferred_transport_type?: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  round_trip_transportation?: RoundTripTransportation
}

export interface TripPlanResponse {
  success: boolean
  message: string
  data?: TripPlan
}

