# 模型连接（模型管理）设计

## 目标

独立「模型管理」：多条可命名连接；每条含提供商类型、模型名、Base URL、API Key；列表展示**连接状态**（会话内最近一次测试结果）；支持新建、删除、**一键测试**（单条或批量）；指定**默认连接**供运行时选模型。

## 存储

- `config/model_connections/<id>.json`：一条连接一条文件（与 MCP/skills 一致）。
- `config/manifest.json` 增加 `model_connection_ids: string[]` 作为顺序与权威 id 列表。
- `config/settings.json` 的 `LlmSettings` 增加可选字段 `default_model_connection_id: string | null`。
- 保留原有 `openai_*` / `anthropic_*` / `default_provider`：当**未**设置默认连接 id 或该 id 不存在时，`get_chat_model` 仍走旧逻辑，避免破坏现有用户。

## 连接条目（Pydantic）

- `id`, `name`（展示用自定义名）, `provider`: `openai_compatible` | `anthropic`
- `base_url`: 字符串；空则 OpenAI 兼容用 `https://api.openai.com/v1`，Anthropic 用官方默认。
- `api_key`, `model`, `enabled`

## 连接测试（不持久化状态）

- 状态仅在管理页内存中显示：`未测试` | `成功` | `失败: <原因>`；打开窗口或点「刷新」可清空或保留（实现：刷新列表时保留可选，简单起见**仅内存**，关窗即失）。
- `openai_compatible`：`GET {base}/models`，`Authorization: Bearer <key>`，超时约 15s。
- `anthropic`：`POST /v1/messages` 极小请求（使用条目中的 `model`），带 `x-api-key` 与 `anthropic-version`；根据 HTTP 状态与响应体判断是否可达。

测试在后台线程执行，避免阻塞 Qt UI。

## UI

- 主表列：启用（勾选）、名称、模型、Base URL（截断）、状态、操作（「测试」按钮）。
- 工具栏：新建连接、删除、测试选中、测试全部、设为默认、刷新、关闭。
- 新建/编辑：独立对话框（名称、提供商、URL、Key、模型、启用）。
- 默认连接：下拉或表格旁单选，绑定 `default_model_connection_id` 写入 `settings.json`。

## 运行时

- `get_chat_model(..., install_root=)`：若存在默认连接且启用，按 `provider` 构造 `ChatOpenAI`（`base_url`）或 `ChatAnthropic`；否则回退旧 `LlmSettings`。

## 非目标（本版不做）

- 任务级覆盖连接；向量/路由；密钥加密存储（仍明文 JSON，与当前 settings 一致）。

定稿：2026-03-30
