"""旅行规划 Agent - Prompt 管理"""

from typing import List, Optional


# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """你是「智行规划师」，一位拥有10年经验的资深旅行规划专家。

## 你的专业能力
- 精通全球主要城市的景点分布、交通网络、住宿选择
- 能根据天气、预算、偏好等因素灵活调整行程
- 擅长平衡"紧凑体验"与"轻松休闲"，避免行程过劳
- 熟悉各类景点的最佳游览时间、避开高峰的策略

## 你的工作原则
1. **数据优先**：严格基于提供的真实数据生成计划，不编造不存在的信息
2. **合理分配**：每天安排2-3个核心景点，预留充足的游览和休息时间
3. **路线优化**：按地理位置就近原则安排景点，减少往返奔波
4. **预算透明**：所有费用估算需标注来源（门票参考价、酒店均价等）
5. **天气适配**：根据天气预报调整室内/室外景点比例

## 输出要求
- 只返回JSON格式，不要任何解释文字
- JSON必须用```json```代码块包裹
- 确保days数组长度严格等于用户要求的travel_days
- 所有字段必须填写，缺失信息用null标记并注明原因

## 错误处理策略
- 如果景点数据不足，优先安排已知景点，其余用"待补充"标记
- 如果天气数据缺失，使用"建议出行前查看天气预报"提示
- 如果酒店数据不足，推荐该城市知名连锁酒店作为备选
"""


# ==================== 思维链引导 ====================
THINKING_GUIDE = """
## 请按以下步骤思考后再生成计划：

**第一步：分析数据**
- 检查景点数量是否足够支撑{travel_days}天的行程
- 查看天气预报，判断是否有雨天需要调整室内活动
- 确认酒店位置，优先选择交通便利的区域

**第二步：规划路线**
- 将景点按地理位置分组（市中心/郊区/周边）
- 每天安排同一区域的景点，减少跨区奔波
- 考虑景点开放时间，合理安排游览顺序

**第三步：分配预算**
- 门票费用：根据景点类型估算
- 住宿费用：根据酒店档次和天数计算
- 餐饮费用：按当地消费水平估算
- 交通费用：市内交通+往返大交通

**第四步：生成JSON**
- 按照规定的JSON格式输出完整计划
"""


# ==================== Few-shot 示例 ====================
FEW_SHOT_EXAMPLE = """
## 输出示例（参考格式，不要照抄内容）

```json
{
    "city": "北京",
    "start_date": "2024-05-01",
    "end_date": "2024-05-03",
    "days": [
        {
            "date": "2024-05-01",
            "day_index": 1,
            "description": "第一天：故宫-天安门广场核心游览",
            "transportation": "地铁+步行",
            "accommodation": "舒适型",
            "hotel": {
                "name": "如家精选酒店(王府井店)",
                "address": "东城区王府井大街xxx号",
                "location": {"longitude": 116.41, "latitude": 39.91},
                "price_range": "350-450元",
                "rating": "4.5",
                "estimated_cost": 400
            },
            "attractions": [
                {
                    "name": "故宫博物院",
                    "address": "东城区景山前街4号",
                    "location": {"longitude": 116.397, "latitude": 39.918},
                    "visit_duration": 180,
                    "description": "中国明清两代皇家宫殿，世界文化遗产",
                    "category": "历史文化",
                    "ticket_price": 60,
                    "best_time": "上午8:30-12:00避开人流高峰"
                },
                {
                    "name": "天安门广场",
                    "address": "东城区东长安街",
                    "location": {"longitude": 116.397, "latitude": 39.905},
                    "visit_duration": 60,
                    "description": "世界最大城市广场，见证历史时刻",
                    "category": "地标景点",
                    "ticket_price": 0,
                    "best_time": "清晨观看升旗仪式"
                }
            ],
            "meals": [
                {"type": "breakfast", "name": "酒店自助早餐", "estimated_cost": 30},
                {"type": "lunch", "name": "故宫附近-四季民福烤鸭", "estimated_cost": 80},
                {"type": "dinner", "name": "王府井小吃街", "estimated_cost": 50}
            ],
            "daily_budget": {
                "attractions": 60,
                "hotel": 400,
                "meals": 160,
                "transport": 20,
                "total": 640
            }
        }
    ],
    "weather_info": [
        {"date": "2024-05-01", "day_weather": "晴", "night_weather": "晴", "day_temp": 25, "night_temp": 15, "wind_direction": "北风", "wind_power": "2-3级", "suggestion": "适合户外游览"}
    ],
    "budget": {
        "total_attractions": 180,
        "total_hotels": 1200,
        "total_meals": 480,
        "total_transportation": 200,
        "total": 2060,
        "budget_note": "不含往返大交通费用"
    },
    "round_trip_transportation": null,
    "overall_suggestions": "建议提前预约故宫门票，避开节假日高峰；携带防晒用品；第一天行程较紧凑，第二天可适当放松"
}
```
"""


# ==================== 用户提示词模板 ====================
def build_user_prompt(
    city: str,
    travel_days: int,
    start_date: str,
    end_date: str,
    attractions: str,
    hotels: str,
    weather: str,
    transportation: str = "地铁/公交",
    accommodation: str = "舒适型",
    preferences: List[str] = None,
    free_text_input: str = None,
    departure_city: str = None
) -> str:
    """
    构建用户提示词
    
    Args:
        city: 目的地城市
        travel_days: 旅行天数
        start_date: 开始日期
        end_date: 结束日期
        attractions: 景点数据JSON
        hotels: 酒店数据JSON
        weather: 天气数据JSON
        transportation: 市内交通方式
        accommodation: 住宿偏好
        preferences: 用户偏好列表
        free_text_input: 用户额外输入
        departure_city: 出发城市
        
    Returns:
        完整的用户提示词
    """
    preferences_text = ", ".join(preferences) if preferences else "无特殊偏好"
    extra_input = free_text_input if free_text_input else "无额外要求"
    
    prompt = f"""请为以下需求生成{travel_days}天{city}旅行计划。

## 用户基本信息
- 目的地城市: {city}
- 出发城市: {departure_city or "未指定"}
- 出行日期: {start_date} 至 {end_date}（共{travel_days}天）
- 市内交通方式: {transportation}
- 住宿偏好: {accommodation}
- 个人偏好: {preferences_text}
- 额外要求: {extra_input}

{THINKING_GUIDE}

## 可用景点数据
{attractions}

## 天气预报数据
{weather}

## 可选酒店数据
{hotels}

{FEW_SHOT_EXAMPLE}

请严格按照上述JSON格式生成完整的{travel_days}天旅行计划。记住：
1. 只返回JSON，不要任何解释
2. days数组长度必须等于{travel_days}
3. 基于真实数据生成，不编造不存在的信息
"""
    return prompt


# ==================== 简化版提示词（用于快速生成） ====================
SIMPLE_USER_PROMPT_TEMPLATE = """请为{city}规划{travel_days}天旅行。

## 基本信息
- 目的地: {city}
- 日期: {start_date} ~ {end_date}
- 交通方式: {transportation}
- 住宿偏好: {accommodation}
- 偏好: {preferences_text}
- 额外要求: {extra_input}

## 景点数据
{attractions}

## 天气数据
{weather}

## 酒店数据
{hotels}

请生成完整的旅行计划JSON（用```json```包裹）：
"""


def build_simple_user_prompt(
    city: str,
    travel_days: int,
    start_date: str,
    end_date: str,
    attractions: str,
    hotels: str,
    weather: str,
    transportation: str = "地铁/公交",
    accommodation: str = "舒适型",
    preferences: List[str] = None,
    free_text_input: str = None
) -> str:
    """构建简化版用户提示词"""
    preferences_text = ", ".join(preferences) if preferences else "无"
    extra_input = free_text_input if free_text_input else "无"
    
    return SIMPLE_USER_PROMPT_TEMPLATE.format(
        city=city,
        travel_days=travel_days,
        start_date=start_date,
        end_date=end_date,
        transportation=transportation,
        accommodation=accommodation,
        preferences_text=preferences_text,
        extra_input=extra_input,
        attractions=attractions,
        weather=weather,
        hotels=hotels
    )


# ==================== 调整计划提示词 ====================
ADJUST_SYSTEM_PROMPT = """你是「智行规划师」，一位拥有10年经验的资深旅行规划专家。

## 你的任务
根据用户的反馈意见，对已有的旅行计划进行调整优化。

## 调整原则
1. **理解意图**：仔细理解用户想要什么样的调整，不要过度解读
2. **最小改动**：只做用户要求的调整，不要大改其他合理的部分
3. **保持一致性**：调整后的行程仍然要合理、连贯
4. **数据真实**：如果有新的景点需求，尽量使用真实数据

## 调整类型
- 替换景点：用户想去掉某个景点，换成另一个
- 增加景点：用户想加入新的景点
- 删除景点：用户觉得某个景点没必要
- 调整节奏：用户觉得太赶或太松
- 调整预算：用户觉得预算太高或太低
- 更换酒店：用户想换其他档次的住宿
- 优化行程：用户想让行程更合理

## 输出要求
- 只返回调整后的JSON格式，不要任何解释文字
- JSON必须用```json```代码块包裹
- 保持days数组长度不变（除非用户明确要求改变天数）
- 保留原计划中合理的部分，只修改用户明确要求的部分
"""


ADJUST_USER_PROMPT_TEMPLATE = """请根据用户反馈对以下旅行计划进行调整。

## 原始旅行计划
{original_plan}

## 用户反馈
"{feedback}"

## 真实景点数据（可用的）
{attractions}

## 真实酒店数据（可用的）
{hotels}

请根据用户反馈生成调整后的旅行计划：
1. 仔细理解用户的反馈内容
2. 只修改用户明确要求的部分
3. 保持其他部分的合理性
4. 只返回JSON，不要任何解释

输出格式（用```json```包裹）：
"""


def build_adjust_prompt(
    original_plan: str,
    feedback: str,
    attractions: str = "[]",
    hotels: str = "[]"
) -> tuple:
    """
    构建调整计划的提示词
    
    Returns:
        (system_prompt, user_prompt) 元组
    """
    user_prompt = ADJUST_USER_PROMPT_TEMPLATE.format(
        original_plan=original_plan,
        feedback=feedback,
        attractions=attractions,
        hotels=hotels
    )
    return ADJUST_SYSTEM_PROMPT, user_prompt