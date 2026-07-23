"""LangGraph 旅行规划 Agent - 状态定义"""

from typing import TypedDict, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class TripRequestState(TypedDict):
    """旅行规划的输入状态"""
    city: str
    travel_days: int
    start_date: str
    end_date: str
    departure_city: Optional[str] = None
    preferred_transport_type: Optional[str] = "all"
    transportation: str = "地铁/公交"
    accommodation: str = "舒适型"
    preferences: List[str] = Field(default_factory=list)
    free_text_input: Optional[str] = None


class TripAgentState(TypedDict):
    """LangGraph Agent 的完整状态"""
    # 用户输入
    city: str
    travel_days: int
    start_date: str
    end_date: str
    departure_city: Optional[str]
    preferred_transport_type: Optional[str]
    transportation: str
    accommodation: str
    preferences: List[str]
    free_text_input: Optional[str]
    
    # 意图识别结果
    intent: Optional[str]
    intent_confidence: Optional[float]
    intent_city: Optional[str]
    intent_days: Optional[int]
    
    # 中间状态 - 工具调用结果
    attractions: Optional[List[dict]]
    hotels: Optional[List[dict]]
    weather: Optional[List[dict]]
    outbound_transport: Optional[List[dict]]
    return_transport: Optional[List[dict]]
    
    # 最终输出
    generated_plan: Optional[dict]
    error: Optional[str]
    retry_count: int
    
    # 结果校验
    validation_result: Optional[dict]
    validation_score: Optional[float]
    validation_is_valid: Optional[bool]
    validation_errors: Optional[List[dict]]
    validation_warnings: Optional[List[dict]]
    fix_suggestions: Optional[List[str]]
    
    # 用户反馈（LLM驱动）
    feedback_applied: Optional[bool]
    feedback_adjust_type: Optional[str]
    feedback_adjust_count: Optional[int]
    feedback_used_fallback: Optional[bool]
    feedback_error: Optional[str]
    feedback_comment: Optional[str]
    adjustment_successful: Optional[bool]
    
    # LLM上下文
    messages: List[dict]


class PlanDayDetail(TypedDict):
    """每日计划详情"""
    date: str
    day_index: int
    description: str
    attractions: List[dict]
    meals: List[dict]
    hotel: Optional[dict]
    transportation: str


class FinalTripPlan(TypedDict):
    """最终旅行计划"""
    city: str
    start_date: str
    end_date: str
    days: List[PlanDayDetail]
    weather_info: List[dict]
    round_trip_transportation: Optional[dict]
    budget: dict
    overall_suggestions: str
