"""旅行规划 API 路由 - LangGraph 版本"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
import json
import re
from datetime import datetime, timedelta

from openai import OpenAI

from ...models.schemas import (
    TripRequest,
    TripPlanResponse
)
from ...agents.adjust_plan import adjust_plan_with_llm_sync
from ...agents.user_feedback import save_feedback, FeedbackRecord, FeedbackType
from ...database import get_db, TripPlanDB, User
from ...auth import get_current_user
from ...config import get_settings

settings = get_settings()

client = OpenAI(
    api_key=settings.llm_api_key or settings.openai_api_key,
    base_url=settings.llm_base_url or settings.openai_base_url,
    timeout=120
)

router = APIRouter(prefix="/trip", tags=["旅行规划-LangGraph"])


# 可选用户依赖（不需要登录）
def get_optional_user():
    """获取可选用户（不强制登录）"""
    return None


DEFAULT_ATTRACTIONS = {
    "北京": [
        {"name": "故宫博物院", "address": "东城区景山前街4号", "category": "历史文化", "rating": "4.8", "ticket_price": 60},
        {"name": "天安门广场", "address": "东城区东长安街", "category": "地标景点", "rating": "4.9", "ticket_price": 0},
        {"name": "颐和园", "address": "海淀区新建宫门路19号", "category": "皇家园林", "rating": "4.7", "ticket_price": 30},
        {"name": "长城(八达岭)", "address": "延庆区G6京藏高速58号出口", "category": "世界遗产", "rating": "4.8", "ticket_price": 40},
        {"name": "天坛公园", "address": "东城区天坛内东里7号", "category": "皇家祭坛", "rating": "4.6", "ticket_price": 35},
        {"name": "鸟巢", "address": "朝阳区国家体育场南路1号", "category": "现代建筑", "rating": "4.5", "ticket_price": 50},
        {"name": "南锣鼓巷", "address": "东城区南锣鼓巷", "category": "历史文化街区", "rating": "4.3", "ticket_price": 0},
    ],
    "上海": [
        {"name": "外滩", "address": "黄浦区中山东一路", "category": "地标景点", "rating": "4.9", "ticket_price": 0},
        {"name": "东方明珠", "address": "浦东新区世纪大道1号", "category": "现代建筑", "rating": "4.5", "ticket_price": 160},
        {"name": "豫园", "address": "黄浦区福佑路168号", "category": "古典园林", "rating": "4.6", "ticket_price": 40},
        {"name": "迪士尼乐园", "address": "浦东新区川沙新镇黄赵路310号", "category": "主题乐园", "rating": "4.8", "ticket_price": 475},
        {"name": "南京路步行街", "address": "黄浦区南京东路", "category": "购物", "rating": "4.5", "ticket_price": 0},
        {"name": "城隍庙", "address": "黄浦区方浜中路249号", "category": "宗教文化", "rating": "4.4", "ticket_price": 0},
    ],
    "广州": [
        {"name": "广州塔", "address": "海珠区阅江西路222号", "category": "现代建筑", "rating": "4.7", "ticket_price": 150},
        {"name": "陈家祠", "address": "荔湾区中山七路恩龙里34号", "category": "历史文化", "rating": "4.6", "ticket_price": 10},
        {"name": "白云山", "address": "白云区广园中路801号", "category": "自然风光", "rating": "4.5", "ticket_price": 5},
        {"name": "长隆欢乐世界", "address": "番禺区迎宾路", "category": "主题乐园", "rating": "4.7", "ticket_price": 250},
        {"name": "沙面岛", "address": "荔湾区沙面北街", "category": "历史文化", "rating": "4.4", "ticket_price": 0},
    ],
    "杭州": [
        {"name": "西湖", "address": "西湖区龙井路1号", "category": "自然风光", "rating": "4.9", "ticket_price": 0},
        {"name": "灵隐寺", "address": "西湖区灵隐路法云弄1号", "category": "宗教文化", "rating": "4.7", "ticket_price": 75},
        {"name": "千岛湖", "address": "淳安县千岛湖镇", "category": "自然风光", "rating": "4.6", "ticket_price": 150},
        {"name": "宋城", "address": "西湖区之江路148号", "category": "主题乐园", "rating": "4.5", "ticket_price": 300},
        {"name": "雷峰塔", "address": "西湖区南山路", "category": "历史文化", "rating": "4.4", "ticket_price": 40},
    ],
    "成都": [
        {"name": "宽窄巷子", "address": "青羊区长顺街附近", "category": "历史文化街区", "rating": "4.5", "ticket_price": 0},
        {"name": "锦里", "address": "武侯区武侯祠大街231号", "category": "历史文化街区", "rating": "4.4", "ticket_price": 0},
        {"name": "大熊猫繁育研究基地", "address": "成华区熊猫大道1375号", "category": "动物观赏", "rating": "4.7", "ticket_price": 55},
        {"name": "武侯祠", "address": "武侯区武侯祠大街231号", "category": "历史文化", "rating": "4.6", "ticket_price": 50},
        {"name": "都江堰", "address": "都江堰市公园路", "category": "世界遗产", "rating": "4.7", "ticket_price": 80},
    ],
    "郑州": [
        {"name": "少林寺", "address": "登封市嵩山少林风景区", "category": "宗教文化", "rating": "4.7", "ticket_price": 100},
        {"name": "嵩山", "address": "登封市", "category": "自然风光", "rating": "4.5", "ticket_price": 80},
        {"name": "河南博物院", "address": "金水区农业路8号", "category": "博物馆", "rating": "4.6", "ticket_price": 0},
        {"name": "郑州黄河风景名胜区", "address": "惠济区", "category": "自然风光", "rating": "4.3", "ticket_price": 60},
        {"name": "二七塔", "address": "二七区", "category": "地标景点", "rating": "4.2", "ticket_price": 0},
        {"name": "CBD千玺广场", "address": "郑东新区", "category": "现代建筑", "rating": "4.4", "ticket_price": 80},
    ],
}

HOTEL_TEMPLATES = {
    "经济型": [
        {"name": "如家酒店", "price_range": "150-250元", "rating": "4.0"},
        {"name": "汉庭酒店", "price_range": "180-280元", "rating": "4.0"},
        {"name": "7天连锁", "price_range": "120-200元", "rating": "3.8"},
    ],
    "舒适型": [
        {"name": "全季酒店", "price_range": "300-450元", "rating": "4.5"},
        {"name": "亚朵酒店", "price_range": "350-500元", "rating": "4.6"},
        {"name": "锦江之星", "price_range": "250-380元", "rating": "4.2"},
    ],
    "豪华型": [
        {"name": "希尔顿酒店", "price_range": "800-1500元", "rating": "4.8"},
        {"name": "万豪酒店", "price_range": "900-1600元", "rating": "4.7"},
        {"name": "洲际酒店", "price_range": "850-1400元", "rating": "4.7"},
    ]
}


def _get_attractions(city: str):
    if city in DEFAULT_ATTRACTIONS:
        return DEFAULT_ATTRACTIONS[city]
    else:
        return [
            {"name": f"{city}博物馆", "address": f"{city}市中心", "category": "博物馆", "rating": "4.0", "ticket_price": 0},
            {"name": f"{city}公园", "address": f"{city}市区", "category": "公园", "rating": "4.2", "ticket_price": 0},
            {"name": f"{city}老街", "address": f"{city}历史街区", "category": "历史文化", "rating": "4.3", "ticket_price": 0},
        ]


def _get_hotels(city: str, accommodation: str):
    hotels = HOTEL_TEMPLATES.get(accommodation, HOTEL_TEMPLATES["舒适型"])
    return [
        {"name": f"{city}{h['name']}", "address": f"{city}市中心", "price_range": h["price_range"], "rating": h["rating"]}
        for h in hotels
    ]


def _get_weather(city: str, days: int, start_date: str):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except:
        start = datetime.now()
    
    weather_list = []
    for i in range(days):
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        weather_list.append({
            "date": date,
            "day_weather": "晴",
            "night_weather": "多云",
            "day_temp": 25,
            "night_temp": 18,
            "wind_direction": "南风",
            "wind_power": "1-3级"
        })
    return weather_list


def _extract_json(text: str) -> dict:
    """从 LLM 响应中提取 JSON - 多策略提取"""
    
    # 策略1: 从 ```json 代码块提取
    if "```json" in text.lower():
        s = text.lower().find("```json")
        marker_end = text.find("```", s + 7)
        if marker_end > s:
            candidate = text[s + 7:marker_end].strip()
            try:
                return json.loads(candidate)
            except:
                pass
    
    # 策略2: 从第一个 ``` 代码块到下一个 ``` 提取
    if "```" in text:
        s = text.find("```")
        marker_end = text.find("```", s + 3)
        if marker_end > s:
            candidate = text[s + 3:marker_end].strip()
            # 检查是否是 JSON
            if candidate.strip().startswith("{"):
                try:
                    return json.loads(candidate)
                except:
                    pass
    
    # 策略3: 查找最外层的 {}
    s = text.find("{")
    e = text.rfind("}")
    if s >= 0 and e > s:
        candidate = text[s:e + 1]
        try:
            return json.loads(candidate)
        except:
            pass
        
        # 策略3b: 清理尾随逗号再试一次
        try:
            cleaned = re.sub(r',\s*([}\]])', r'\1', candidate)
            return json.loads(cleaned)
        except:
            pass
    
    # 策略4: 从左到右匹配大括号
    level = 0
    start = -1
    for i, c in enumerate(text):
        if c == '{':
            if level == 0:
                start = i
            level += 1
        elif c == '}':
            level -= 1
            if level == 0 and start >= 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except:
                    # 清理后再试
                    try:
                        cleaned = re.sub(r',\s*([}\]])', r'\1', candidate)
                        return json.loads(cleaned)
                    except:
                        start = -1  # 继续查找下一个完整的 JSON
    
    return None


def _generate_fallback_plan(city: str, travel_days: int, start_date: str, end_date: str):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except:
        start = datetime.now()
    
    days = []
    attractions = _get_attractions(city)[:travel_days * 2]
    hotel = _get_hotels(city, "经济型")[0]
    
    # 解析酒店价格
    price_str = str(hotel.get("price_range", "150-200元"))
    try:
        hotel_cost = int(price_str.split("-")[0].replace("元", "").strip())
    except:
        hotel_cost = 150
    
    for i in range(travel_days):
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        day_attractions = attractions[i*2:(i+1)*2] if attractions else [
            {"name": f"{city}景点{i+1}", "address": city, "category": "景点", "ticket_price": 0}
        ]
        
        days.append({
            "date": date,
            "day_index": i,
            "description": f"第{i+1}天：{city}游览",
            "transportation": "公共交通",
            "accommodation": hotel["name"],
            "hotel": {
                "name": hotel["name"],
                "address": hotel["address"],
                "price_range": hotel["price_range"],
                "rating": hotel["rating"],
                "estimated_cost": hotel_cost,
                "location": {"longitude": 113.13, "latitude": 27.83}
            },
            "attractions": [
                {
                    "name": a["name"],
                    "address": a["address"],
                    "category": a["category"],
                    "ticket_price": a["ticket_price"],
                    "visit_duration": 120,
                    "description": f"{a['category']}类景点",
                    "location": {"longitude": 113.13, "latitude": 27.83}
                }
                for a in day_attractions
            ],
            "meals": [
                {"type": "breakfast", "name": "酒店早餐", "estimated_cost": 30},
                {"type": "lunch", "name": "当地特色餐厅", "estimated_cost": 60},
                {"type": "dinner", "name": "当地特色餐厅", "estimated_cost": 60}
            ]
        })
    
    plan = {
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "weather_info": _get_weather(city, travel_days, start_date),
        "budget": {
            "total_attractions": sum(a["ticket_price"] for d in days for a in d["attractions"]),
            "total_hotels": hotel_cost * travel_days,
            "total_meals": travel_days * 150,
            "total_transportation": 200,
            "total": 0
        },
        "overall_suggestions": f"欢迎来到{city}！这是一份{travel_days}天的旅行计划，建议提前预订酒店和热门景点门票。"
    }
    
    plan["budget"]["total"] = sum(plan["budget"].values())
    return plan


def _enrich_plan(plan: Dict[str, Any], city: str, days_count: int, start_date: str, accommodation: str) -> Dict[str, Any]:
    """补全计划数据，确保所有字段完整"""
    attractions = _get_attractions(city)
    hotels = _get_hotels(city, accommodation)
    weather = _get_weather(city, days_count, start_date)
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except:
        start = datetime.now()
    
    default_attraction_template = attractions[0] if attractions else {"name": "景点", "address": city, "category": "景点", "ticket_price": 0}
    default_hotel_template = hotels[0] if hotels else {"name": "经济型酒店", "address": city, "price_range": "150-200元", "rating": "4.0", "estimated_cost": 150}
    
    # 获取 LLM 返回的 days，不足时用空 dict 填充，多余时截断
    llm_days = plan.get("days", []) if isinstance(plan, dict) and isinstance(plan.get("days"), list) else []
    if len(llm_days) < days_count:
        # 补齐缺失的天
        llm_days = llm_days + [{} for _ in range(days_count - len(llm_days))]
    elif len(llm_days) > days_count:
        llm_days = llm_days[:days_count]
    
    processed_days = []
    for idx, day in enumerate(llm_days):
        if not isinstance(day, dict):
            day = {}
        
        # 处理景点
        day_attractions = []
        if "attractions" in day and isinstance(day["attractions"], list):
            for a in day["attractions"]:
                if not isinstance(a, dict):
                    continue
                attr = dict(a)
                if "name" not in attr or not attr["name"]:
                    continue
                attr.setdefault("address", city)
                attr.setdefault("visit_duration", 120)
                attr.setdefault("description", f"{attr.get('category', city)}景点")
                attr.setdefault("category", "景点")
                attr.setdefault("ticket_price", 0)
                attr.setdefault("location", {"longitude": 113.13, "latitude": 27.83})
                day_attractions.append(attr)
        
        if not day_attractions:
            # 填充默认景点
            for a in attractions[idx*2:(idx+1)*2]:
                day_attractions.append({
                    "name": a["name"],
                    "address": a["address"],
                    "visit_duration": 120,
                    "description": f"{a.get('category', city)}景点",
                    "category": a.get("category", "景点"),
                    "ticket_price": a.get("ticket_price", 0),
                    "location": {"longitude": 113.13, "latitude": 27.83}
                })
        
        # 处理酒店
        hotel = day.get("hotel") if isinstance(day.get("hotel"), dict) else None
        if not hotel:
            hotel = {
                "name": default_hotel_template.get("name", "经济型酒店"),
                "address": default_hotel_template.get("address", city),
                "price_range": default_hotel_template.get("price_range", "150-200元"),
                "rating": default_hotel_template.get("rating", "4.0"),
                "estimated_cost": default_hotel_template.get("estimated_cost", 150)
            }
        else:
            hotel = dict(hotel)
            hotel.setdefault("name", default_hotel_template.get("name", "经济型酒店"))
            hotel.setdefault("address", city)
            hotel.setdefault("price_range", default_hotel_template.get("price_range", "150-200元"))
            hotel.setdefault("rating", default_hotel_template.get("rating", "4.0"))
            hotel.setdefault("estimated_cost", int(str(default_hotel_template.get("price_range", "150-200")).split("-")[0].replace("元", "").strip()) if str(default_hotel_template.get("price_range", "150")).replace("元", "").replace("-", "").isdigit() else 150)
            hotel.setdefault("location", {"longitude": 113.13, "latitude": 27.83})
        
        # 处理餐饮
        meals = day.get("meals") if isinstance(day.get("meals"), list) else []
        if not meals:
            meals = [
                {"type": "breakfast", "name": "酒店早餐", "estimated_cost": 30},
                {"type": "lunch", "name": "当地特色餐厅", "estimated_cost": 60},
                {"type": "dinner", "name": "当地特色餐厅", "estimated_cost": 60}
            ]
        else:
            meals = [dict(m) if isinstance(m, dict) else {"type": "lunch", "name": "当地餐厅", "estimated_cost": 50} for m in meals]
            for m in meals:
                m.setdefault("type", "lunch")
                m.setdefault("name", "当地餐厅")
                m.setdefault("estimated_cost", 50)
        
        # 处理日期
        date_str = day.get("date") or (start + timedelta(days=idx)).strftime("%Y-%m-%d")
        
        # 构造完整day
        processed_day = {
            "date": date_str,
            "day_index": idx,
            "description": day.get("description") or f"第{idx+1}天：{city}游览",
            "transportation": day.get("transportation") or "公共交通",
            "accommodation": day.get("accommodation") or hotel.get("name", "经济型酒店"),
            "hotel": hotel,
            "attractions": day_attractions,
            "meals": meals
        }
        processed_days.append(processed_day)
    
    # 计算预算
    total_attractions = sum(a.get("ticket_price", 0) for d in processed_days for a in d["attractions"])
    total_hotels = sum(d["hotel"].get("estimated_cost", 150) for d in processed_days)
    total_meals = sum(m.get("estimated_cost", 50) for d in processed_days for m in d["meals"])
    total_transport = 200
    
    enriched_plan = {
        "city": city,
        "start_date": start_date,
        "end_date": plan.get("end_date", start_date),
        "days": processed_days,
        "weather_info": weather,
        "budget": {
            "total_attractions": total_attractions,
            "total_hotels": total_hotels,
            "total_meals": total_meals,
            "total_transportation": total_transport,
            "total": total_attractions + total_hotels + total_meals + total_transport
        },
        "overall_suggestions": plan.get("overall_suggestions") or f"欢迎来到{city}！这是一份{days_count}天的旅行计划，建议提前预订酒店和热门景点门票。"
    }
    
    return enriched_plan


@router.post(
    "/plan/langgraph",
    response_model=TripPlanResponse,
    summary="生成旅行计划 (LangGraph版)",
    description="使用 LLM 生成详细的旅行计划"
)
async def plan_trip_langgraph(
    request: TripRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    使用 LLM 生成旅行计划
    
    Args:
        request: 旅行请求参数
        current_user: 当前登录用户（可选）
        
    Returns:
        旅行计划响应
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 [LLM] 收到旅行规划请求:")
        print(f"   城市: {request.city}")
        print(f"   日期: {request.start_date} - {request.end_date}")
        print(f"   天数: {request.travel_days}")
        print(f"{'='*60}\n")
        
        print("🚀 [LLM] 获取数据...")
        
        attractions = _get_attractions(request.city)
        hotels = _get_hotels(request.city, request.accommodation)
        weather = _get_weather(request.city, request.travel_days, request.start_date)
        
        print(f"   景点: {len(attractions)}个")
        print(f"   酒店: {len(hotels)}家")
        print(f"   天气: {len(weather)}天")
        
        plan = None
        try:
            print("🚀 [LLM] 调用大模型生成计划...")
            
            prompt = f"""请为{request.city}规划{request.travel_days}天旅行计划。

## 基本信息
- 目的地: {request.city}
- 出发城市: {request.departure_city or '未指定'}
- 日期: {request.start_date} ~ {request.end_date}
- 交通方式: {request.transportation}
- 住宿偏好: {request.accommodation}
- 个人偏好: {', '.join(request.preferences) if request.preferences else '无'}

## 景点数据（从下面列表中选择安排到每天）
{json.dumps(attractions, ensure_ascii=False)}

## 酒店数据（从下面列表中选择）
{json.dumps(hotels, ensure_ascii=False)}

## 天气数据
{json.dumps(weather, ensure_ascii=False)}

## 输出要求【严格遵守以下格式】

只返回JSON格式，用```json```代码块包裹，不要任何解释文字。
必须严格按照以下字段结构输出：

{{{{
  "days": [
    {{{{
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天：城市游览主题",
      "transportation": "交通方式",
      "accommodation": "酒店名称",
      "hotel": {{{{
        "name": "酒店名称",
        "address": "酒店地址",
        "price_range": "150-200元",
        "rating": "4.0",
        "estimated_cost": 150
      }}}},
      "attractions": [
        {{{{
          "name": "景点名称",
          "address": "景点地址",
          "category": "景点分类",
          "ticket_price": 50,
          "visit_duration": 120,
          "description": "景点简介"
        }}}}
      ],
      "meals": [
        {{{{"type": "breakfast", "name": "早餐", "estimated_cost": 30}}}},
        {{{{"type": "lunch", "name": "午餐", "estimated_cost": 60}}}},
        {{{{"type": "dinner", "name": "晚餐", "estimated_cost": 60}}}}
      ]
    }}}}
  ],
  "overall_suggestions": "整体建议"
}}}}

重要规则：
1. days数组的长度必须精确等于 {request.travel_days}
2. day_index 从 0 开始递增
3. 所有数字类型字段（visit_duration, ticket_price, estimated_cost）必须是纯数字，不要加单位或引号
4. attractions 数组中必须有至少1个景点
5. 不要在 JSON 中添加注释
6. 不要省略任何字段

现在生成 {request.travel_days} 天的完整旅行计划："""
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一位专业的旅行规划师，请根据用户需求和提供的景点、酒店、天气数据，生成完整的旅行计划。只返回JSON格式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                timeout=120
            )
            
            content = response.choices[0].message.content
            print(f"[LLM] 收到响应，长度: {len(content)}字符")
            
            plan = _extract_json(content)
            
        except Exception as llm_error:
            print(f"❌ [LLM] 调用失败: {llm_error}")
        
        # 补全计划（LLM生成或兜底）
        # 策略: 只要 plan 有 days 列表就尝试融合；只有完全不可用才走兜底
        if plan and isinstance(plan, dict) and "days" in plan and isinstance(plan["days"], list) and len(plan["days"]) > 0:
            print(f"✅ [LLM] 计划生成成功（{len(plan.get('days',[]))} 天），正在补全字段...")
            enriched_plan = _enrich_plan(plan, request.city, request.travel_days, request.start_date, request.accommodation)
        else:
            print("⚠️ 使用兜底计划")
            enriched_plan = _generate_fallback_plan(request.city, request.travel_days, request.start_date, request.end_date)
        
        return TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=enriched_plan
        )
        
    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        plan = _generate_fallback_plan(request.city, request.travel_days, request.start_date, request.end_date)
        return TripPlanResponse(
            success=True,
            message=f"旅行计划生成成功（使用兜底数据）",
            data=plan
        )


class SavePlanRequest(BaseModel):
    title: str
    plan_data: dict


@router.post(
    "/save",
    summary="保存行程到数据库",
    description="将生成的旅行计划保存到当前用户的账户"
)
def save_plan(
    req: SavePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存行程"""
    try:
        new_plan = TripPlanDB(
            user_id=current_user.id,
            title=req.title,
            plan_data=json.dumps(req.plan_data, ensure_ascii=False)
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        return {
            "success": True,
            "message": "行程保存成功",
            "plan_id": new_plan.id
        }
    except Exception as e:
        print(f"❌ 保存行程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/plans")
def get_user_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户行程列表"""
    plans = db.query(TripPlanDB).filter(
        TripPlanDB.user_id == current_user.id
    ).order_by(TripPlanDB.created_at.desc()).all()
    
    return {
        "success": True,
        "plans": [
            {
                "id": p.id,
                "title": p.title,
                "created_at": p.created_at.isoformat()
            }
            for p in plans
        ]
    }


@router.get("/plan/{plan_id}")
def get_plan_detail(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取行程详情"""
    plan = db.query(TripPlanDB).filter(
        TripPlanDB.id == plan_id,
        TripPlanDB.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="行程不存在")
    
    return {
        "success": True,
        "id": plan.id,
        "title": plan.title,
        "data": json.loads(plan.plan_data),
        "created_at": plan.created_at.isoformat()
    }


@router.delete("/plan/{plan_id}")
def delete_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除行程"""
    plan = db.query(TripPlanDB).filter(
        TripPlanDB.id == plan_id,
        TripPlanDB.user_id == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="行程不存在")
    
    db.delete(plan)
    db.commit()
    
    return {"success": True, "message": "行程删除成功"}


class AdjustPlanRequest(BaseModel):
    plan_id: str
    original_plan: dict
    feedback: str


@router.post(
    "/plan/langgraph/adjust",
    summary="调整旅行计划 (LLM驱动)",
    description="使用LLM理解用户反馈，智能调整旅行计划"
)
async def adjust_trip_plan(
    request: AdjustPlanRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    使用LLM驱动的计划调整
    
    Args:
        request: 调整请求（包含原始计划和用户反馈）
        
    Returns:
        调整后的旅行计划
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 [LLM调整] 收到计划调整请求")
        print(f"   计划ID: {request.plan_id}")
        print(f"   用户反馈: {request.feedback}")
        print(f"{'='*60}\n")
        
        # 调用LLM调整
        result = adjust_plan_with_llm_sync(
            original_plan=request.original_plan,
            feedback=request.feedback,
            attractions="[]",
            hotels="[]"
        )
        
        if result["success"]:
            print("✅ [LLM调整] 计划调整成功")
            return TripPlanResponse(
                success=True,
                message="计划调整成功",
                data=result["plan"]
            )
        else:
            print(f"⚠️ [LLM调整] 使用兜底方案")
            return TripPlanResponse(
                success=True,
                message="计划调整成功（使用兜底方案）",
                data=result["plan"]
            )
            
    except Exception as e:
        print(f"❌ [LLM调整] 调整失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"调整计划失败: {str(e)}"
        )


class FeedbackRequest(BaseModel):
    plan_id: str
    feedback_type: str
    rating: Optional[int] = None
    comment: Optional[str] = None
    adjust_type: Optional[str] = None


@router.post(
    "/feedback",
    summary="提交用户反馈",
    description="提交对旅行计划的评分、评论或点赞"
)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    提交用户反馈
    
    Args:
        request: 反馈请求
        
    Returns:
        反馈提交结果
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 [反馈] 收到用户反馈")
        print(f"   计划ID: {request.plan_id}")
        print(f"   反馈类型: {request.feedback_type}")
        print(f"{'='*60}\n")
        
        user_id = current_user.id if current_user else None
        
        feedback = FeedbackRecord(
            feedback_id=f"fb_{int(__import__('time').time() * 1000)}",
            plan_id=request.plan_id,
            user_id=user_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            comment=request.comment,
            adjust_type=request.adjust_type
        )
        
        success = save_feedback(feedback)
        
        if success:
            print("✅ [反馈] 反馈保存成功")
            return {
                "success": True,
                "message": "反馈提交成功"
            }
        else:
            print("❌ [反馈] 反馈保存失败")
            raise HTTPException(
                status_code=500,
                detail="反馈提交失败"
            )
            
    except Exception as e:
        print(f"❌ [反馈] 提交失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"提交反馈失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "trip-planner-langgraph",
        "framework": "LangGraph"
    }