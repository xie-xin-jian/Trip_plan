"""旅行规划Agent — LLM生成行程，天气用真实API"""

import json
import re
from datetime import datetime, timedelta
from ..services.llm_service import get_llm
from ..services.amap_service import get_amap_service
from ..models.schemas import (
    TripRequest, TripPlan, DayPlan, Attraction, Meal,
    WeatherInfo, Location, Hotel, Budget,
    RoundTripTransportation, TransportationOption
)
from ..config import get_settings

SYSTEM_PROMPT = """你是专业旅行规划师。基于你的知识直接生成详细的旅行计划JSON。

## 返回格式（严格遵循）

```json
{
  "city": "城市名",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天: 具体行程主题",
      "transportation": "市内交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "真实酒店名", "address": "详细地址",
        "location": {"longitude": 116.397, "latitude": 39.908},
        "price_range": "300-500元", "rating": "4.5",
        "distance": "距景点2km", "type": "舒适型", "estimated_cost": 350
      },
      "attractions": [
        {
          "name": "真实景点名", "address": "详细地址",
          "location": {"longitude": 116.397, "latitude": 39.916},
          "visit_duration": 120, "description": "景点介绍",
          "category": "类别", "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {"date": "YYYY-MM-DD", "day_weather": "晴", "night_weather": "多云",
     "day_temp": 25, "night_temp": 15, "wind_direction": "南风", "wind_power": "1-3级"}
  ],
  "overall_suggestions": "实用旅行建议",
  "budget": {"total_attractions": 180, "total_hotels": 1200, "total_meals": 480, "total_transportation": 200, "total": 2060},
  "round_trip_transportation": null
}
```

`round_trip_transportation` 仅在用户提供了出发城市时才填写，格式如下：
```json
{
  "departure_city": "出发城市",
  "destination_city": "目的城市",
  "outbound": [
    {"transport_type": "high_speed_rail", "transport_name": "G123", "departure_time": "08:00", "arrival_time": "12:30", "duration": "4h30m", "departure_station": "北京西站", "arrival_station": "郑州东站", "price_economy": 309, "price_business": 525, "seats_available": "有票"}
  ],
  "return_trip": [
    {"transport_type": "flight", "transport_name": "CZ6245", "departure_time": "16:00", "arrival_time": "18:15", "duration": "2h15m", "departure_station": "新郑机场", "arrival_station": "大兴机场", "price_economy": 580, "price_business": 1680, "seats_available": "有票"}
  ],
  "total_transport_budget": 889
}
```

## 规则
1. 每天2-3个景点，每天景点/餐饮/酒店不同
2. 用真实景点名和地址，经纬度要准确（用你的地理知识）
3. 温度纯数字，不带单位
4. 每天含早中晚三餐
5. 预算合理
6. 只返回JSON，在```json```代码块内
7. **重要**：如果用户提供了出发城市，必须填写round_trip_transportation（去程+返程各2-3个选项，不同时间段和价格）。如果没有出发城市，设为null。
"""


def _extract_json(text: str) -> str:
    """从文本中提取JSON"""
    # JSON代码块
    if "```json" in text:
        s = text.find("```json") + 7
        e = text.find("```", s)
        if e > s:
            return text[s:e].strip()
    if "```" in text:
        s = text.find("```") + 3
        e = text.find("```", s)
        if e > s:
            return text[s:e].strip()
    # 裸JSON
    s = text.find("{")
    e = text.rfind("}")
    if s >= 0 and e > s:
        return text[s:e + 1]
    return ""


def _clean_json(s: str) -> str:
    s = re.sub(r'//.*$', '', s, flags=re.MULTILINE)
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    return s


def _build_query(request: TripRequest) -> str:
    parts = [f"请为{request.city}规划{request.travel_days}天旅行。",
             f"日期: {request.start_date} ~ {request.end_date}",
             f"天数: {request.travel_days}天",
             f"市内交通: {request.transportation}",
             f"住宿偏好: {request.accommodation}"]
    if request.preferences:
        parts.append(f"偏好: {', '.join(request.preferences)}")
    if request.free_text_input:
        parts.append(f"额外要求: {request.free_text_input}")

    if request.departure_city:
        pt = request.preferred_transport_type or "all"
        parts.append(f"出发城市: {request.departure_city}")
        parts.append(f"交通偏好: {pt}")
        parts.append("请在JSON中增加round_trip_transportation字段，包含去程和返程各2-3个真实交通选项")

    return "\n".join(parts)


class TripPlannerAgent:
    """旅行规划Agent"""

    def __init__(self):
        print("[INIT] Initializing trip planner...")
        self.llm = get_llm()
        settings = get_settings()
        self.amap_key = settings.amap_api_key
        print(f"[OK] LLM: {self.llm.model}, Amap key: {'yes' if self.amap_key else 'no'}")

    def plan_trip(self, request: TripRequest) -> TripPlan:
        print(f"\n[PLAN] {request.city} | {request.travel_days}天 | {request.start_date}~{request.end_date}")
        if request.departure_city:
            print(f"[PLAN]   {request.departure_city} → {request.city}")

        query = _build_query(request)

        # 尝试 LLM 直接生成
        for attempt in range(2):
            try:
                response = self.llm.invoke([
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ])
                print(f"[LLM] Attempt {attempt + 1}: {len(response)} chars")

                json_str = _extract_json(response)
                if json_str:
                    data = json.loads(_clean_json(json_str))
                    # 补全必要字段
                    data.setdefault("city", request.city)
                    data.setdefault("start_date", request.start_date)
                    data.setdefault("end_date", request.end_date)
                    data.setdefault("overall_suggestions", f"祝您在{request.city}旅途愉快！")

                    if not data.get("days"):
                        raise ValueError("days field missing")

                    start = datetime.strptime(request.start_date, "%Y-%m-%d")
                    for i, day in enumerate(data["days"]):
                        day.setdefault("date", (start + timedelta(days=i)).strftime("%Y-%m-%d"))
                        day.setdefault("day_index", i)
                        day.setdefault("attractions", [])
                        day.setdefault("meals", [])
                        if not day.get("hotel"):
                            day["hotel"] = None

                    # 用真实API的天气数据覆盖LLM生成的数据
                    print(f"\n[天气] 正在获取 {request.city} 的真实天气数据...")
                    amap_service = get_amap_service()
                    real_weather = amap_service.get_weather(request.city)

                    if real_weather:
                        # 根据旅行天数截取或扩展
                        weather_info = []
                        for i in range(request.travel_days):
                            if i < len(real_weather):
                                weather_info.append(real_weather[i])
                            else:
                                # 超出预报范围的，用最后一天的天气数据
                                last = real_weather[-1]
                                weather_info.append(WeatherInfo(
                                    date=(start + timedelta(days=i)).strftime("%Y-%m-%d"),
                                    day_weather=last.day_weather,
                                    night_weather=last.night_weather,
                                    day_temp=last.day_temp,
                                    night_temp=last.night_temp,
                                    wind_direction=last.wind_direction,
                                    wind_power=last.wind_power
                                ))
                        data["weather_info"] = [w.model_dump() for w in weather_info]
                        print(f"[天气] 已应用真实天气数据: {len(weather_info)} 天")
                    else:
                        # API失败时的兜底数据（仅在无法获取真实数据时使用）
                        data["weather_info"] = [{
                            "date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                            "day_weather": "查询失败", "night_weather": "查询失败",
                            "day_temp": 0, "night_temp": 0,
                            "wind_direction": "-", "wind_power": "-"
                        } for i in range(request.travel_days)]
                        print(f"[天气] ⚠️  真实天气数据获取失败，使用兜底数据")

                    if not data.get("budget"):
                        data["budget"] = None

                    plan = TripPlan(**data)
                    print(f"[OK] Plan: {len(plan.days)} days")
                    return plan

                else:
                    print(f"[WARN] No JSON found, retrying...")
                    query = "请直接返回JSON，不要任何解释文字。\n" + query

            except Exception as e:
                print(f"[ERR] Attempt {attempt + 1}: {e}")
                if attempt == 0:
                    query = f"上次失败了（{e}）。请务必在```json```代码块中返回完整JSON，确保days数组不为空。\n" + _build_query(request)

        # 最终兜底
        return self._minimal_plan(request)

    def _minimal_plan(self, request: TripRequest) -> TripPlan:
        """最简兜底"""
        print("[FALLBACK] Using minimal plan")
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        days = []
        for i in range(request.travel_days):
            d = start + timedelta(days=i)
            days.append(DayPlan(
                date=d.strftime("%Y-%m-%d"), day_index=i,
                description=f"第{i+1}天",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[Attraction(
                    name=f"{request.city}景点{j + 1}", address=f"{request.city}市",
                    location=Location(longitude=0, latitude=0),
                    visit_duration=120, description="请查看高德地图",
                    category="景点", ticket_price=0
                ) for j in range(2)],
                meals=[Meal(type=t, name=f"{request.city}美食", estimated_cost=30)
                       for t in ["breakfast", "lunch", "dinner"]]
            ))
        return TripPlan(
            city=request.city, start_date=request.start_date, end_date=request.end_date,
            days=days, overall_suggestions=f"请在高德地图搜索{request.city}景点",
            weather_info=[], round_trip_transportation=None
        )


_planner_instance = None


def get_trip_planner_agent() -> TripPlannerAgent:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = TripPlannerAgent()
    return _planner_instance
