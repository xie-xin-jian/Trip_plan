"""旅行规划API路由"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
    ErrorResponse
)
from ...agents.trip_planner_agent import get_trip_planner_agent
from ...database import get_db, TripPlanDB, User
from ...auth import get_current_user

router = APIRouter(prefix="/trip", tags=["旅行规划"])


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求,生成详细的旅行计划"
)
async def plan_trip(
    request: TripRequest,
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    生成旅行计划

    Args:
        request: 旅行请求参数
        current_user: 当前登录用户（可选）

    Returns:
        旅行计划响应
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 收到旅行规划请求:")
        print(f"   城市: {request.city}")
        print(f"   日期: {request.start_date} - {request.end_date}")
        print(f"   天数: {request.travel_days}")
        print(f"{'='*60}\n")

        agent = get_trip_planner_agent()
        print("🚀 开始生成旅行计划...")
        trip_plan = agent.plan_trip(request)
        print("✅ 旅行计划生成成功,准备返回响应\n")

        return TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=trip_plan
        )

    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
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


@router.get(
    "/plans",
    summary="获取当前用户的行程列表",
    description="获取当前登录用户保存的所有旅行计划"
)
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


@router.get(
    "/plan/{plan_id}",
    summary="获取单个行程详情",
    description="根据ID获取行程的详细数据"
)
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


@router.delete(
    "/plan/{plan_id}",
    summary="删除行程",
    description="删除当前用户保存的某个行程"
)
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


@router.get(
    "/health",
    summary="健康检查",
    description="检查旅行规划服务是否正常"
)
async def health_check():
    """健康检查"""
    try:
        agent = get_trip_planner_agent()

        return {
            "status": "healthy",
            "service": "trip-planner",
            "agent_name": agent.agent.name,
            "tools_count": len(agent.agent.list_tools())
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )
