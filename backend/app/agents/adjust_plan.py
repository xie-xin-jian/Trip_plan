"""LLM驱动的计划调整模块 - LLM-based Plan Adjustment"""

import json
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .prompts import ADJUST_SYSTEM_PROMPT, ADJUST_USER_PROMPT_TEMPLATE
from .fallback_handler import fallback_plan
from ..config import get_settings


def get_llm():
    """获取 LLM 实例"""
    settings = get_settings()
    api_key = settings.openai_api_key or settings.llm_api_key
    base_url = settings.openai_base_url or settings.llm_base_url
    
    return ChatOpenAI(
        model=settings.openai_model or "deepseek-chat",
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        streaming=False
    )


def _extract_json(text: str) -> Optional[dict]:
    """从文本中提取 JSON"""
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
    
    s = text.find("{")
    e = text.rfind("}")
    if s >= 0 and e > s:
        text = text[s:e + 1]
        try:
            import re
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


async def adjust_plan_with_llm(
    original_plan: dict,
    feedback: str,
    attractions: str = "[]",
    hotels: str = "[]",
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    使用 LLM 根据用户反馈调整旅行计划
    
    Args:
        original_plan: 原始旅行计划
        feedback: 用户反馈文本
        attractions: 景点数据JSON字符串
        hotels: 酒店数据JSON字符串
        max_retries: 最大重试次数
        
    Returns:
        调整后的计划，包含以下字段：
        - success: 是否成功
        - plan: 调整后的计划（成功时）
        - error: 错误信息（失败时）
        - used_fallback: 是否使用了兜底
        - adjustment_count: 调整次数
    """
    print("\n" + "="*60)
    print("[LLM调整] 开始 LLM 驱动的计划调整")
    print("="*60)
    print(f"[LLM调整] 用户反馈: {feedback}")
    
    llm = get_llm()
    
    # 构建提示词
    system_prompt = ADJUST_SYSTEM_PROMPT
    user_prompt = ADJUST_USER_PROMPT_TEMPLATE.format(
        original_plan=json.dumps(original_plan, ensure_ascii=False, indent=2),
        feedback=feedback,
        attractions=attractions if attractions else "[]",
        hotels=hotels if hotels else "[]"
    )
    
    for attempt in range(max_retries):
        try:
            print(f"[LLM调整] 第 {attempt + 1} 次尝试...")
            
            # 调用 LLM
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            content = str(response.content)
            print(f"[LLM调整] LLM 返回了 {len(content)} 字符")
            
            # 提取 JSON
            adjusted_plan = _extract_json(content)
            
            if adjusted_plan:
                print(f"[LLM调整] 成功提取调整后的计划")
                
                # 标记为调整版本
                adjusted_plan["_adjusted"] = True
                adjusted_plan["_original_plan_id"] = original_plan.get("id") or original_plan.get("city")
                adjusted_plan["_adjustment_feedback"] = feedback
                
                return {
                    "success": True,
                    "plan": adjusted_plan,
                    "error": None,
                    "used_fallback": False,
                    "adjustment_count": attempt + 1
                }
            else:
                print(f"[LLM调整] 无法从响应中提取JSON")
                if attempt < max_retries - 1:
                    print(f"[LLM调整] 重试...")
                    continue
                    
        except Exception as e:
            print(f"[LLM调整] 第 {attempt + 1} 次尝试失败: {e}")
            if attempt < max_retries - 1:
                print(f"[LLM调整] 重试...")
                continue
    
    # 所有重试都失败了，触发兜底
    print(f"[LLM调整] LLM 调整失败，触发兜底")
    
    fb_result = fallback_plan(
        city=original_plan.get("city", ""),
        travel_days=original_plan.get("days", [[]]).__len__(),
        start_date=original_plan.get("start_date", ""),
        end_date=original_plan.get("end_date", ""),
        reason=f"LLM调整失败: {feedback}"
    )
    
    return {
        "success": False,
        "plan": fb_result.data,
        "error": f"LLM调整失败，已使用兜底",
        "used_fallback": True,
        "adjustment_count": max_retries
    }


# ==================== 同步版本（用于非异步场景）====================
def adjust_plan_with_llm_sync(
    original_plan: dict,
    feedback: str,
    attractions: str = "[]",
    hotels: str = "[]",
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    同步版本的 LLM 计划调整
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已经在事件循环中，创建一个新的
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    adjust_plan_with_llm(
                        original_plan, feedback, attractions, hotels, max_retries
                    )
                )
                return future.result()
        else:
            return loop.run_until_complete(
                adjust_plan_with_llm(
                    original_plan, feedback, attractions, hotels, max_retries
                )
            )
    except RuntimeError:
        # 没有事件循环，创建一个新的
        return asyncio.run(
            adjust_plan_with_llm(
                original_plan, feedback, attractions, hotels, max_retries
            )
        )


# ==================== 测试 ====================
async def test_adjust():
    """测试 LLM 驱动的计划调整"""
    print("=" * 60)
    print("LLM 计划调整测试")
    print("=" * 60)
    
    test_plan = {
        "city": "北京",
        "start_date": "2024-05-01",
        "end_date": "2024-05-03",
        "days": [
            {
                "day_index": 0,
                "description": "第一天：故宫-天安门",
                "attractions": [
                    {"name": "故宫博物院", "visit_duration": 180},
                    {"name": "天安门广场", "visit_duration": 60}
                ]
            },
            {
                "day_index": 1,
                "description": "第二天：长城",
                "attractions": [
                    {"name": "八达岭长城", "visit_duration": 240}
                ]
            }
        ],
        "budget": {"total": 2000}
    }
    
    test_cases = [
        "第一天太赶了，减少一个景点",
        "把第二天的长城去掉，换成更适合孩子的景点",
        "预算减少500元",
        "行程太赶，放松一点",
        "帮我看看有什么问题，优化一下"
    ]
    
    for feedback in test_cases:
        print(f"\n测试反馈: {feedback}")
        result = await adjust_plan_with_llm(
            original_plan=test_plan,
            feedback=feedback,
            attractions="[{\"name\": \"北京海洋馆\"}, {\"name\": \"颐和园\"}]",
            hotels="[]"
        )
        print(f"结果: success={result['success']}, fallback={result['used_fallback']}")


if __name__ == "__main__":
    asyncio.run(test_adjust())