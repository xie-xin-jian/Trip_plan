"""用户反馈模块 - User Feedback"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class FeedbackType(Enum):
    """反馈类型"""
    POSITIVE = "positive"            # 点赞
    NEGATIVE = "negative"            # 点踩
    RATING = "rating"                # 评分
    ADJUST_REQUEST = "adjust_request" # 调整请求
    COMMENT = "comment"              # 文字评论
    REGENERATE = "regenerate"        # 重新生成


class FeedbackRecord:
    """反馈记录"""
    
    def __init__(
        self,
        feedback_id: str,
        plan_id: str,
        user_id: Optional[str],
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        adjust_type: Optional[str] = None,
        adjust_target: Optional[str] = None,
        adjust_params: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        self.feedback_id = feedback_id
        self.plan_id = plan_id
        self.user_id = user_id
        self.feedback_type = feedback_type
        self.rating = rating
        self.comment = comment
        self.adjust_type = adjust_type
        self.adjust_target = adjust_target
        self.adjust_params = adjust_params or {}
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "feedback_id": self.feedback_id,
            "plan_id": self.plan_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type,
            "rating": self.rating,
            "comment": self.comment,
            "adjust_type": self.adjust_type,
            "adjust_target": self.adjust_target,
            "adjust_params": self.adjust_params,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


# ==================== 内存存储（生产环境应使用数据库）====================
_feedback_store: List[FeedbackRecord] = []


def save_feedback(feedback: FeedbackRecord) -> bool:
    """保存反馈"""
    try:
        _feedback_store.append(feedback)
        print(f"[反馈] 保存反馈: {feedback.feedback_id}, 类型: {feedback.feedback_type}")
        return True
    except Exception as e:
        print(f"[反馈] 保存失败: {e}")
        return False


def get_feedback_by_plan(plan_id: str) -> List[FeedbackRecord]:
    """获取某个计划的所有反馈"""
    return [f for f in _feedback_store if f.plan_id == plan_id]


def get_feedback_stats() -> Dict[str, Any]:
    """获取反馈统计"""
    if not _feedback_store:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "avg_rating": 0,
            "adjust_requests": 0
        }
    
    total = len(_feedback_store)
    positive = sum(1 for f in _feedback_store if f.feedback_type == FeedbackType.POSITIVE.value)
    negative = sum(1 for f in _feedback_store if f.feedback_type == FeedbackType.NEGATIVE.value)
    ratings = [f.rating for f in _feedback_store if f.rating is not None]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    adjust_requests = sum(1 for f in _feedback_store if f.feedback_type == FeedbackType.ADJUST_REQUEST.value)
    
    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "avg_rating": round(avg_rating, 2),
        "adjust_requests": adjust_requests,
        "satisfaction_rate": round(positive / (positive + negative) * 100, 2) if (positive + negative) > 0 else 0
    }