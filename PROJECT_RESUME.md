# 旅行规划 Agent 项目 - 简历素材

## 一、项目概述

**项目名称**：智能旅行规划助手（AI Trip Planner）

**项目定位**：基于 LangGraph 的垂直领域 AI Agent，帮助用户快速生成包含景点推荐、酒店预订、天气查询、交通规划、预算估算的完整旅行计划。

**技术栈**：
- 框架：LangGraph + LangChain + FastAPI
- 语言：Python 3.10+
- 数据库：SQLite（可扩展至 PostgreSQL）
- 前端：Vue 3 + Vite
- 部署：Docker + Docker Compose
- 外部服务：高德地图 API、DeepSeek LLM API

**项目亮点**：
- 完整的 Tool-Calling Agent 工作流，集成真实地图数据
- 模块化设计，支持 HelloAgents 和 LangGraph 双框架版本
- Docker 容器化部署，支持阿里云 ECS 一键部署

---

## 二、核心功能

1. **景点搜索**：调用高德地图 POI API，获取目的地热门景点（公园、博物馆、景区等）
2. **天气预报**：获取旅行期间的天气信息，用于行程优化
3. **酒店推荐**：根据住宿偏好（经济型/舒适型/豪华型）筛选酒店
4. **交通规划**：搜索往返城市的交通方案（高铁、飞机、大巴）
5. **行程生成**：基于真实数据，LLM 自动生成详细的每日行程计划
6. **行程管理**：用户登录后可保存、查看、删除旅行计划

---

## 三、问题与解决方案

### 3.1 部署问题：端口占用

**问题描述**：阿里云服务器上部署时，端口 8000 被其他服务占用，导致后端无法启动。

**解决方案**：
- 将后端端口从 8000 修改为 8001
- 更新 docker-compose.yml 中的端口映射配置
- 更新前端 API 地址配置
- 更新 Nginx 反向代理配置

**代码改动**：
- [docker-compose.yml](backend/docker-compose.yml)：修改 ports 配置
- [frontend/.env](frontend/.env)：修改 VITE_API_BASE_URL

**简历价值**：展示排查和解决部署问题的能力，熟悉 Docker 和端口配置。

---

### 3.2 部署问题：SSH 权限拒绝

**问题描述**：使用 SSH 密钥连接阿里云 ECS 时，出现 "Permission denied (publickey)" 错误。

**解决方案**：
- 在阿里云控制台重置实例密码
- 修改 `/etc/ssh/sshd_config`，设置 `PasswordAuthentication yes`
- 重启 SSH 服务：`systemctl restart sshd`
- 使用密码登录后，重新配置 SSH 密钥

**简历价值**：展示服务器运维和安全配置能力。

---

### 3.3 Docker 构建失败：依赖安装问题

**问题描述**：Docker 构建时，`pip install -r requirements.txt` 失败，exit code 2。

**解决方案**：
- 分析错误日志，发现 `hello-agents` 依赖安装失败
- 使用清华镜像源加速依赖安装
- 将依赖安装拆分为多个步骤，先安装基础依赖，再安装 AI 相关依赖
- 移除 `hello-agents` 依赖后重新添加

**代码改动**：
- [backend/Dockerfile](backend/Dockerfile)：重新编写依赖安装逻辑

**简历价值**：展示 Docker 构建优化和依赖管理能力。

---

### 3.4 FastAPI 参数定义错误

**问题描述**：API 路由中 `current_user` 参数缺少依赖注入，`SavePlanRequest` 未继承 `BaseModel`，导致启动报错。

**解决方案**：
- 为 `current_user` 参数添加 `get_optional_user` 依赖函数
- 修改 `SavePlanRequest` 类继承 `BaseModel`
- 添加必要的 import 语句

**代码改动**：
- [backend/app/api/routes/trip_langgraph.py](backend/app/api/routes/trip_langgraph.py)：修复参数定义

**简历价值**：展示 FastAPI 框架使用和调试能力。

---

### 3.5 前端启动错误：依赖缺失

**问题描述**：前端执行 `npm run dev` 时，报错 "'vite' is not recognized"。

**解决方案**：
- 在前端目录执行 `npm install` 安装所有依赖
- 确认 `node_modules` 目录生成
- 使用 `npx vite` 验证 Vite 是否安装成功

**简历价值**：展示前端项目配置和依赖管理能力。

---

## 四、优化动作

### 4.1 Prompt 工程优化

**优化前**：
- Prompt 分散在 `langgraph_workflow.py` 和 `langgraph_tools.py` 两个文件中
- 系统提示词仅简单描述角色："你是一个专业的旅行规划师"
- 没有思维链引导，LLM 直接生成结果
- 没有 Few-shot 示例，输出格式不稳定

**优化后**：
- 创建独立的 [prompts.py](backend/app/agents/prompts.py) 统一管理所有提示词
- 增强角色设定："智行规划师，10年经验的资深旅行规划专家"
- 添加思维链引导（Chain-of-Thought）：分析数据 → 规划路线 → 分配预算 → 生成 JSON
- 添加完整的 Few-shot 示例（北京3天旅行计划）
- 增加错误处理策略：数据不足时的 fallback 机制

**优化效果**：
- 生成的旅行计划格式更加规范统一
- LLM 输出 JSON 的成功率提升
- 行程安排更加合理，考虑天气和地理位置因素

**代码改动**：
- 新建 [backend/app/agents/prompts.py](backend/app/agents/prompts.py)
- 修改 [backend/app/agents/langgraph_workflow.py](backend/app/agents/langgraph_workflow.py)：使用新的 prompt
- 修改 [backend/app/agents/langgraph_tools.py](backend/app/agents/langgraph_tools.py)：使用统一模板

**简历价值**：展示 Prompt Engineering 能力，理解思维链和 Few-shot 技术。

---

### 4.2 框架迁移：从 HelloAgents 到 LangGraph

**背景**：最初项目使用 HelloAgents 框架，但该框架生态不够成熟，文档和社区支持较少。

**迁移方案**：
- 定义 LangGraph 状态结构 `TripAgentState`，包含用户输入、中间状态、最终输出
- 将原有的工具函数（景点搜索、天气查询、酒店搜索、交通规划）封装为 LangChain Tool
- 创建 StateGraph 工作流，包含两个核心节点：`search_tools`（收集数据）和 `generate_plan`（生成计划）
- 重构 API 路由，支持 HelloAgents 和 LangGraph 双版本

**迁移效果**：
- 工作流更加可视化，便于调试和扩展
- 支持持久化执行和流式输出（LangGraph 内置能力）
- 社区生态更成熟，便于后续功能扩展

**代码改动**：
- 新建 [backend/app/agents/langgraph_state.py](backend/app/agents/langgraph_state.py)
- 新建 [backend/app/agents/langgraph_tools.py](backend/app/agents/langgraph_tools.py)
- 新建 [backend/app/agents/langgraph_workflow.py](backend/app/agents/langgraph_workflow.py)
- 新建 [backend/app/api/routes/trip_langgraph.py](backend/app/api/routes/trip_langgraph.py)

**简历价值**：展示多框架对比和迁移能力，理解 Agent Framework 和 Agent Runtime 的区别。

---

### 4.3 任务识别模块（Intent Recognition）

**背景**：用户输入可能包含自然语言描述（如"帮我规划北京3天旅行"），需要识别用户意图并提取关键信息。

**设计方案**：
- 定义 7 种意图类型：生成计划、查询景点、查询天气、查询酒店、查询交通、调整计划、推荐美食
- 使用规则+权重的方式进行意图识别，支持置信度计算
- 从自然语言中提取城市、天数、日期、出发城市等关键信息
- 支持城市别名（如"帝都"→北京、"魔都"→上海）

**功能特性**：
- 意图识别准确率高，支持模糊匹配
- 自动提取实体信息，减少用户输入步骤
- 置信度低于阈值时标记为"未知意图"，避免误判

**代码改动**：
- 新建 [backend/app/agents/intent_recognition.py](backend/app/agents/intent_recognition.py)
- 修改 [backend/app/agents/langgraph_workflow.py](backend/app/agents/langgraph_workflow.py)：添加意图识别节点
- 修改 [backend/app/agents/langgraph_state.py](backend/app/agents/langgraph_state.py)：添加意图识别相关状态字段

**简历价值**：展示自然语言处理和意图识别能力，理解 NLU 技术在 Agent 系统中的应用。

---

### 4.4 结果校验模块（Result Validation）

**背景**：LLM 生成的旅行计划可能存在格式错误、天数不匹配、景点编造等问题，需要在返回给用户前进行校验。

**设计方案**：
- 创建综合校验函数，包含 8 项校验：JSON格式、结构完整性、天数匹配、日期合法性、每日行程、预算、天气信息、真实性校验
- 区分错误（必须修复）和警告（建议修复），不同级别扣不同分数
- 自动生成修复建议，指导 LLM 重试优化
- 校验失败时自动触发重试（最多3次）

**功能特性**：
- 自动校验生成计划的合法性和真实性
- 景点/酒店真实性校验：比对原始数据，检测 LLM 编造信息
- 分数机制：满分100分，错误扣10分，警告扣2分
- 自动重试：校验失败时自动触发重新生成

**代码改动**：
- 新建 [backend/app/agents/result_validation.py](backend/app/agents/result_validation.py)
- 修改 [backend/app/agents/langgraph_workflow.py](backend/app/agents/langgraph_workflow.py)：添加结果校验节点和条件重试逻辑
- 修改 [backend/app/agents/langgraph_state.py](backend/app/agents/langgraph_state.py)：添加校验相关状态字段

**简历价值**：展示系统设计和质量保障能力，理解 Agent 系统中校验和兜底机制的重要性。

---

### 4.5 失败兜底模块（Fallback Handler）

**背景**：在生产环境中，外部 API（高德地图、DeepSeek LLM）可能因为网络、限流、Key 失效等原因失败，必须有兜底机制保证系统可用性。

**设计方案**：
- 实现 4 级兜底策略：L1 软兜底（默认值）、L2 中兜底（通用数据）、L3 硬兜底（基础模板）、L4 紧急兜底（手动查询提示）
- 每个工具调用都有独立的 try-except 保护，失败时自动降级
- 错误分类：API错误、LLM错误、解析错误、校验错误、超时错误、未知错误
- 提供默认数据：5个热门城市的默认景点、3档酒店模板、基础天气数据

**功能特性**：
- 单个工具失败不影响整体流程
- LLM生成失败时返回基础模板计划，保证用户至少能看到一个可用结果
- 完整的错误日志记录，便于排查问题
- 兜底级别和数据来源可追溯

**代码改动**：
- 新建 [backend/app/agents/fallback_handler.py](backend/app/agents/fallback_handler.py)
- 修改 [backend/app/agents/langgraph_workflow.py](backend/app/agents/langgraph_workflow.py)：工具调用和LLM生成加try-except

**简历价值**：展示系统可靠性和容错能力，理解生产环境 Agent 系统的健壮性设计。

---

### 4.6 用户反馈模块（User Feedback）- LLM 驱动 + 前端 UI

**背景**：用户对生成的旅行计划可能有各种调整需求（换景点、改预算、调节奏），系统需要支持自然语言调整请求的处理。

**技术演进**：
- **v1（规则匹配）**：使用正则表达式解析用户输入，只能处理简单句式
- **v2（LLM 驱动）**：使用 LLM 理解用户反馈，智能处理任意复杂度的调整请求
- **v3（完整闭环）**：添加前端 UI，实现完整的反馈交互闭环

**v3 设计方案**：

**后端新增接口**：
- `POST /api/trip/plan/langgraph/adjust`：LLM 驱动的计划调整
- `POST /api/trip/feedback`：提交用户反馈（评分、评论、调整请求）

**前端新增功能**：
- 评分功能：1-5星评分
- 评论功能：文字评论输入
- 智能调整：自然语言调整请求（如"第一天太赶了，减少一个景点"）
- 一键调整：调用 LLM 重新生成调整后的计划

**功能特性**：
- 智能意图理解：能处理复杂、模糊的自然语言反馈
- 上下文感知：理解用户的真实需求，而非字面匹配
- 渐进式调整：用户可以连续追问，逐步完善计划
- 兜底机制：LLM 调整失败时自动降级到基础模板
- 实时更新：调整后页面实时刷新，地图重新初始化

**代码改动**：
- 新建 [backend/app/agents/adjust_plan.py](backend/app/agents/adjust_plan.py)：LLM驱动的计划调整
- 新建 [backend/app/agents/user_feedback.py](backend/app/agents/user_feedback.py)：反馈记录和存储
- 修改 [backend/app/agents/prompts.py](backend/app/agents/prompts.py)：添加调整计划提示词
- 修改 [backend/app/agents/langgraph_workflow.py](backend/app/agents/langgraph_workflow.py)：使用LLM处理反馈
- 修改 [backend/app/api/routes/trip_langgraph.py](backend/app/api/routes/trip_langgraph.py)：新增调整和反馈接口
- 修改 [frontend/src/services/api.ts](frontend/src/services/api.ts)：新增 API 方法
- 修改 [frontend/src/views/Result.vue](frontend/src/views/Result.vue)：添加反馈面板 UI

**简历价值**：展示用户交互设计和智能反馈处理能力，理解 LLM 在 Agent 系统中的核心作用，完整的反馈闭环实现。

---

## 五、工程化实践

### 5.1 配置管理

- 使用 `pydantic-settings` 管理配置，支持 `.env` 文件
- 配置项包括：服务器端口、CORS 域名、API Key、LLM 配置等
- 提供配置验证函数 `validate_config()`，启动时检查必要配置

**代码**：[backend/app/config.py](backend/app/config.py)

---

### 5.2 异常处理

- API 路由层：使用 try-except 捕获异常，返回统一的 HTTP 错误响应
- 工具函数层：每个工具都有独立的异常处理，失败时返回空数据而非崩溃
- 日志记录：关键节点打印详细日志，便于排查问题

**代码**：[backend/app/api/routes/trip_langgraph.py](backend/app/api/routes/trip_langgraph.py)

---

### 5.3 Docker 容器化

- 后端和前端分别构建 Docker 镜像
- 使用 Docker Compose 编排多容器服务
- 配置环境变量传递敏感信息（API Key 等）
- 数据库数据持久化到宿主机

**代码**：[docker-compose.yml](docker-compose.yml)

---

### 5.4 用户认证

- 使用 JWT 实现用户登录和认证
- 支持注册、登录、密码重置
- 行程保存和查询需要用户认证
- 使用 `python-jose` 和 `argon2-cffi` 进行令牌生成和密码加密

**代码**：[backend/app/auth.py](backend/app/auth.py)

---

## 六、项目亮点总结

| 维度 | 亮点 | 简历话术 |
|------|------|---------|
| **业务价值** | 垂直场景（旅行规划），解决真实痛点 | "针对旅行规划场景，设计并实现了基于 AI Agent 的智能行程生成系统" |
| **技术架构** | Tool-Calling + LangGraph 工作流 | "构建了完整的工具调用链，集成高德地图 API 获取真实数据，通过 LangGraph 编排工作流" |
| **Prompt 工程** | 思维链引导 + Few-shot + 错误处理 | "通过优化系统提示词、添加思维链引导和 Few-shot 示例，提升了生成结果的质量和稳定性" |
| **框架迁移** | HelloAgents → LangGraph | "主导完成从 HelloAgents 到 LangGraph 的框架迁移，提升了系统的可维护性和扩展性" |
| **工程化** | Docker 部署 + 配置管理 + 异常处理 | "完成项目的 Docker 容器化部署，实现配置拆分、异常处理、日志记录等工程化实践" |
| **容错能力** | 4级失败兜底策略 | "设计了4级兜底机制，API失败时自动降级到默认数据或基础模板，保证系统可用性" |
| **用户反馈** | LLM驱动 + 智能调整 | "使用LLM理解用户反馈，实现智能计划调整，支持复杂自然语言和连续追问" |

---

## 七、待完成事项

- [x] 添加任务识别模块（已完成）
- [x] 添加结果校验模块，校验生成的旅行计划是否合法（已完成）
- [x] 添加失败兜底策略，工具调用失败时有降级方案（已完成）
- [x] 添加用户反馈模块，支持自然语言调整请求（已完成）
- [ ] 构建测试集，覆盖简单问答、多轮追问、知识缺失、歧义问题等场景
- [ ] 添加指标跟踪（响应时间、工具调用成功率、JSON 解析成功率）
- [ ] 添加可观测性，记录完整的执行日志（模型输入输出、工具调用过程）
- [ ] 完善多轮对话，支持更复杂的追问场景