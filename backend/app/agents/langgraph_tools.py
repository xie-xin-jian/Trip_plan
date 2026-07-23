"""LangGraph 旅行规划 Agent - 工具函数"""

import json
import re
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..services.amap_service import get_amap_service
from ..config import get_settings
from .prompts import SYSTEM_PROMPT, build_user_prompt


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


def _get_default_attractions(city: str):
    if city in DEFAULT_ATTRACTIONS:
        return DEFAULT_ATTRACTIONS[city]
    else:
        return [
            {"name": f"{city}博物馆", "address": f"{city}市中心", "category": "博物馆", "rating": "4.0", "ticket_price": 0},
            {"name": f"{city}公园", "address": f"{city}市区", "category": "公园", "rating": "4.2", "ticket_price": 0},
            {"name": f"{city}老街", "address": f"{city}历史街区", "category": "历史文化", "rating": "4.3", "ticket_price": 0},
            {"name": f"{city}广场", "address": f"{city}市中心", "category": "城市广场", "rating": "4.1", "ticket_price": 0},
        ]


# ==================== 工具 1: 搜索景点 ====================
@tool
def search_attractions(city: str, travel_days: int) -> str:
    """
    搜索目的地的热门景点。
    
    Args:
        city: 目的地城市名称
        travel_days: 旅行天数
        
    Returns:
        景点列表JSON字符串
    """
    print(f"\n[工具] 搜索景点: {city}, {travel_days}天")
    
    try:
        attractions = _get_default_attractions(city)
        print(f"[工具] 使用默认景点数据，找到 {len(attractions)} 个景点")
        return json.dumps(attractions, ensure_ascii=False)
            
    except Exception as e:
        print(f"[工具] 搜索景点失败: {e}")
        return json.dumps([], ensure_ascii=False)


# ==================== 工具 2: 获取天气 ====================
@tool
def get_weather_info(city: str, travel_days: int, start_date: str) -> str:
    """
    获取目的地城市的天气预报。
    
    Args:
        city: 目的地城市名称
        travel_days: 旅行天数
        start_date: 出发日期 (YYYY-MM-DD)
        
    Returns:
        天气预报JSON字符串
    """
    print(f"\n[工具] 获取天气: {city}, {start_date} + {travel_days}天")
    
    try:
        amap_service = get_amap_service()
        weather = amap_service.get_weather(city)
        
        if weather:
            result = [w.model_dump() for w in weather]
            print(f"[工具] 获取到 {len(result)} 天的天气")
            return json.dumps(result, ensure_ascii=False)
        else:
            return json.dumps([], ensure_ascii=False)
            
    except Exception as e:
        print(f"[工具] 获取天气失败: {e}")
        return json.dumps([], ensure_ascii=False)


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


def _get_default_hotels(city: str, accommodation: str):
    hotels = HOTEL_TEMPLATES.get(accommodation, HOTEL_TEMPLATES["舒适型"])
    return [
        {
            "name": f"{city}{h['name']}",
            "address": f"{city}市中心",
            "price_range": h["price_range"],
            "rating": h["rating"],
            "location": {"longitude": 116.0, "latitude": 39.0}
        }
        for h in hotels
    ]


# ==================== 工具 3: 搜索酒店 ====================
@tool
def search_hotels(city: str, travel_days: int, accommodation: str = "舒适型") -> str:
    """
    搜索目的地城市的酒店。
    
    Args:
        city: 目的地城市名称
        travel_days: 旅行天数
        accommodation: 住宿偏好 (经济型/舒适型/豪华型)
        
    Returns:
        酒店列表JSON字符串
    """
    print(f"\n[工具] 搜索酒店: {city}, {accommodation}")
    
    try:
        hotels = _get_default_hotels(city, accommodation)
        print(f"[工具] 使用默认酒店数据，找到 {len(hotels)} 家酒店")
        return json.dumps(hotels, ensure_ascii=False)
            
    except Exception as e:
        print(f"[工具] 搜索酒店失败: {e}")
        return json.dumps([], ensure_ascii=False)


# ==================== 工具 4: 搜索往返交通 ====================
@tool
def search_transportation(
    departure_city: str,
    destination_city: str,
    travel_days: int,
    transport_type: str = "all"
) -> str:
    """
    搜索出发地到目的地的往返交通信息。
    
    Args:
        departure_city: 出发城市
        destination_city: 目的城市
        travel_days: 旅行天数
        transport_type: 交通类型 (all/high_speed_rail/flight/bus)
        
    Returns:
        交通信息JSON字符串，包含去程和返程
    """
    print(f"\n[工具] 搜索交通: {departure_city} -> {destination_city}")
    
    try:
        amap_service = get_amap_service()
        
        # 搜索去程和返程的交通
        outbound = amap_service.search_transit(
            origin=departure_city,
            destination=destination_city
        )
        
        return_trip = amap_service.search_transit(
            origin=destination_city,
            destination=departure_city
        )
        
        result = {
            "departure_city": departure_city,
            "destination_city": destination_city,
            "outbound": outbound[:5] if outbound else [],
            "return_trip": return_trip[:5] if return_trip else []
        }
        
        print(f"[工具] 去程 {len(result['outbound'])} 个选项, 返程 {len(result['return_trip'])} 个选项")
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        print(f"[工具] 搜索交通失败: {e}")
        return json.dumps({"outbound": [], "return_trip": []}, ensure_ascii=False)


# ==================== 工具 5: 生成旅行计划 ====================
@tool
def generate_travel_plan(
    city: str,
    travel_days: int,
    start_date: str,
    end_date: str,
    attractions: str,
    hotels: str,
    weather: str,
    transportation: str,
    accommodation: str,
    preferences: str = "[]",
    free_text_input: str = ""
) -> str:
    """
    基于收集的信息生成完整的旅行计划提示词。
    
    Args:
        city: 目的地城市
        travel_days: 旅行天数
        start_date: 开始日期
        end_date: 结束日期
        attractions: 景点列表JSON
        hotels: 酒店列表JSON
        weather: 天气预报JSON
        transportation: 交通方式偏好
        accommodation: 住宿偏好
        preferences: 用户偏好列表JSON
        free_text_input: 用户额外输入
        
    Returns:
        完整的提示词（用于后续LLM调用）
    """
    print(f"\n[工具] 生成旅行计划提示词: {city}, {travel_days}天")
    
    # 解析JSON数据
    try:
        preferences_data = json.loads(preferences) if preferences else []
    except:
        preferences_data = []
    
    # 使用优化后的 prompt 模块构建提示词
    prompt = build_user_prompt(
        city=city,
        travel_days=travel_days,
        start_date=start_date,
        end_date=end_date,
        attractions=attractions,
        hotels=hotels,
        weather=weather,
        transportation=transportation,
        accommodation=accommodation,
        preferences=preferences_data,
        free_text_input=free_text_input if free_text_input else None
    )
    
    return prompt


# ==================== 工具列表 ====================
TOOLS = [
    search_attractions,
    get_weather_info,
    search_hotels,
    search_transportation,
    generate_travel_plan
]


def get_all_tools():
    """获取所有工具"""
    return TOOLS


def get_tool_by_name(name: str):
    """根据名称获取工具"""
    for t in TOOLS:
        if t.name == name:
            return t
    return None