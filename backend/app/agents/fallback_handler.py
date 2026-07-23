"""失败兜底模块 - Fallback Handler"""

import json
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class FallbackLevel:
    """兜底级别"""
    L1_SOFT = "L1_soft"           # 软兜底：使用默认值
    L2_MEDIUM = "L2_medium"       # 中兜底：使用缓存/通用数据
    L3_HARD = "L3_hard"           # 硬兜底：返回错误信息
    L4_EMERGENCY = "L4_emergency" # 紧急兜底：使用预设模板


class FallbackResult:
    """兜底结果"""
    
    def __init__(
        self,
        data: Any,
        level: str,
        used_fallback: bool = True,
        source: str = "fallback",
        message: str = ""
    ):
        self.data = data
        self.level = level
        self.used_fallback = used_fallback
        self.source = source
        self.message = message
    
    def to_dict(self):
        return {
            "data": self.data,
            "level": self.level,
            "used_fallback": self.used_fallback,
            "source": self.source,
            "message": self.message
        }


# ==================== 景点兜底 ====================
DEFAULT_ATTRACTIONS = {
    "北京": [
        {"name": "故宫博物院", "address": "东城区景山前街4号", "category": "历史文化", "ticket_price": 60},
        {"name": "天安门广场", "address": "东城区东长安街", "category": "地标景点", "ticket_price": 0},
        {"name": "颐和园", "address": "海淀区新建宫门路19号", "category": "皇家园林", "ticket_price": 30},
        {"name": "长城(八达岭)", "address": "延庆区G6京藏高速58号出口", "category": "世界遗产", "ticket_price": 40},
        {"name": "天坛公园", "address": "东城区天坛内东里7号", "category": "皇家祭坛", "ticket_price": 35},
    ],
    "上海": [
        {"name": "外滩", "address": "黄浦区中山东一路", "category": "地标景点", "ticket_price": 0},
        {"name": "东方明珠", "address": "浦东新区世纪大道1号", "category": "现代建筑", "ticket_price": 160},
        {"name": "豫园", "address": "黄浦区福佑路168号", "category": "古典园林", "ticket_price": 40},
        {"name": "迪士尼乐园", "address": "浦东新区川沙新镇黄赵路310号", "category": "主题乐园", "ticket_price": 475},
    ],
    "广州": [
        {"name": "广州塔", "address": "海珠区阅江西路222号", "category": "现代建筑", "ticket_price": 150},
        {"name": "陈家祠", "address": "荔湾区中山七路恩龙里34号", "category": "历史文化", "ticket_price": 10},
        {"name": "白云山", "address": "白云区广园中路801号", "category": "自然风光", "ticket_price": 5},
    ],
    "杭州": [
        {"name": "西湖", "address": "西湖区龙井路1号", "category": "自然风光", "ticket_price": 0},
        {"name": "灵隐寺", "address": "西湖区灵隐路法云弄1号", "category": "宗教文化", "ticket_price": 75},
        {"name": "千岛湖", "address": "淳安县千岛湖镇", "category": "自然风光", "ticket_price": 150},
    ],
    "成都": [
        {"name": "宽窄巷子", "address": "青羊区长顺街附近", "category": "历史文化街区", "ticket_price": 0},
        {"name": "锦里", "address": "武侯区武侯祠大街231号", "category": "历史文化街区", "ticket_price": 0},
        {"name": "大熊猫繁育研究基地", "address": "成华区熊猫大道1375号", "category": "动物观赏", "ticket_price": 55},
    ],
}


def fallback_attractions(city: str, travel_days: int) -> FallbackResult:
    """景点搜索失败时的兜底"""
    if city in DEFAULT_ATTRACTIONS:
        attractions = DEFAULT_ATTRACTIONS[city]
        return FallbackResult(
            data=attractions,
            level=FallbackLevel.L1_SOFT,
            source="default_data",
            message=f"使用{city}默认景点数据（API失败）"
        )
    else:
        generic_attractions = [
            {"name": f"{city}博物馆", "address": f"{city}市中心", "category": "博物馆", "ticket_price": 0},
            {"name": f"{city}公园", "address": f"{city}市区", "category": "公园", "ticket_price": 0},
            {"name": f"{city}老街", "address": f"{city}历史街区", "category": "历史文化", "ticket_price": 0},
            {"name": f"{city}广场", "address": f"{city}市中心", "category": "城市广场", "ticket_price": 0},
        ]
        return FallbackResult(
            data=generic_attractions,
            level=FallbackLevel.L2_MEDIUM,
            source="generic_template",
            message=f"未找到{city}专属数据，使用通用模板"
        )


# ==================== 天气兜底 ====================
def fallback_weather(city: str, travel_days: int, start_date: str) -> FallbackResult:
    """天气获取失败时的兜底"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except:
        start = datetime.now()
    
    weather_list = []
    for i in range(travel_days):
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        weather_list.append({
            "date": date,
            "day_weather": "晴",
            "night_weather": "多云",
            "day_temp": 20 + random.randint(-5, 10),
            "night_temp": 10 + random.randint(-5, 10),
            "wind_direction": "南风",
            "wind_power": "1-3级",
            "suggestion": "建议出行前查看实时天气预报"
        })
    
    return FallbackResult(
        data=weather_list,
        level=FallbackLevel.L2_MEDIUM,
        source="default_weather",
        message="天气API失败，使用默认天气数据（建议出行前查看实时天气）"
    )


# ==================== 酒店兜底 ====================
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


def fallback_hotels(city: str, accommodation: str = "舒适型") -> FallbackResult:
    """酒店搜索失败时的兜底"""
    hotels = HOTEL_TEMPLATES.get(accommodation, HOTEL_TEMPLATES["舒适型"])
    
    hotel_list = []
    for h in hotels:
        hotel_list.append({
            "name": f"{city}{h['name']}",
            "address": f"{city}市中心",
            "price_range": h["price_range"],
            "rating": h["rating"],
            "location": {"longitude": 116.0, "latitude": 39.0}
        })
    
    return FallbackResult(
        data=hotel_list,
        level=FallbackLevel.L1_SOFT,
        source="default_hotels",
        message=f"使用{accommodation}默认酒店模板（API失败）"
    )


# ==================== 交通兜底 ====================
def fallback_transport(departure_city: str, destination_city: str) -> FallbackResult:
    """交通搜索失败时的兜底"""
    return FallbackResult(
        data={
            "outbound": [
                {"type": "建议查询", "note": f"请通过12306查询{departure_city}到{destination_city}的车次"},
                {"type": "建议查询", "note": f"请通过携程查询{departure_city}到{destination_city}的航班"},
            ],
            "return_trip": [
                {"type": "建议查询", "note": f"请通过12306查询{destination_city}到{departure_city}的车次"},
            ]
        },
        level=FallbackLevel.L4_EMERGENCY,
        source="manual_query",
        message="交通API失败，建议手动查询12306/携程"
    )


# ==================== 计划生成兜底 ====================
def fallback_plan(city: str, travel_days: int, start_date: str, end_date: str, reason: str = "") -> FallbackResult:
    """计划生成失败时的兜底 - 返回基础模板"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except:
        start = datetime.now()
    
    days = []
    for i in range(travel_days):
        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        days.append({
            "date": date,
            "day_index": i,
            "description": f"第{i+1}天：{city}自由行",
            "transportation": "建议公共交通",
            "accommodation": "建议提前预订",
            "attractions": [],
            "meals": [
                {"type": "breakfast", "name": "酒店早餐或当地小吃", "estimated_cost": 30},
                {"type": "lunch", "name": "当地特色餐厅", "estimated_cost": 80},
                {"type": "dinner", "name": "当地特色餐厅", "estimated_cost": 80}
            ],
            "_fallback": True
        })
    
    plan = {
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "weather_info": [],
        "budget": None,
        "round_trip_transportation": None,
        "overall_suggestions": f"系统暂时无法生成详细计划，请稍后重试。{reason}",
        "_fallback": True,
        "_fallback_level": FallbackLevel.L3_HARD
    }
    
    return FallbackResult(
        data=plan,
        level=FallbackLevel.L3_HARD,
        source="basic_template",
        message=f"LLM生成失败，返回基础模板。原因：{reason}"
    )


# ==================== 错误分类 ====================
class ErrorCategory:
    """错误分类"""
    API_ERROR = "api_error"               # 外部API调用失败
    LLM_ERROR = "llm_error"               # LLM调用失败
    PARSE_ERROR = "parse_error"           # 解析失败
    VALIDATION_ERROR = "validation_error" # 校验失败
    TIMEOUT_ERROR = "timeout_error"       # 超时
    UNKNOWN_ERROR = "unknown_error"       # 未知错误


def classify_error(error: Exception) -> str:
    """分类错误类型"""
    error_str = str(error).lower()
    
    if "api" in error_str or "network" in error_str or "connection" in error_str:
        return ErrorCategory.API_ERROR
    elif "llm" in error_str or "openai" in error_str or "deepseek" in error_str:
        return ErrorCategory.LLM_ERROR
    elif "json" in error_str or "parse" in error_str:
        return ErrorCategory.PARSE_ERROR
    elif "validation" in error_str:
        return ErrorCategory.VALIDATION_ERROR
    elif "timeout" in error_str or "timed out" in error_str:
        return ErrorCategory.TIMEOUT_ERROR
    else:
        return ErrorCategory.UNKNOWN_ERROR


# ==================== 统一兜底入口 ====================
def handle_fallback(
    error: Exception,
    context: Dict[str, Any]
) -> FallbackResult:
    """
    统一兜底处理入口
    
    Args:
        error: 异常对象
        context: 上下文信息，包含：
            - operation: 操作类型 (attractions/weather/hotels/transport/plan)
            - city: 城市
            - travel_days: 天数
            - start_date: 开始日期
            - 其他参数
    
    Returns:
        FallbackResult: 兜底结果
    """
    error_category = classify_error(error)
    operation = context.get("operation", "")
    
    print(f"\n[兜底] 触发兜底机制")
    print(f"[兜底] 错误类型: {error_category}")
    print(f"[兜底] 失败操作: {operation}")
    print(f"[兜底] 错误信息: {str(error)}")
    
    if operation == "attractions":
        return fallback_attractions(
            city=context.get("city", ""),
            travel_days=context.get("travel_days", 3)
        )
    elif operation == "weather":
        return fallback_weather(
            city=context.get("city", ""),
            travel_days=context.get("travel_days", 3),
            start_date=context.get("start_date", "")
        )
    elif operation == "hotels":
        return fallback_hotels(
            city=context.get("city", ""),
            accommodation=context.get("accommodation", "舒适型")
        )
    elif operation == "transport":
        return fallback_transport(
            departure_city=context.get("departure_city", ""),
            destination_city=context.get("destination_city", "")
        )
    elif operation == "plan":
        return fallback_plan(
            city=context.get("city", ""),
            travel_days=context.get("travel_days", 3),
            start_date=context.get("start_date", ""),
            end_date=context.get("end_date", ""),
            reason=str(error)
        )
    else:
        return FallbackResult(
            data=None,
            level=FallbackLevel.L4_EMERGENCY,
            source="unknown",
            message=f"未知操作类型: {operation}, 错误: {str(error)}"
        )


# ==================== 测试 ====================
def test_fallback():
    """测试兜底功能"""
    print("=" * 60)
    print("兜底机制测试")
    print("=" * 60)
    
    # 1. 景点兜底
    print("\n[测试1] 景点兜底")
    result = fallback_attractions("北京", 3)
    print(f"  级别: {result.level}")
    print(f"  数据数量: {len(result.data)}")
    print(f"  消息: {result.message}")
    
    print("\n[测试2] 未知城市景点兜底")
    result = fallback_attractions("未知城市", 3)
    print(f"  级别: {result.level}")
    print(f"  数据: {result.data[:2]}")
    
    # 2. 天气兜底
    print("\n[测试3] 天气兜底")
    result = fallback_weather("北京", 3, "2024-05-01")
    print(f"  级别: {result.level}")
    print(f"  数据天数: {len(result.data)}")
    print(f"  消息: {result.message}")
    
    # 3. 酒店兜底
    print("\n[测试4] 酒店兜底")
    result = fallback_hotels("北京", "舒适型")
    print(f"  级别: {result.level}")
    print(f"  酒店数: {len(result.data)}")
    
    # 4. 计划兜底
    print("\n[测试5] 计划生成兜底")
    result = fallback_plan("北京", 3, "2024-05-01", "2024-05-03", "测试失败")
    print(f"  级别: {result.level}")
    print(f"  天数: {len(result.data['days'])}")
    print(f"  消息: {result.message}")
    
    # 5. 错误分类
    print("\n[测试6] 错误分类")
    errors = [
        Exception("Connection timeout"),
        Exception("API key invalid"),
        Exception("JSON decode error"),
        Exception("LLM rate limit exceeded"),
    ]
    for err in errors:
        category = classify_error(err)
        print(f"  '{str(err)}' -> {category}")
    
    # 6. 统一入口
    print("\n[测试7] 统一兜底入口")
    try:
        raise Exception("API connection failed")
    except Exception as e:
        result = handle_fallback(e, {
            "operation": "attractions",
            "city": "上海",
            "travel_days": 3
        })
        print(f"  级别: {result.level}")
        print(f"  景点数: {len(result.data)}")
        print(f"  消息: {result.message}")


if __name__ == "__main__":
    test_fallback()