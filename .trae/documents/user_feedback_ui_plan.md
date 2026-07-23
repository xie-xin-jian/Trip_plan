# 用户反馈 UI 功能实现计划

## 问题分析

当前项目已实现：
- ✅ 后端：用户反馈模块（user_feedback.py）、LLM驱动的计划调整（adjust_plan.py）
- ❌ 前端：Result.vue 页面没有反馈相关的 UI 入口

用户反馈功能缺失的环节：
1. 点赞/点踩按钮
2. 评分功能（1-5星）
3. 文字评论输入框
4. 调整请求输入（自然语言调整计划）

## 实现方案

### 1. 后端 API 修改

**文件**: `backend/app/api/routes/trip_langgraph.py`

新增接口：
- `POST /api/trip/plan/langgraph/adjust` - LLM 驱动的计划调整
- `POST /api/trip/feedback` - 提交用户反馈（评分、评论、点赞）

### 2. 前端 UI 修改

**文件**: `frontend/src/views/Result.vue`

新增组件：
- 反馈卡片区域（点赞、评分、评论）
- 调整请求输入框（自然语言调整）
- 调整结果展示

### 3. 前端 API 服务

**文件**: `frontend/src/services/api.ts`

新增方法：
- `submitFeedback()` - 提交反馈
- `adjustPlan()` - 请求调整计划

## 实施步骤

### 步骤 1: 修改后端 API

在 `trip_langgraph.py` 中添加：
```python
# 计划调整接口
@router.post("/plan/langgraph/adjust")
async def adjust_trip_plan(
    request: AdjustPlanRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    # 调用 adjust_plan_with_llm_sync
    ...

# 反馈提交接口
@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    # 调用 save_feedback
    ...
```

### 步骤 2: 添加 Pydantic 模型

在 `trip_langgraph.py` 中添加：
- `AdjustPlanRequest` - 调整请求模型
- `FeedbackRequest` - 反馈请求模型

### 步骤 3: 修改前端 API 服务

在 `api.ts` 中添加：
```typescript
export const adjustPlan = async (planId: string, feedback: string, plan: any) => { ... }
export const submitFeedback = async (planId: string, feedback: any) => { ... }
```

### 步骤 4: 修改前端 Result.vue

在页面中添加反馈区域：
1. 页面顶部按钮区域添加"反馈"按钮
2. 页面底部添加反馈卡片（评分、评论、调整请求）
3. 实现调整请求的提交和结果更新

## 风险评估

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| LLM 调用超时 | 中 | 高 | 添加加载状态和超时提示 |
| 反馈数据丢失 | 低 | 中 | 使用内存存储，生产环境迁移到数据库 |
| 调整结果不符合预期 | 中 | 中 | 添加重试按钮和手动编辑作为兜底 |

## 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/api/routes/trip_langgraph.py` | 修改 | 添加调整和反馈接口 |
| `frontend/src/services/api.ts` | 修改 | 添加 API 方法 |
| `frontend/src/views/Result.vue` | 修改 | 添加反馈 UI |

## 完成标准

1. 用户可以在结果页面看到反馈入口
2. 用户可以提交评分和评论
3. 用户可以输入自然语言调整请求
4. 调整请求可以调用 LLM 并返回调整后的计划