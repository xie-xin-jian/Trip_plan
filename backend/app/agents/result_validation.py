"""结果校验模块 - Result Validation"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import re


class ValidationResult:
    """校验结果"""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.score = 100.0
    
    def add_error(self, code: str, message: str, field: str = None):
        """添加错误"""
        self.is_valid = False
        error = {"code": code, "message": message, "field": field}
        self.errors.append(error)
        self.score -= 10
    
    def add_warning(self, code: str, message: str, field: str = None):
        """添加警告"""
        warning = {"code": code, "message": message, "field": field}
        self.warnings.append(warning)
        self.score -= 2
    
    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "score": round(self.score, 2),
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def __repr__(self):
        return f"ValidationResult(is_valid={self.is_valid}, score={self.score:.2f}, errors={len(self.errors)}, warnings={len(self.warnings)})"


# ==================== JSON 格式校验 ====================
def validate_json_format(data: str) -> ValidationResult:
    """校验JSON格式"""
    result = ValidationResult()
    
    try:
        parsed = json.loads(data)
        if not isinstance(parsed, dict):
            result.add_error("INVALID_JSON_TYPE", "JSON必须是对象类型")
            return result
        return result
    except json.JSONDecodeError as e:
        result.add_error("JSON_DECODE_ERROR", f"JSON解析失败: {str(e)}")
        return result


# ==================== 旅行计划结构校验 ====================
def validate_plan_structure(plan: dict) -> ValidationResult:
    """校验旅行计划结构"""
    result = ValidationResult()
    
    required_fields = ["city", "start_date", "end_date", "days"]
    for field in required_fields:
        if field not in plan:
            result.add_error("MISSING_FIELD", f"缺少必填字段: {field}", field)
        elif plan[field] is None:
            result.add_error("NULL_FIELD", f"字段值为空: {field}", field)
    
    return result


# ==================== 天数校验 ====================
def validate_days_length(plan: dict, expected_days: int) -> ValidationResult:
    """校验days数组长度是否匹配预期"""
    result = ValidationResult()
    
    days = plan.get("days", [])
    actual_days = len(days)
    
    if actual_days != expected_days:
        result.add_error(
            "DAYS_MISMATCH",
            f"天数不匹配: 预期{expected_days}天, 实际{actual_days}天",
            "days"
        )
    
    return result


# ==================== 日期校验 ====================
def validate_dates(plan: dict) -> ValidationResult:
    """校验日期合法性"""
    result = ValidationResult()
    
    start_date = plan.get("start_date")
    end_date = plan.get("end_date")
    
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            result.add_error("INVALID_START_DATE", f"开始日期格式错误: {start_date}", "start_date")
    
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            result.add_error("INVALID_END_DATE", f"结束日期格式错误: {end_date}", "end_date")
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if end < start:
                result.add_error("DATE_ORDER_ERROR", "结束日期不能早于开始日期", "end_date")
        except ValueError:
            pass
    
    return result


# ==================== 每日行程校验 ====================
def validate_daily_plan(day_plan: dict, day_index: int, expected_city: str) -> ValidationResult:
    """校验单日行程"""
    result = ValidationResult()
    
    required_fields = ["date", "day_index", "description", "attractions", "meals"]
    for field in required_fields:
        if field not in day_plan:
            result.add_error("MISSING_FIELD", f"第{day_index+1}天缺少字段: {field}", f"days[{day_index}].{field}")
    
    day_idx = day_plan.get("day_index")
    if day_idx is not None and day_idx != day_index:
        result.add_warning("DAY_INDEX_MISMATCH", f"第{day_index+1}天的day_index为{day_idx}, 应为{day_index}", f"days[{day_index}].day_index")
    
    date_str = day_plan.get("date")
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            result.add_error("INVALID_DATE", f"第{day_index+1}天日期格式错误: {date_str}", f"days[{day_index}].date")
    
    attractions = day_plan.get("attractions", [])
    if not isinstance(attractions, list):
        result.add_error("INVALID_ATTRACTIONS_TYPE", f"第{day_index+1}天attractions必须是数组", f"days[{day_index}].attractions")
    elif len(attractions) == 0:
        result.add_warning("EMPTY_ATTRACTIONS", f"第{day_index+1}天没有安排景点", f"days[{day_index}].attractions")
    elif len(attractions) > 5:
        result.add_warning("TOO_MANY_ATTRACTIONS", f"第{day_index+1}天安排了{len(attractions)}个景点,可能过于紧凑", f"days[{day_index}].attractions")
    
    for i, attr in enumerate(attractions):
        if not isinstance(attr, dict):
            result.add_error("INVALID_ATTRACTION_TYPE", f"第{day_index+1}天景点{i+1}必须是对象", f"days[{day_index}].attractions[{i}]")
            continue
        
        if "name" not in attr or not attr["name"]:
            result.add_warning("MISSING_ATTRACTION_NAME", f"第{day_index+1}天景点{i+1}缺少名称", f"days[{day_index}].attractions[{i}].name")
        
        if "visit_duration" in attr and attr["visit_duration"]:
            try:
                dur = int(attr["visit_duration"])
                if dur > 480:
                    result.add_warning("EXCESSIVE_VISIT_DURATION", f"第{day_index+1}天景点{i+1}游览时长{dur}分钟过长", f"days[{day_index}].attractions[{i}].visit_duration")
                elif dur < 15:
                    result.add_warning("TOO_SHORT_VISIT_DURATION", f"第{day_index+1}天景点{i+1}游览时长{dur}分钟过短", f"days[{day_index}].attractions[{i}].visit_duration")
            except ValueError:
                result.add_error("INVALID_VISIT_DURATION", f"第{day_index+1}天景点{i+1}游览时长必须是数字", f"days[{day_index}].attractions[{i}].visit_duration")
    
    meals = day_plan.get("meals", [])
    meal_types = {"breakfast", "lunch", "dinner"}
    found_types = set()
    
    for meal in meals:
        if isinstance(meal, dict) and "type" in meal:
            found_types.add(meal["type"])
    
    missing_meals = meal_types - found_types
    if missing_meals:
        result.add_warning("MISSING_MEALS", f"第{day_index+1}天缺少{', '.join(missing_meals)}安排", f"days[{day_index}].meals")
    
    return result


# ==================== 预算校验 ====================
def validate_budget(plan: dict) -> ValidationResult:
    """校验预算"""
    result = ValidationResult()
    
    budget = plan.get("budget")
    if not budget:
        result.add_warning("MISSING_BUDGET", "缺少预算信息", "budget")
        return result
    
    if not isinstance(budget, dict):
        result.add_error("INVALID_BUDGET_TYPE", "budget必须是对象", "budget")
        return result
    
    required_budget_fields = ["total_attractions", "total_hotels", "total_meals", "total_transportation", "total"]
    for field in required_budget_fields:
        if field not in budget:
            result.add_warning("MISSING_BUDGET_FIELD", f"预算缺少字段: {field}", f"budget.{field}")
    
    total_calculated = sum([
        budget.get("total_attractions", 0),
        budget.get("total_hotels", 0),
        budget.get("total_meals", 0),
        budget.get("total_transportation", 0),
    ])
    
    total_given = budget.get("total", 0)
    if total_calculated != total_given:
        result.add_warning("BUDGET_MISMATCH", f"预算总额不匹配: 分项合计{total_calculated}, 总计{total_given}", "budget.total")
    
    for field in ["total_attractions", "total_hotels", "total_meals", "total_transportation", "total"]:
        value = budget.get(field)
        if value is not None:
            try:
                num = float(value)
                if num < 0:
                    result.add_error("NEGATIVE_BUDGET", f"预算{field}不能为负数", f"budget.{field}")
            except ValueError:
                result.add_error("INVALID_BUDGET_VALUE", f"预算{field}必须是数字", f"budget.{field}")
    
    return result


# ==================== 天气信息校验 ====================
def validate_weather(plan: dict, travel_days: int) -> ValidationResult:
    """校验天气信息"""
    result = ValidationResult()
    
    weather_info = plan.get("weather_info", [])
    
    if len(weather_info) == 0:
        result.add_warning("NO_WEATHER_DATA", "没有天气信息", "weather_info")
    elif len(weather_info) < travel_days:
        result.add_warning("INCOMPLETE_WEATHER", f"天气信息不完整: 预期{travel_days}天, 实际{len(weather_info)}天", "weather_info")
    
    for i, weather in enumerate(weather_info):
        if not isinstance(weather, dict):
            result.add_error("INVALID_WEATHER_TYPE", f"天气数据第{i+1}条必须是对象", f"weather_info[{i}]")
            continue
        
        if "date" not in weather:
            result.add_warning("MISSING_WEATHER_DATE", f"天气数据第{i+1}条缺少日期", f"weather_info[{i}].date")
    
    return result


# ==================== 景点真实性校验 ====================
def validate_attractions_against_data(plan: dict, attractions_data: list) -> ValidationResult:
    """校验景点是否来自真实数据"""
    result = ValidationResult()
    
    real_attraction_names = {attr.get("name", "") for attr in attractions_data}
    
    for day_idx, day_plan in enumerate(plan.get("days", [])):
        for attr_idx, attraction in enumerate(day_plan.get("attractions", [])):
            attr_name = attraction.get("name", "")
            if attr_name and attr_name not in real_attraction_names:
                result.add_warning(
                    "UNVERIFIED_ATTRACTION",
                    f"第{day_idx+1}天景点'{attr_name}'未在原始数据中找到",
                    f"days[{day_idx}].attractions[{attr_idx}].name"
                )
    
    return result


# ==================== 酒店真实性校验 ====================
def validate_hotels_against_data(plan: dict, hotels_data: list) -> ValidationResult:
    """校验酒店是否来自真实数据"""
    result = ValidationResult()
    
    real_hotel_names = {hotel.get("name", "") for hotel in hotels_data}
    
    for day_idx, day_plan in enumerate(plan.get("days", [])):
        hotel = day_plan.get("hotel")
        if isinstance(hotel, dict):
            hotel_name = hotel.get("name", "")
            if hotel_name and hotel_name not in real_hotel_names:
                result.add_warning(
                    "UNVERIFIED_HOTEL",
                    f"第{day_idx+1}天酒店'{hotel_name}'未在原始数据中找到",
                    f"days[{day_idx}].hotel.name"
                )
    
    return result


# ==================== 综合校验 ====================
def validate_trip_plan(
    plan: dict,
    expected_days: int,
    expected_city: str,
    attractions_data: Optional[list] = None,
    hotels_data: Optional[list] = None
) -> ValidationResult:
    """
    综合校验旅行计划
    
    Args:
        plan: 旅行计划字典
        expected_days: 预期旅行天数
        expected_city: 预期目的地城市
        attractions_data: 原始景点数据（可选，用于校验景点真实性）
        hotels_data: 原始酒店数据（可选，用于校验酒店真实性）
        
    Returns:
        ValidationResult: 校验结果
    """
    print("\n" + "="*60)
    print("[校验] 开始综合校验旅行计划")
    print("="*60)
    
    result = ValidationResult()
    
    # 1. 结构校验
    struct_result = validate_plan_structure(plan)
    result.errors.extend(struct_result.errors)
    result.warnings.extend(struct_result.warnings)
    result.is_valid = result.is_valid and struct_result.is_valid
    
    # 2. 天数校验
    days_result = validate_days_length(plan, expected_days)
    result.errors.extend(days_result.errors)
    result.warnings.extend(days_result.warnings)
    result.is_valid = result.is_valid and days_result.is_valid
    
    # 3. 日期校验
    date_result = validate_dates(plan)
    result.errors.extend(date_result.errors)
    result.warnings.extend(date_result.warnings)
    result.is_valid = result.is_valid and date_result.is_valid
    
    # 4. 每日行程校验
    for day_idx, day_plan in enumerate(plan.get("days", [])):
        daily_result = validate_daily_plan(day_plan, day_idx, expected_city)
        result.errors.extend(daily_result.errors)
        result.warnings.extend(daily_result.warnings)
        result.is_valid = result.is_valid and daily_result.is_valid
    
    # 5. 预算校验
    budget_result = validate_budget(plan)
    result.errors.extend(budget_result.errors)
    result.warnings.extend(budget_result.warnings)
    
    # 6. 天气校验
    weather_result = validate_weather(plan, expected_days)
    result.errors.extend(weather_result.errors)
    result.warnings.extend(weather_result.warnings)
    
    # 7. 景点真实性校验（如果提供了原始数据）
    if attractions_data:
        attr_result = validate_attractions_against_data(plan, attractions_data)
        result.errors.extend(attr_result.errors)
        result.warnings.extend(attr_result.warnings)
    
    # 8. 酒店真实性校验（如果提供了原始数据）
    if hotels_data:
        hotel_result = validate_hotels_against_data(plan, hotels_data)
        result.errors.extend(hotel_result.errors)
        result.warnings.extend(hotel_result.warnings)
    
    # 计算最终分数
    result.score = max(0, 100 - len(result.errors) * 10 - len(result.warnings) * 2)
    
    print(f"[校验] 完成: 有效={result.is_valid}, 分数={result.score:.2f}, 错误={len(result.errors)}, 警告={len(result.warnings)}")
    
    if result.errors:
        print("\n[校验] 错误列表:")
        for err in result.errors:
            print(f"  - [{err['code']}] {err['message']}")
    
    if result.warnings:
        print("\n[校验] 警告列表:")
        for warn in result.warnings:
            print(f"  - [{warn['code']}] {warn['message']}")
    
    return result


# ==================== 修复建议 ====================
def generate_fix_suggestions(validation_result: ValidationResult) -> List[str]:
    """根据校验结果生成修复建议"""
    suggestions = []
    
    error_codes = {err["code"] for err in validation_result.errors}
    warning_codes = {warn["code"] for warn in validation_result.warnings}
    
    if "DAYS_MISMATCH" in error_codes:
        suggestions.append("检查days数组长度，确保与travel_days一致")
    
    if "INVALID_JSON_TYPE" in error_codes or "JSON_DECODE_ERROR" in error_codes:
        suggestions.append("检查JSON格式是否正确")
    
    if "MISSING_FIELD" in error_codes:
        suggestions.append("确保包含所有必填字段：city, start_date, end_date, days")
    
    if "UNVERIFIED_ATTRACTION" in warning_codes:
        suggestions.append("部分景点未在原始数据中找到，建议使用真实景点")
    
    if "UNVERIFIED_HOTEL" in warning_codes:
        suggestions.append("部分酒店未在原始数据中找到，建议使用真实酒店")
    
    if "MISSING_BUDGET" in warning_codes:
        suggestions.append("建议添加预算信息")
    
    if "EMPTY_ATTRACTIONS" in warning_codes:
        suggestions.append("部分天数未安排景点，请补充")
    
    if "TOO_MANY_ATTRACTIONS" in warning_codes:
        suggestions.append("部分天数景点过多，建议每天2-3个")
    
    return suggestions


# ==================== 批量测试 ====================
def test_validation():
    """测试校验功能"""
    test_plan = {
        "city": "北京",
        "start_date": "2024-05-01",
        "end_date": "2024-05-03",
        "days": [
            {
                "date": "2024-05-01",
                "day_index": 0,
                "description": "第一天：故宫游览",
                "transportation": "地铁",
                "accommodation": "舒适型",
                "attractions": [
                    {"name": "故宫博物院", "visit_duration": 180}
                ],
                "meals": [
                    {"type": "breakfast", "name": "酒店早餐", "estimated_cost": 30},
                    {"type": "lunch", "name": "四季民福", "estimated_cost": 80}
                ]
            },
            {
                "date": "2024-05-02",
                "day_index": 1,
                "description": "第二天：颐和园",
                "attractions": [],
                "meals": []
            }
        ],
        "budget": {
            "total_attractions": 60,
            "total_hotels": 800,
            "total_meals": 200,
            "total_transportation": 50,
            "total": 1000
        },
        "weather_info": [
            {"date": "2024-05-01", "day_weather": "晴"}
        ],
        "overall_suggestions": "建议提前预约"
    }
    
    print("=" * 60)
    print("结果校验测试")
    print("=" * 60)
    
    result = validate_trip_plan(test_plan, expected_days=3, expected_city="北京")
    print(f"\n校验结果: {result}")
    print(f"\n修复建议: {generate_fix_suggestions(result)}")


if __name__ == "__main__":
    test_validation()