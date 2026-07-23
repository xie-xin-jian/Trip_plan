"""任务识别模块 - Intent Recognition"""

from typing import Literal, Optional
from enum import Enum
import re


class IntentType(Enum):
    """意图类型枚举"""
    GENERATE_PLAN = "generate_plan"
    QUERY_ATTRACTIONS = "query_attractions"
    QUERY_WEATHER = "query_weather"
    QUERY_HOTELS = "query_hotels"
    QUERY_TRANSPORT = "query_transport"
    ADJUST_PLAN = "adjust_plan"
    RECOMMEND_FOOD = "recommend_food"
    UNKNOWN = "unknown"


class IntentResult:
    """意图识别结果"""
    
    def __init__(
        self,
        intent: IntentType,
        confidence: float,
        city: Optional[str] = None,
        travel_days: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        departure_city: Optional[str] = None,
        keywords: Optional[list] = None,
        raw_input: Optional[str] = None
    ):
        self.intent = intent
        self.confidence = confidence
        self.city = city
        self.travel_days = travel_days
        self.start_date = start_date
        self.end_date = end_date
        self.departure_city = departure_city
        self.keywords = keywords or []
        self.raw_input = raw_input
    
    def __repr__(self):
        return f"IntentResult(intent={self.intent.value}, confidence={self.confidence:.2f}, city={self.city}, days={self.travel_days})"
    
    def to_dict(self):
        return {
            "intent": self.intent.value,
            "confidence": round(self.confidence, 2),
            "city": self.city,
            "travel_days": self.travel_days,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "departure_city": self.departure_city,
            "keywords": self.keywords
        }


# ==================== 城市名称映射 ====================
CITY_KEYWORDS = {
    "北京": ["北京", "帝都", "京城", "BJ"],
    "上海": ["上海", "魔都", "沪", "SH"],
    "广州": ["广州", "羊城", "穗", "GZ"],
    "深圳": ["深圳", "鹏城", "SZ"],
    "杭州": ["杭州", "杭", "天堂"],
    "成都": ["成都", "蓉城", "天府"],
    "西安": ["西安", "古都", "长安"],
    "南京": ["南京", "金陵", "宁"],
    "武汉": ["武汉", "江城"],
    "重庆": ["重庆", "山城", "渝"],
    "天津": ["天津", "津"],
    "苏州": ["苏州", "姑苏"],
    "厦门": ["厦门", "鹭岛"],
    "青岛": ["青岛", "岛城"],
    "大连": ["大连", "滨城"],
    "昆明": ["昆明", "春城"],
    "哈尔滨": ["哈尔滨", "冰城"],
    "沈阳": ["沈阳", "盛京"],
    "长沙": ["长沙", "星城"],
    "郑州": ["郑州", "商都"],
}


def extract_city(text: str) -> Optional[str]:
    """从文本中提取城市名称"""
    for city, aliases in CITY_KEYWORDS.items():
        for alias in aliases:
            if alias in text:
                return city
    return None


def extract_travel_days(text: str) -> Optional[int]:
    """从文本中提取旅行天数"""
    patterns = [
        r'(\d+)天',
        r'(\d+)日',
        r'(\d+)晚',
        r'(\d+)夜',
        r'(\d+)天(\d+)晚',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    return None


def extract_date(text: str) -> tuple:
    """从文本中提取日期"""
    date_pattern = r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?'
    matches = re.findall(date_pattern, text)
    
    if matches:
        if len(matches) == 1:
            date_str = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
            return date_str, None
        elif len(matches) >= 2:
            start_date = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
            end_date = f"{matches[1][0]}-{matches[1][1].zfill(2)}-{matches[1][2].zfill(2)}"
            return start_date, end_date
    
    return None, None


def extract_departure_city(text: str) -> Optional[str]:
    """从文本中提取出发城市"""
    departure_patterns = [
        r'从(.+?)出发',
        r'从(.+?)去',
        r'从(.+?)到',
        r'(.+?)出发',
    ]
    
    for pattern in departure_patterns:
        match = re.search(pattern, text)
        if match:
            city = extract_city(match.group(1))
            if city:
                return city
    return None


# ==================== 意图识别规则 ====================
INTENT_PATTERNS = {
    IntentType.GENERATE_PLAN: [
        (r'规划|行程|计划|攻略|安排', 0.8),
        (r'去(.+?)玩', 0.7),
        (r'旅行|旅游|游玩', 0.6),
        (r'怎么安排|如何安排', 0.7),
    ],
    IntentType.QUERY_ATTRACTIONS: [
        (r'景点|景区|好玩的|哪里好玩', 0.8),
        (r'名胜|古迹|风景', 0.7),
        (r'推荐景点|必去景点', 0.9),
    ],
    IntentType.QUERY_WEATHER: [
        (r'天气|预报|气温|冷不冷', 0.8),
        (r'下雨|晴天|温度', 0.7),
    ],
    IntentType.QUERY_HOTELS: [
        (r'酒店|住宿|宾馆|旅馆', 0.8),
        (r'住哪里|推荐酒店', 0.9),
    ],
    IntentType.QUERY_TRANSPORT: [
        (r'交通|高铁|飞机|火车|动车', 0.8),
        (r'怎么去|路线|路程', 0.7),
        (r'往返|去程|返程', 0.7),
    ],
    IntentType.ADJUST_PLAN: [
        (r'调整|修改|改一下|换一下', 0.8),
        (r'不想去|不去|换个', 0.7),
        (r'重新规划|换个行程', 0.9),
    ],
    IntentType.RECOMMEND_FOOD: [
        (r'美食|吃|餐厅|小吃', 0.8),
        (r'推荐吃的|当地美食', 0.9),
    ],
}


def recognize_intent(text: str) -> IntentResult:
    """
    识别用户意图
    
    Args:
        text: 用户输入文本
        
    Returns:
        IntentResult: 意图识别结果
    """
    text = text.strip()
    if not text:
        return IntentResult(IntentType.UNKNOWN, 0.0, raw_input=text)
    
    scores = {intent: 0.0 for intent in IntentType}
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, text):
                scores[intent] += weight
    
    max_intent = max(scores, key=scores.get)
    max_score = scores[max_intent]
    
    if max_score < 0.5:
        max_intent = IntentType.UNKNOWN
        max_score = 0.0
    
    city = extract_city(text)
    travel_days = extract_travel_days(text)
    start_date, end_date = extract_date(text)
    departure_city = extract_departure_city(text)
    
    keywords = []
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern, _ in patterns:
            if re.search(pattern, text):
                keywords.append(pattern)
    
    return IntentResult(
        intent=max_intent,
        confidence=max_score,
        city=city,
        travel_days=travel_days,
        start_date=start_date,
        end_date=end_date,
        departure_city=departure_city,
        keywords=keywords,
        raw_input=text
    )


# ==================== 意图分类路由 ====================
def route_by_intent(intent_result: IntentResult) -> str:
    """
    根据意图结果返回路由标识
    
    Args:
        intent_result: 意图识别结果
        
    Returns:
        路由标识字符串
    """
    intent_map = {
        IntentType.GENERATE_PLAN: "generate_plan",
        IntentType.QUERY_ATTRACTIONS: "query_attractions",
        IntentType.QUERY_WEATHER: "query_weather",
        IntentType.QUERY_HOTELS: "query_hotels",
        IntentType.QUERY_TRANSPORT: "query_transport",
        IntentType.ADJUST_PLAN: "adjust_plan",
        IntentType.RECOMMEND_FOOD: "recommend_food",
        IntentType.UNKNOWN: "unknown",
    }
    return intent_map.get(intent_result.intent, "unknown")


# ==================== 意图描述 ====================
def get_intent_description(intent: IntentType) -> str:
    """获取意图描述"""
    descriptions = {
        IntentType.GENERATE_PLAN: "生成完整旅行计划",
        IntentType.QUERY_ATTRACTIONS: "查询景点信息",
        IntentType.QUERY_WEATHER: "查询天气预报",
        IntentType.QUERY_HOTELS: "查询酒店信息",
        IntentType.QUERY_TRANSPORT: "查询交通信息",
        IntentType.ADJUST_PLAN: "调整旅行计划",
        IntentType.RECOMMEND_FOOD: "推荐当地美食",
        IntentType.UNKNOWN: "未知意图",
    }
    return descriptions.get(intent, "未知意图")


# ==================== 批量测试 ====================
def test_intent_recognition():
    """测试意图识别"""
    test_cases = [
        "帮我规划北京3天的旅行",
        "北京有什么好玩的",
        "北京最近天气怎么样",
        "北京推荐住哪里",
        "从上海到北京怎么去",
        "帮我改一下行程",
        "北京有什么好吃的",
        "Hello",
        "成都5天旅游攻略",
        "从广州去深圳2天行程",
    ]
    
    print("=" * 60)
    print("意图识别测试")
    print("=" * 60)
    
    for text in test_cases:
        result = recognize_intent(text)
        print(f"输入: {text}")
        print(f"  意图: {result.intent.value} ({result.confidence:.2f})")
        print(f"  城市: {result.city}")
        print(f"  天数: {result.travel_days}")
        print(f"  日期: {result.start_date} ~ {result.end_date}")
        print(f"  出发城市: {result.departure_city}")
        print()


if __name__ == "__main__":
    test_intent_recognition()