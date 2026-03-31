# 模型连接 Implementation Plan

> **For agentic workers:** 按任务顺序执行；步骤用 `- [ ]` 勾选。

**Goal:** 可增删的命名模型连接 + 列表状态 + 后台测试 + 默认连接驱动 `get_chat_model`，并与旧 `settings.json` 共存回退。

**Architecture:** `config/model_connections/*.json` + manifest `model_connection_ids`；纯函数 `connection_check`（urllib）；Qt 管理页 + 编辑对话框；`LlmSettings` 增加 `default_model_connection_id`。

**Tech Stack:** PySide6、Pydantic、LangChain ChatOpenAI/ChatAnthropic、stdlib urllib

---

### Task 1: 配置模型与 manifest

**Files:**
- Modify: `src/agentloom/config/models.py`
- Modify: `config/manifest.json`
- Modify: `src/agentloom/config/schema/manifest.schema.json`

- [x] 新增 `ModelConnectionEntry`；`ManifestRecord.model_connection_ids`；`LlmSettings.default_model_connection_id`

### Task 2: CRUD 与加载顺序

**Files:**
- Create: `src/agentloom/config/model_connection_store.py`
- Modify: `src/agentloom/config/manifest.py`（如需导出，可仅从 loader 调）

- [x] `iter_model_connection_files`、`load_model_connection`、`save_model_connection_entry`、`delete_model_connection_entry`、`list_model_connections`

### Task 3: 连接探测

**Files:**
- Create: `src/agentloom/llm/connection_check.py`

- [x] `normalize_openai_base_url`、`probe_openai_compatible`、`probe_anthropic_connection` → `(ok: bool, message: str)`

### Task 4: LLM 工厂接入默认连接

**Files:**
- Modify: `src/agentloom/llm/factory.py`
- Modify: `src/agentloom/config/llm_settings_store.py`（确保新字段读写）

- [x] 优先默认连接；否则旧逻辑

### Task 5: UI

**Files:**
- Modify: `src/agentloom/ui/dialogs/models_manager.py`
- Create: `src/agentloom/ui/dialogs/model_connection_editor.py`

- [x] 表格、新建/编辑/删除、测试线程、默认连接下拉、保存 manifest + settings

### Task 6: 测试

**Files:**
- Create: `tests/test_model_connection_store.py`
- Create: `tests/test_connection_check.py`（mock urllib）

- [x] `uv run pytest -q` 全绿

---

## Commit

每完成一个 Task 可单独 commit，或 Task 6 后一次 commit。
