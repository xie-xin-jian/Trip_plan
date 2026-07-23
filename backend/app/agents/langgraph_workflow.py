"""LangGraph 旅行规划 Agent - 工作流定义"""

import json
from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from .langgraph_state import TripAgentState
from .langgraph_tools import (
    search_attractions,
    get_weather_info,
    search_hotels,
    search_transportation,
    get_all_tools,
    get_tool_by_name
)
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .intent_recognition import recognize_intent, IntentType, route_by_intent, get_intent_description
from .result_validation import validate_trip_plan, generate_fix_suggestions
from .fallback_handler import handle_fallback, fallback_attractions, fallback_weather, fallback_hotels, fallback_transport, fallback_plan
from .user_feedback import (
    FeedbackRecord, FeedbackType, save_feedback, 
    get_feedback_stats
)
from .adjust_plan import adjust_plan_with_llm
from ..config import get_settings


# ==================== LLM 配置 ====================
def get_llm():
    """获取 LLM 实例"""
    settings = get_settings()
    api_key = settings.openai_api_key or settings.llm_api_key
    base_url = settings.openai_base_url or settings.llm_base_url
    
    print(f"[LLM配置] API Key: {'已配置' if api_key else '未配置'}")
    print(f"[LLM配置] Base URL: {base_url}")
    print(f"[LLM配置] Model: {settings.openai_model or 'deepseek-chat'}")
    
    return ChatOpenAI(
        model=settings.openai_model or "deepseek-chat",
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        streaming=False,
        max_retries=3,
        timeout=120
    )


# ==================== 节点函数 ====================
def intent_recognition_node(state: TripAgentState) -> TripAgentState:
    """
    意图识别节点 - 判断用户意图，决定后续流程
    """
    print("\n" + "="*60)
    print("[LangGraph] 执行意图识别节点")
    print("="*60)
    
    free_text_input = state.get("free_text_input", "")
    
    if free_text_input:
        intent_result = recognize_intent(free_text_input)
        print(f"[意图识别] 输入: {free_text_input}")
        print(f"[意图识别] 结果: {intent_result.intent.value} (置信度: {intent_result.confidence:.2f})")
        print(f"[意图识别] 提取城市: {intent_result.city}")
        print(f"[意图识别] 提取天数: {intent_result.travel_days}")
        
        # 如果意图识别提取到了城市，覆盖原有的城市
        if intent_result.city:
            state["city"] = intent_result.city
        if intent_result.travel_days:
            state["travel_days"] = intent_result.travel_days
        
        return {
            **state,
            "intent": intent_result.intent.value,
            "intent_confidence": intent_result.confidence,
            "intent_city": intent_result.city,
            "intent_days": intent_result.travel_days
        }
    else:
        return {
            **state,
            "intent": IntentType.GENERATE_PLAN.value,
            "intent_confidence": 1.0,
            "intent_city": None,
            "intent_days": None
        }


def should_continue(state: TripAgentState) -> Literal["search_tools", "generate_plan", "end"]:
    """根据意图决定下一步"""
    intent = state.get("intent", IntentType.GENERATE_PLAN.value)
    
    if intent == IntentType.GENERATE_PLAN.value:
        if not state.get("attractions"):
            return "search_tools"
        return "generate_plan"
    elif intent in [IntentType.QUERY_ATTRACTIONS.value, IntentType.QUERY_WEATHER.value, 
                    IntentType.QUERY_HOTELS.value, IntentType.QUERY_TRANSPORT.value]:
        return "search_tools"
    elif intent == IntentType.ADJUST_PLAN.value:
        return "generate_plan"
    else:
        return "end"


def search_tools_node(state: TripAgentState) -> TripAgentState:
    """
    搜索工具节点 - 收集景点、天气、酒店等信息
    """
    print("\n" + "="*60)
    print("[LangGraph] 执行搜索节点")
    print("="*60)
    
    city = state["city"]
    travel_days = state["travel_days"]
    start_date = state["start_date"]
    departure_city = state.get("departure_city")
    accommodation = state.get("accommodation", "舒适型")
    
    results = {}
    fallback_used = []
    
    # 1. 搜索景点
    print("[1/4] 搜索景点...")
    try:
        attractions_result = search_attractions.invoke({
            "city": city,
            "travel_days": travel_days
        })
        # 检查是否返回了有效数据
        parsed_attractions = json.loads(attractions_result) if attractions_result else []
        if not parsed_attractions or len(parsed_attractions) == 0:
            raise ValueError("API返回空数据")
        results["attractions"] = attractions_result
    except Exception as e:
        print(f"[警告] 景点搜索失败: {e}, 触发兜底")
        fb_result = handle_fallback(e, {
            "operation": "attractions",
            "city": city,
            "travel_days": travel_days
        })
        results["attractions"] = json.dumps(fb_result.data, ensure_ascii=False)
        fallback_used.append({"operation": "attractions", "level": fb_result.level, "message": fb_result.message})
    
    # 2. 获取天气
    print("[2/4] 获取天气...")
    try:
        weather_result = get_weather_info.invoke({
            "city": city,
            "travel_days": travel_days,
            "start_date": start_date
        })
        parsed_weather = json.loads(weather_result) if weather_result else []
        if not parsed_weather or len(parsed_weather) == 0:
            raise ValueError("API返回空数据")
        results["weather"] = weather_result
    except Exception as e:
        print(f"[警告] 天气获取失败: {e}, 触发兜底")
        fb_result = handle_fallback(e, {
            "operation": "weather",
            "city": city,
            "travel_days": travel_days,
            "start_date": start_date
        })
        results["weather"] = json.dumps(fb_result.data, ensure_ascii=False)
        fallback_used.append({"operation": "weather", "level": fb_result.level, "message": fb_result.message})
    
    # 3. 搜索酒店
    print("[3/4] 搜索酒店...")
    try:
        hotels_result = search_hotels.invoke({
            "city": city,
            "travel_days": travel_days,
            "accommodation": accommodation
        })
        parsed_hotels = json.loads(hotels_result) if hotels_result else []
        if not parsed_hotels or len(parsed_hotels) == 0:
            raise ValueError("API返回空数据")
        results["hotels"] = hotels_result
    except Exception as e:
        print(f"[警告] 酒店搜索失败: {e}, 触发兜底")
        fb_result = handle_fallback(e, {
            "operation": "hotels",
            "city": city,
            "accommodation": accommodation
        })
        results["hotels"] = json.dumps(fb_result.data, ensure_ascii=False)
        fallback_used.append({"operation": "hotels", "level": fb_result.level, "message": fb_result.message})
    
    # 4. 搜索交通（如果有出发城市）
    if departure_city:
        print("[4/4] 搜索往返交通...")
        try:
            transport_result = search_transportation.invoke({
                "departure_city": departure_city,
                "destination_city": city,
                "travel_days": travel_days,
                "transport_type": state.get("preferred_transport_type", "all")
            })
            transport_data = json.loads(transport_result)
            if not transport_data.get("outbound"):
                raise ValueError("API返回空数据")
            results["outbound_transport"] = transport_data.get("outbound", [])
            results["return_transport"] = transport_data.get("return_trip", [])
        except Exception as e:
            print(f"[警告] 交通搜索失败: {e}, 触发兜底")
            fb_result = handle_fallback(e, {
                "operation": "transport",
                "departure_city": departure_city,
                "destination_city": city
            })
            results["outbound_transport"] = fb_result.data.get("outbound", [])
            results["return_transport"] = fb_result.data.get("return_trip", [])
            fallback_used.append({"operation": "transport", "level": fb_result.level, "message": fb_result.message})
    else:
        results["outbound_transport"] = []
        results["return_transport"] = []
    
    print(f"[完成] 收集到: 景点{len(json.loads(results['attractions']))}个, "
          f"酒店{len(json.loads(results['hotels']))}家, "
          f"天气{len(json.loads(results['weather']))}天")
    
    if fallback_used:
        print(f"[兜底] 触发{len(fallback_used)}个兜底:")
        for fb in fallback_used:
            print(f"  - {fb['operation']}: {fb['level']}")
    
    return {
        **state,
        **results,
        "retry_count": state.get("retry_count", 0)
    }


def generate_plan_node(state: TripAgentState) -> TripAgentState:
    """
    生成计划节点 - 使用 LLM 生成完整的旅行计划
    """
    print("\n" + "="*60)
    print("[LangGraph] 执行生成节点")
    print("="*60)
    
    llm = get_llm()
    
    # 准备工具结果
    attractions = state.get("attractions", "[]")
    hotels = state.get("hotels", "[]")
    weather = state.get("weather", "[]")
    
    # 使用优化后的 prompt
    user_prompt = build_user_prompt(
        city=state['city'],
        travel_days=state['travel_days'],
        start_date=state['start_date'],
        end_date=state['end_date'],
        attractions=attractions,
        hotels=hotels,
        weather=weather,
        transportation=state.get('transportation', '地铁/公交'),
        accommodation=state.get('accommodation', '舒适型'),
        preferences=state.get('preferences', []),
        free_text_input=state.get('free_text_input'),
        departure_city=state.get('departure_city')
    )
    
    try:
        # 调用 LLM（使用优化后的系统提示词）
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ])
        
        print(f"[LLM] 生成了 {len(str(response.content))} 字符的计划")
        
        # 提取 JSON
        plan = _extract_json(str(response.content))
        
        if plan:
            # 如果有往返交通，添加到计划中
            if state.get("outbound_transport") and state.get("return_transport"):
                plan["round_trip_transportation"] = {
                    "departure_city": state["departure_city"],
                    "destination_city": state["city"],
                    "outbound": state["outbound_transport"],
                    "return_trip": state["return_transport"],
                    "total_transport_budget": sum(
                        t.get("price_economy", 0) for t in state["outbound_transport"] + state["return_transport"]
                    ) // 2 if state["outbound_transport"] and state["return_transport"] else 0
                }
            
            print(f"[成功] 生成 {len(plan.get('days', []))} 天行程")
            return {
                **state,
                "generated_plan": plan,
                "error": None
            }
        else:
            print("[失败] 无法提取JSON")
            return {
                **state,
                "error": "无法生成有效的旅行计划",
                "retry_count": state.get("retry_count", 0) + 1
            }
            
    except Exception as e:
        print(f"[错误] 生成计划失败: {e}, 触发兜底")
        # 触发计划兜底
        fb_result = handle_fallback(e, {
            "operation": "plan",
            "city": state['city'],
            "travel_days": state['travel_days'],
            "start_date": state['start_date'],
            "end_date": state['end_date']
        })
        return {
            **state,
            "generated_plan": fb_result.data,
            "error": str(e),
            "fallback_used": True,
            "fallback_level": fb_result.level,
            "fallback_message": fb_result.message,
            "retry_count": state.get("retry_count", 0) + 1
        }


def validate_plan_node(state: TripAgentState) -> TripAgentState:
    """
    结果校验节点 - 校验生成的旅行计划是否合法
    """
    print("\n" + "="*60)
    print("[LangGraph] 执行结果校验节点")
    print("="*60)
    
    plan = state.get("generated_plan")
    
    if not plan:
        print("[校验] 没有生成计划，跳过校验")
        return {
            **state,
            "validation_result": None,
            "validation_score": 0.0
        }
    
    # 解析原始数据用于真实性校验
    attractions_data = []
    hotels_data = []
    
    try:
        attractions_str = state.get("attractions", "[]")
        attractions_data = json.loads(attractions_str)
    except:
        pass
    
    try:
        hotels_str = state.get("hotels", "[]")
        hotels_data = json.loads(hotels_str)
    except:
        pass
    
    # 执行综合校验
    validation_result = validate_trip_plan(
        plan=plan,
        expected_days=state["travel_days"],
        expected_city=state["city"],
        attractions_data=attractions_data,
        hotels_data=hotels_data
    )
    
    # 生成修复建议
    suggestions = generate_fix_suggestions(validation_result)
    
    print(f"[校验] 结果: 有效={validation_result.is_valid}, 分数={validation_result.score:.2f}")
    if suggestions:
        print(f"[校验] 修复建议: {suggestions}")
    
    return {
        **state,
        "validation_result": validation_result.to_dict(),
        "validation_score": validation_result.score,
        "validation_is_valid": validation_result.is_valid,
        "validation_errors": validation_result.errors,
        "validation_warnings": validation_result.warnings,
        "fix_suggestions": suggestions
    }


def should_retry(state: TripAgentState) -> Literal["generate_plan", "end"]:
    """判断是否需要重试生成"""
    retry_count = state.get("retry_count", 0)
    validation_is_valid = state.get("validation_is_valid", True)
    error = state.get("error")
    
    if error and retry_count < 3:
        print(f"[重试] 第 {retry_count + 1} 次重试")
        return "generate_plan"
    
    if not validation_is_valid and retry_count < 3:
        print(f"[重试] 校验失败，第 {retry_count + 1} 次重试")
        return "generate_plan"
    
    return "end"


def feedback_node(state: TripAgentState) -> TripAgentState:
    """
    用户反馈处理节点 - 使用 LLM 处理用户对生成计划的反馈
    """
    print("\n" + "="*60)
    print("[LangGraph] 执行用户反馈节点（LLM驱动）")
    print("="*60)
    
    plan = state.get("generated_plan")
    free_text_input = state.get("free_text_input", "")
    
    # 如果没有反馈或计划，直接返回
    if not free_text_input or not plan:
        stats = get_feedback_stats()
        return {
            **state,
            "feedback_stats": stats
        }
    
    # 判断是否为调整请求（包含调整相关的关键词）
    adjust_keywords = [
        "换", "改", "调整", "去掉", "删除", "增加", "加", "减少", "删除",
        "太赶", "太松", "放松", "紧凑", "预算", "优化", "重新"
    ]
    
    is_adjust_request = any(kw in free_text_input for kw in adjust_keywords)
    
    # 记录反馈
    feedback_type = FeedbackType.ADJUST_REQUEST.value if is_adjust_request else FeedbackType.COMMENT.value
    feedback = FeedbackRecord(
        feedback_id=f"fb_{int(datetime.now().timestamp() * 1000)}",
        plan_id=state.get("plan_id", "unknown"),
        user_id=state.get("user_id"),
        feedback_type=feedback_type,
        adjust_type="llm_adjustment" if is_adjust_request else None,
        comment=free_text_input
    )
    save_feedback(feedback)
    
    if is_adjust_request:
        # 使用 LLM 进行计划调整
        print(f"[反馈] 识别为调整请求，调用 LLM 处理")
        print(f"[反馈] 用户反馈: {free_text_input}")
        
        # 获取原始数据
        attractions = state.get("attractions", "[]")
        hotels = state.get("hotels", "[]")
        
        # 调用 LLM 调整
        result = adjust_plan_with_llm_sync(
            original_plan=plan,
            feedback=free_text_input,
            attractions=attractions if isinstance(attractions, str) else json.dumps(attractions),
            hotels=hotels if isinstance(hotels, str) else json.dumps(hotels)
        )
        
        if result["success"]:
            print(f"[反馈] LLM 调整成功，尝试次数: {result['adjustment_count']}")
            return {
                **state,
                "generated_plan": result["plan"],
                "feedback_applied": True,
                "feedback_adjust_type": "llm_adjustment",
                "feedback_adjust_count": result["adjustment_count"],
                "feedback_used_fallback": result["used_fallback"],
                "adjustment_successful": True
            }
        else:
            print(f"[反馈] LLM 调整失败: {result['error']}")
            return {
                **state,
                "generated_plan": result["plan"],
                "feedback_applied": False,
                "feedback_error": result["error"],
                "adjustment_successful": False
            }
    else:
        # 非调整请求，记录为评论
        print(f"[反馈] 记录为用户评论")
        stats = get_feedback_stats()
        return {
            **state,
            "feedback_stats": stats,
            "feedback_comment": free_text_input
        }


# ==================== JSON 提取辅助 ====================
def _extract_json(text: str) -> dict:
    """从文本中提取 JSON"""
    # 尝试从代码块中提取
    if "```json" in text:
        s = text.find("```json") + 7
        e = text.find("```", s)
        if e > s:
            text = text[s:e].strip()
    elif "```" in text:
        s = text.find("```") + 3
        e = text.find("```", s)
        if e > s:
            text = text[s:e].strip()
    
    # 尝试找到 JSON 对象
    s = text.find("{")
    e = text.rfind("}")
    if s >= 0 and e > s:
        text = text[s:e + 1]
        
        # 清理并解析
        try:
            import re
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    return None


# ==================== 创建图 ====================
def create_trip_planner_graph():
    """
    创建旅行规划图
    
    工作流程：
    1. intent_recognition -> 识别用户意图
    2. search_tools -> 收集景点、天气、酒店、交通（带失败兜底）
    3. generate_plan -> 使用 LLM 生成完整计划（带失败兜底）
    4. validate_plan -> 校验生成的计划是否合法
    5. should_retry -> 判断是否需要重试
    6. feedback -> 处理用户反馈
    7. END -> 返回结果
    """
    print("\n[LangGraph] 创建旅行规划图...")
    
    # 创建图
    graph = StateGraph(TripAgentState)
    
    # 添加节点
    graph.add_node("intent_recognition", intent_recognition_node)
    graph.add_node("search_tools", search_tools_node)
    graph.add_node("generate_plan", generate_plan_node)
    graph.add_node("validate_plan", validate_plan_node)
    graph.add_node("feedback", feedback_node)
    
    # 设置入口点
    graph.set_entry_point("intent_recognition")
    
    # 添加边
    graph.add_edge("intent_recognition", "search_tools")
    graph.add_edge("search_tools", "generate_plan")
    graph.add_edge("generate_plan", "validate_plan")
    graph.add_conditional_edges("validate_plan", should_retry, {
        "generate_plan": "generate_plan",
        "end": "feedback"
    })
    graph.add_edge("feedback", END)
    
    # 编译图
    compiled = graph.compile()
    
    print("[LangGraph] 图创建完成")
    return compiled


# ==================== 预编译实例 ====================
_trip_graph = None


def get_trip_planner_graph():
    """获取旅行规划图实例（单例）"""
    global _trip_graph
    if _trip_graph is None:
        _trip_graph = create_trip_planner_graph()
    return _trip_graph


# ==================== 执行函数 ====================
async def run_trip_planner(
    city: str,
    travel_days: int,
    start_date: str,
    end_date: str,
    departure_city: str = None,
    preferred_transport_type: str = "all",
    transportation: str = "地铁/公交",
    accommodation: str = "舒适型",
    preferences: list = None,
    free_text_input: str = None
):
    """
    运行旅行规划 Agent
    
    Args:
        city: 目的地城市
        travel_days: 旅行天数
        start_date: 开始日期
        end_date: 结束日期
        departure_city: 出发城市（可选）
        preferred_transport_type: 交通偏好
        transportation: 市内交通方式
        accommodation: 住宿偏好
        preferences: 用户偏好列表
        free_text_input: 用户额外输入
        
    Returns:
        生成的旅行计划 dict
    """
    print(f"\n{'='*60}")
    print(f"[LangGraph] 开始规划: {city}, {travel_days}天")
    print(f"{'='*60}")
    
    # 初始化状态
    initial_state: TripAgentState = {
        "city": city,
        "travel_days": travel_days,
        "start_date": start_date,
        "end_date": end_date,
        "departure_city": departure_city,
        "preferred_transport_type": preferred_transport_type,
        "transportation": transportation,
        "accommodation": accommodation,
        "preferences": preferences or [],
        "free_text_input": free_text_input,
        "attractions": None,
        "hotels": None,
        "weather": None,
        "outbound_transport": None,
        "return_transport": None,
        "generated_plan": None,
        "error": None,
        "retry_count": 0,
        "messages": [],
        "intent": None,
        "intent_confidence": None,
        "intent_city": None,
        "intent_days": None,
        "validation_result": None,
        "validation_score": None,
        "validation_is_valid": None,
        "validation_errors": None,
        "validation_warnings": None,
        "fix_suggestions": None,
        "feedback_applied": None,
        "feedback_adjust_type": None,
        "feedback_adjust_count": None,
        "feedback_used_fallback": None,
        "feedback_error": None,
        "feedback_comment": None,
        "adjustment_successful": None
    }
    
    # 运行图
    graph = get_trip_planner_graph()
    result = await graph.ainvoke(initial_state)
    
    # 返回生成的计划（包含校验信息）
    if result.get("generated_plan"):
        print(f"\n[成功] 旅行规划完成！")
        
        # 在结果中添加校验信息
        plan = result["generated_plan"]
        if result.get("validation_result"):
            plan["_validation"] = {
                "score": result.get("validation_score"),
                "is_valid": result.get("validation_is_valid"),
                "errors": result.get("validation_errors"),
                "warnings": result.get("validation_warnings"),
                "suggestions": result.get("fix_suggestions")
            }
        
        # 在结果中添加反馈信息
        if result.get("feedback_applied") is not None:
            plan["_feedback"] = {
                "applied": result.get("feedback_applied"),
                "adjust_type": result.get("feedback_adjust_type"),
                "adjust_count": result.get("feedback_adjust_count"),
                "used_fallback": result.get("feedback_used_fallback"),
                "adjustment_successful": result.get("adjustment_successful"),
                "error": result.get("feedback_error")
            }
        
        return plan
    else:
        print(f"\n[失败] {result.get('error', '未知错误')}")
        return {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "days": [],
            "error": result.get("error", "生成失败"),
            "_validation": {
                "score": 0.0,
                "is_valid": False,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
        }