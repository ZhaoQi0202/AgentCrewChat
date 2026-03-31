# AgentLoom v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: @superpowers:subagent-driven-development（推荐）或 @superpowers:executing-plans，按任务勾选 `- [ ]` 逐步执行。

**Goal:** 交付可运行的 PySide6 桌面壳 + 安装根下目录约定 + 配置清单加载 + 单任务 `uv venv` + LangGraph 五阶段骨架（含 interrupt 占位）+ 右栏事件流接线；真模型与完整 MCP/专家工具可后续迭代。

**Architecture:** 单进程：UI 主线程 + `QThread`/`QRunnable` 跑 LangGraph；`QProcess` 封装 `uv`、Shell、MCP 子进程。配置为 `config/` 下 JSON 多文件，Pydantic 或 jsonschema 校验。状态机用 LangGraph `interrupt_before` / `Command(resume=)` 对接 HITL。

**Tech Stack:** Python 3.11+、`uv`、`PySide6`、`langchain`、`langgraph`、`pydantic`（或 `jsonschema`）、`pytest`、`pytest-qt`（UI 测可选）。

**Spec:** `docs/superpowers/specs/2026-03-30-agentloom-design.md`

---

## 文件结构（拟创建）

| 路径 | 职责 |
|------|------|
| `pyproject.toml` | 依赖、包入口、`agentloom` console script |
| `src/agentloom/__init__.py` | 版本 |
| `src/agentloom/__main__.py` | `python -m agentloom` 启动 |
| `src/agentloom/bootstrap.py` | 解析安装根、创建 `config/` `data/` `workspaces/` |
| `src/agentloom/paths.py` | `install_root()`、`config_dir`、`data_dir`、`workspaces_dir` |
| `src/agentloom/config/manifest.py` | 读写 `config/manifest.json` |
| `src/agentloom/config/models.py` | MCP / skill / shell / settings 的 Pydantic 模型 |
| `src/agentloom/config/loader.py` | 合并加载、Schema 校验 |
| `src/agentloom/config/schema/` | `*.schema.json`（或内嵌 schema 字符串） |
| `src/agentloom/tasks/workspace.py` | 创建 `task_<ts>_<name>`、`uv venv`、列举任务 |
| `src/agentloom/runtime/process_runner.py` | 通用 `QProcess`：超时、输出截断、完成信号 |
| `src/agentloom/runtime/uv_runner.py` | `uv venv`、`uv run`、`uv add` 封装 |
| `src/agentloom/runtime/shell_runner.py` | cmd/ps1，`cwd`=任务根，高危前缀检测 |
| `src/agentloom/runtime/mcp_manager.py` | 按配置启动/停止 MCP 子进程（v1 可 stub） |
| `src/agentloom/llm/factory.py` | LangChain Chat 模型工厂（多提供商 env/配置） |
| `src/agentloom/graph/state.py` | `AgentLoomState` TypedDict/dataclass |
| `src/agentloom/graph/builder.py` | 编译 Graph、checkpoint、interrupt 节点 |
| `src/agentloom/graph/nodes/` | consultant、architect、hitl_blueprint、experts、reviewer 占位 |
| `src/agentloom/ui/app.py` | `QApplication` 入口 |
| `src/agentloom/ui/main_window.py` | 三栏 `QSplitter` |
| `src/agentloom/ui/panels/task_list.py` | 左栏 |
| `src/agentloom/ui/panels/chat_panel.py` | 中栏 |
| `src/agentloom/ui/panels/activity_panel.py` | 右栏时间线 |
| `src/agentloom/ui/worker.py` | `GraphRunner`：线程内 `graph.invoke` / `stream`，`pyqtSignal` 发事件 |
| `tests/conftest.py` | `pytest` 临时目录 fixture |
| `tests/test_paths.py` | 路径解析 |
| `tests/test_workspace.py` | 任务目录创建（mock `uv` 或可选集成） |
| `tests/test_config_loader.py` | manifest + 单 mcp json 校验 |
| `tests/test_graph_compile.py` | Graph 可编译、checkpoint 可写 SQLite |

---

### Task 1: 工程脚手架与入口

**Files:**
- Create: `pyproject.toml`
- Create: `src/agentloom/__init__.py`
- Create: `src/agentloom/__main__.py`
- Create: `src/agentloom/bootstrap.py`
- Create: `src/agentloom/paths.py`
- Test: `tests/test_paths.py`

- [ ] **Step 1: 写失败测试 `test_install_root_from_frozen_placeholder`**

在 `tests/conftest.py` 提供 `tmp_path`；测试假设通过环境变量 `AGENTLOOM_ROOT` 覆盖安装根（便于测），未设置时用 `Path.cwd()`。断言 `paths.install_root()` 为 `Path`。

```python
import os
from pathlib import Path
import agentloom.paths as p

def test_install_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    assert p.install_root() == tmp_path.resolve()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_paths.py::test_install_root_env_override -v`  
Expected: 导入失败或函数不存在

- [ ] **Step 3: 实现 `paths.py` + `bootstrap.ensure_layout()`**

`install_root()` 读 `AGENTLOOM_ROOT` 否则 `Path.cwd()`；`config_dir()` = root/`config`，`data_dir()` = root/`data`，`workspaces_dir()` = root/`workspaces`。`bootstrap.ensure_layout()` 创建缺失目录。

- [ ] **Step 4: 测试通过**

Run: `uv run pytest tests/test_paths.py -v`  
Expected: PASS

- [ ] **Step 5: `__main__.py` 调用 `bootstrap.ensure_layout()` 后启动占位 `print` 或后续接 UI**

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/agentloom tests
git commit -m "feat: scaffold package, paths, bootstrap dirs"
```

---

### Task 2: 配置清单与 Schema 校验

**Files:**
- Create: `src/agentloom/config/models.py`
- Create: `src/agentloom/config/manifest.py`
- Create: `src/agentloom/config/loader.py`
- Create: `src/agentloom/config/schema/manifest.schema.json`（最小字段：`version`, `mcp_ids`, `skill_ids`）
- Test: `tests/test_config_loader.py`

- [ ] **Step 1: 失败测试 `test_load_empty_manifest_creates_default`**

在临时 `AGENTLOOM_ROOT` 下调用 `loader.load_all()`，无文件时期望返回空列表或默认 manifest，不抛异常。

- [ ] **Step 2: 运行失败**

Run: `uv run pytest tests/test_config_loader.py -v`

- [ ] **Step 3: 实现 Pydantic 模型（McpEntry、SkillEntry、ShellPolicy）与 `load_manifest`、`iter_mcp_files`**

校验失败抛 `ConfigValidationError`。

- [ ] **Step 4: 测试通过**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: config loader and manifest"
```

---

### Task 3: 任务工作区与 uv

**Files:**
- Create: `src/agentloom/tasks/workspace.py`
- Modify: `src/agentloom/runtime/process_runner.py`（可先简单 subprocess 再换 QProcess）
- Test: `tests/test_workspace.py`

- [ ] **Step 1: 失败测试 `test_create_task_dir_name_format`**

`create_task("my job")` 返回路径包含 `task_` 与时间戳格式（可用 regex `task_\d+_.+`）。

- [ ] **Step 2: 实现 `create_task`：建目录、可选调用 `uv venv`（测试中 `monkeypatch` 替换为 no-op 或 echo）**

- [ ] **Step 3: `list_tasks` 排序降序**

- [ ] **Step 4: pytest 通过**

- [ ] **Step 5: Commit**

---

### Task 4: 进程执行封装（Shell / uv）

**Files:**
- Create: `src/agentloom/runtime/process_runner.py`
- Create: `src/agentloom/runtime/uv_runner.py`
- Create: `src/agentloom/runtime/shell_runner.py`
- Test: `tests/test_shell_runner.py`（mock 进程：返回固定 rc）

- [ ] **Step 1: `ShellRunner`：根据 `ShellPolicy` 选 `cmd.exe` 或 `powershell`，`cwd` 强制任务根，校验命令字符串不含 `..` 逃逸（v1 简化规则）**

- [ ] **Step 2: `hit_high_risk(command) -> bool` 单元测试**

- [ ] **Step 3: `UvRunner.venv_create(task_path)` 调用 `uv venv`**

- [ ] **Step 4: Commit**

---

### Task 5: LangGraph 状态与可编译图

**Files:**
- Create: `src/agentloom/graph/state.py`
- Create: `src/agentloom/graph/builder.py`
- Create: `src/agentloom/graph/nodes/stubs.py`（各节点返回占位 state 更新）
- Test: `tests/test_graph_compile.py`

- [ ] **Step 1: 定义 `AgentLoomState`（与 spec 字段对齐，用 `TypedDict` + `total=False` 或 reducer）**

- [ ] **Step 2: `builder.build_graph()` 链：consultant → architect → hitl_blueprint → experts → reviewer → END；`architect` / `hitl_blueprint` / `reviewer_max` 设 `interrupt_before`**

- [ ] **Step 3: `SqliteSaver` 指向 `data/checkpoints.sqlite`**

- [ ] **Step 4: 测试 `graph.get_graph().draw_ascii()` 或 `invoke` 空状态直到第一个 interrupt**

- [ ] **Step 5: Commit**

---

### Task 6: LLM 工厂（LangChain）

**Files:**
- Create: `src/agentloom/llm/factory.py`
- Create: `src/agentloom/config/settings.json` 模型（可选）
- Test: `tests/test_llm_factory_mock.py`（`monkeypatch` 返回 FakeChatModel）

- [ ] **Step 1: `get_chat_model(provider: str)` 读环境变量 API Key，未配置时工厂返回可注入的 Fake**

- [ ] **Step 2: Commit**

---

### Task 7: PySide 三栏壳

**Files:**
- Create: `src/agentloom/ui/app.py`
- Create: `src/agentloom/ui/main_window.py`
- Create: `src/agentloom/ui/panels/task_list.py`
- Create: `src/agentloom/ui/panels/chat_panel.py`
- Create: `src/agentloom/ui/panels/activity_panel.py`
- Modify: `src/agentloom/__main__.py` 启动 `QApplication`

- [ ] **Step 1: `MainWindow` 水平 `QSplitter` 1:2:1，占位控件**

- [ ] **Step 2: 左栏绑定 `list_tasks`，按钮「新建任务」调用 `workspace.create_task` 并刷新**

- [ ] **Step 3: 中栏 `QPlainTextEdit` 输入 + 发送按钮（v1 可只发信号）**

- [ ] **Step 4: 右栏 `QListWidget` 或 `QTreeWidget` 追加事件行**

- [ ] **Step 5: 可选 `pytest-qt` 点击新建或手工验收说明**

- [ ] **Step 6: Commit**

---

### Task 8: GraphRunner 与 UI 信号

**Files:**
- Create: `src/agentloom/ui/worker.py`
- Modify: `src/agentloom/ui/main_window.py`

- [ ] **Step 1: `GraphRunner(QObject)`：`pyqtSignal(str, dict)` 发阶段事件；线程内 `for chunk in graph.stream(..., stream_mode="updates")`**

- [ ] **Step 2: MainWindow 连接信号追加右栏**

- [ ] **Step 3: HITL：`interrupt` 后 UI 显示「继续」按钮，`Command(resume=user_payload)` 在同一线程再次 `invoke`（注意 LangGraph API 版本差异，以当前文档为准）**

- [ ] **Step 4: Commit**

---

### Task 9: 配置 UI（最小）

**Files:**
- Create: `src/agentloom/ui/dialogs/mcp_editor.py`（或表单页）
- Modify: `src/agentloom/config/loader.py` 暴露 `save_mcp_entry`

- [ ] **Step 1: 表单字段：id、command、args(JSON)、说明；保存前 Pydantic 校验并写 `config/mcp/<id>.json`，更新 manifest**

- [ ] **Step 2: Commit**

---

### Task 10: 打包与可写性检查

**Files:**
- Modify: `src/agentloom/bootstrap.py`

- [ ] **Step 1: 启动时尝试 `install_root().joinpath(".write_test")` 创建删除；失败则 `QMessageBox` 提示「请置于可写目录」**

- [ ] **Step 2: 文档一行（若项目已有 README 则加一句；无则跳过用户未要求的长文档）**

- [ ] **Step 3: Commit**

---

## 依赖示例（`pyproject.toml` 片段）

```toml
[project]
name = "agentloom"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "PySide6>=6.6",
  "langchain>=0.3",
  "langchain-openai",
  "langchain-anthropic",
  "langgraph>=0.2",
  "pydantic>=2",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-qt"]

[project.scripts]
agentloom = "agentloom.__main__:main"
```

（具体版本锁定在执行阶段用 `uv lock` 固定。）

---

## 执行交接

计划保存于 `docs/superpowers/plans/2026-03-30-agentloom-v1.md`。

**方式 1 — Subagent-Driven（推荐）：** 每任务新开子代理，任务间 review；配合 @superpowers:subagent-driven-development  

**方式 2 — Inline：** 本会话按勾选顺序实现，配合 @superpowers:executing-plans  

你要用哪一种？
