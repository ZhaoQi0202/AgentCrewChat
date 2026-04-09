# 后端开发规范

**范围**：`src/agentcrewchat/`、Python 3.11+、FastAPI、LangGraph

---

## 1. 分层架构

| 层 | 路径 | 职责 |
|----|------|------|
| **路由层** | `api/routes/*` | 校验请求、管理会话、调下层；不写长业务、不直接拼 LLM 提示词 |
| **graph** | `graph/*` | 图编译、节点实现、编排、EventBus、checkpoint；不操作 HTTP 响应对象 |
| **tasks** | `tasks/*` | 工作区创建、venv 管理、需求/蓝图持久化 |
| **config** | `config/*` | LLM 连接、MCP、Skills、LLM 设置的加载与持久化 |
| **skills** | `skills/*` | Skills 注册表、合并逻辑、导入 |
| **tools** | `tools/*` | 工具实例化（shell、python、MCP、Skills） |
| **llm** | `llm/*` | LLM 工厂，按阶段返回对应模型连接 |

---

## 2. 安装根与路径

- 以 **`AGENTCREWCHAT_ROOT`**（或 cwd）为根
- `graph/builder.py` 对 env 的修改必须可恢复
- 路径 `Path.resolve()` 后校验落在 `install_root` 下，防路径穿越
- 任务 Skills 目录：`<workspace>/.agentcrewchat/skills/`

---

## 3. LLM 配置（四阶段分配）

- 用户可为四个阶段分别指定 LLM 连接：需求收集 / 架构规划 / 执行 / 审核
- `settings.json` 新增 `phase_model_connections` 字段：`{ "collect": "<conn_id>", "architect": "<conn_id>", "execute": "<conn_id>", "review": "<conn_id>" }`，每个阶段可独立配置或留空（回退到默认连接）
- LLM 工厂（`llm/factory.py`）的 `get_chat_model()` 新增 `phase` 参数，按阶段查找对应连接；无特定配置时回退到 `default_model_connection_id`
- 各 Agent 节点调用 `get_chat_model(phase="collect"|"architect"|"execute"|"review")` 传入对应阶段
- 执行阶段所有执行 Agent 共用同一 LLM 连接（一期）
- **密钥存储**：`config/model_connections/*.json`，默认不提交 git，代码不打印密钥

---

## 4. Agent 角色提示词规范

### 4.1 固定 Agent

| Agent | 名字 | 性格提示词方向 | 主题色 |
|-------|------|---------------|--------|
| 需求分析师 | 晓柔 | 温和耐心、善于引导，像项目群里贴心的同事，一次只问一个问题 | `#7c3aed`（紫） |
| 架构师 | 明哲 | 严谨理性、言简意赅，直接给结论，不废话 | `#2563eb`（蓝） |
| 审核员 | 铁口 | 毒舌挑剔但细致，审核不通过时给出具体改进建议，直言不讳 | `#ea580c`（橙） |

### 4.2 执行 Agent

- 名字从**随机生成的两字中文名**中分配（如：小见、小瑶、小辰），同一项目组内不重复
- 每次从性格池随机选一种性格，注入提示词
- 性格池：急性子 / 碎嘴子 / 自信派 / 谨慎派 / 乐观派 / 毒舌徒弟 / 学院派 / 佛系
- 主题色从执行 Agent 色板随机分配（15 色：青/绿/粉/靛/棕/珊瑚/翠/玫红/钴蓝/琥珀/薰衣草/湖蓝/橄榄/石板/酒红），不与固定 Agent 主题色重复；超过 15 个时随机生成 HSL 颜色（S: 60-80%, L: 40-55%，色相与已分配色至少相距 30°）

### 4.3 消息规范

- 所有推送到群聊的消息必须是**人类可读的自然语言 + Markdown**，禁止裸 JSON
- Agent 间移交消息由 LLM 生成（拟人化），包含 `@对应名称`
- 审核员超限后的说明消息由 LLM 生成，带具体指导意见

---

## 5. API 与 WebSocket

- **REST**：UTF-8 JSON；错误用语义化状态码 + `detail`
- **WS**：JSON 帧；新增 `type` 必须同步更新前端解析和 `product.md`
- 推送内容必须可 JSON 序列化

### 5.1 WS 断线续跑

- **后端不停**：WS 断线后图执行继续，session 保持存活（不从 `_sessions` 中移除）
- **事件持久化**：EventBus 推送事件时，无论 WS 是否在线，均同步追加写入 `chat_history.json`
- **WS 推送容错**：向 WS 发送事件时捕获 `ConnectionClosed` 异常，仅标记连接断开，不中断执行
- **重连恢复**：前端重连同一 session 后，通过 `GET /api/tasks/<task_id>/chat-history` 拉取完整事件列表，与本地已有事件做差集补发
- **HITL 兼容**：断线期间若进入 `interrupt_before`，图在 checkpoint 暂停等待；重连后前端拉取状态发现 HITL 中断，正常展示确认卡片

---

## 6. DAG 执行与审核

### 6.1 执行规则

- 架构师规划时执行 Agent 默认上限 **5 个**，相似工具任务合并；用户明确要求时可超限
- 任务按依赖关系分层，同层可并行（当前逐个执行）

### 6.2 任务间暂停

- 每个 session 维护 `asyncio.Event` 暂停信号
- 执行 Agent 在**任务间隙**检查信号；当前任务跑完才响应暂停
- 收到继续信号后从断点恢复

### 6.3 审核重试与兜底

- 最多重试 `MAX_AGENT_RETRY`（= 3）次
- 超限后不静默继续，铁口发说明消息（LLM 生成，话术中自然引导用户选择），推送 `hitl_retry_limit` 事件给前端
- 前端在输入框区域显示三个快捷回复按钮，同时支持用户自由输入文本
- 后端对用户输入做意图识别（复用 `is_user_confirmation()` 类似逻辑）判断选择：
  - `skip`：跳过，记录失败继续后续任务
  - `reroute`：交还明哲重规划该任务点 — **单任务替换**（只替换失败任务，任务 ID 不变，插回 DAG 原位置重新执行），每个任务只能用一次
  - `terminate`：终止整个流水线
- 局部重规划后的任务若仍超限，只允许 `skip` 或 `terminate`

### 6.4 局部重规划流程

1. 铁口推送超限消息 → 用户选择 `reroute`
2. 后端向明哲发送：失败任务的原始描述 + 执行结果 + 铁口的审核意见
3. 明哲生成替代方案（更换工具/更换思路），输出格式与原蓝图任务项一致
4. 替代方案替换 DAG 中失败任务的节点（同一 task_id），依赖关系不变
5. 分配给同一个或新的执行 Agent 重新执行
6. 替代方案只有一次机会，若仍失败则只能跳过或终止

---

## 7. 状态与安全

- 图状态类型：**`AgentCrewChatState`**；加字段时考虑 checkpoint 兼容性
- 日志可打堆栈；返回给用户的内容不带敏感路径与密钥
- Shell 策略：Windows 默认使用 `cmd`，高风险命令前缀黑名单在后端配置，**不暴露给用户修改**

---

## 8. 聊天历史持久化

- 每个项目组的聊天事件持久化到本地：`workspaces/<task_id>/chat_history.json`
- **存储格式**：JSON 数组，每个元素为一个 `ChatEvent`（与 WS 推送的事件结构一致：`type`、`payload`、`timestamp`）
- **写入时机**：后端每次通过 EventBus 推送事件时，同步追加写入对应项目组的 `chat_history.json`
- **读取时机**：前端连接 WS 后、发送 `collect` 前，先请求 REST API `/api/tasks/<task_id>/chat-history` 获取历史事件
- 前端收到历史事件后直接注入 `chatStore.events`，不触发 pending 延迟队列
- 重启软件后历史仍在

---

## 9. 依赖与质量

- 新依赖写入 `pyproject.toml` 并 `uv lock`
- 关键逻辑应有单测；当前若无测试目录，不宣称已跑 pytest

---

## 10. 路径速查

| 区域 | 路径 |
|------|------|
| WS 路由 / 图 | `api/routes/graph.py`、`graph/*` |
| 任务 CRUD | `api/routes/tasks.py`、`tasks/workspace.py` |
| 配置 API | `api/routes/config.py` |
| LLM 工厂 | `llm/factory.py` |
| DAG 编排 | `graph/orchestrator.py` |
| Agent 节点 | `graph/nodes/` |
| Skills 合并 | `skills/registry.py` |

---

## 11. 自包含安装包（F-15）

### 11.1 技术方案

- **嵌入式 Python**：使用 [python-build-standalone](https://github.com/indygreg/python-build-standalone) 预编译的独立 Python 运行时
- **打包工具**：Electron Builder 负责 Electron 壳打包，Python 运行时作为 extraResources 一起打入安装包
- 安装包内目录结构：`resources/python/` 放嵌入式 Python，`resources/backend/` 放后端代码和依赖

### 11.2 运行时流程

1. Electron 主进程启动时，从 `resources/python/python.exe` 启动后端
2. `python-manager.cjs` 管理后端进程生命周期（已有框架）
3. 首次启动时用嵌入式 Python 的 pip 安装后端依赖到 `resources/backend/.venv/`
4. 后续启动跳过安装步骤

### 11.3 安装目录

- 首次安装时由用户选择安装目录（Electron Builder NSIS installer 默认支持）
- 工作区数据目录与安装目录分离，存放在 `%APPDATA%/AgentCrewChat/`
