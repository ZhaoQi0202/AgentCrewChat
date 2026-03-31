# AgentLoom

桌面端多智能体协作：按任务文件夹隔离与 **uv** 独立环境；从需求到蓝图、人在回路、专家执行与审核的流程骨架（**LangGraph**）；支持 **MCP**、本机命令行与 **Skills** 扩展（持续完善中）。

**仓库：** [github.com/ZhaoQi0202/AgentLoom](https://github.com/ZhaoQi0202/AgentLoom)

## 技术栈

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（依赖与任务内虚拟环境）
- Electron + React（`client/`，桌面 UI）
- LangChain（多厂商 Chat 模型）+ LangGraph（状态与中断）
- Pydantic（配置校验）

## 环境要求

- Python **3.11+**
- 已安装 **uv**（[安装说明](https://docs.astral.sh/uv/getting-started/installation/)）
- 创建任务虚拟环境、执行 `uv venv` / `uv run` 时，本机需能调用 **uv**（未打入当前 PyInstaller 包）

## 快速开始

```powershell
git clone https://github.com/ZhaoQi0202/AgentLoom.git
cd AgentLoom
uv sync
uv run python -m agentloom
```

- **HTTP API（默认）：** `uv run python -m agentloom` 启动 FastAPI（默认 `127.0.0.1:9800`），并在项目根（或 `AGENTLOOM_ROOT`）下确保 `config/`、`data/`、`workspaces/` 存在。
- **仅初始化布局：** `uv run python -m agentloom --cli`
- **桌面客户端：** 见 `client/README.md`（`npm run dev` / `npm run dev:electron`）

安装根默认可写；Electron 启动后端前会检查可写性。

## 配置与数据

| 项 | 说明 |
|------|------|
| 任务工作区 | `workspaces/task_<时间戳>_<名称>/`，新建任务时初始化 uv 环境 |
| 模型 | `client` 内模型页或手写 `config/settings.json`、`config/model_connections/`（**勿提交**，见 `.gitignore`） |
| MCP | `config/mcp/<id>.json` + `manifest.json` |
| 技能（应用级） | `data/skills_install/`；与任务下 `.agentloom/skills/` 由 `merged_skills_for_agents` 合并，同名任务级覆盖 |

可选环境变量：**`AGENTLOOM_ROOT`** — 指定安装根（数据与配置均相对该路径）。

## Windows 打包

```powershell
uv sync
uv run pyinstaller --noconfirm packaging\agentloom.spec
```

产物目录：`dist\AgentLoom\`，可整体拷贝分发。详见 `packaging\agentloom.spec`。

## 测试

```powershell
uv sync --group dev
uv run pytest -q
```

## 文档

设计与实现计划见 `docs/superpowers/specs/`、`docs/superpowers/plans/`。

## 许可证

Apache License 2.0 — 见 [LICENSE](LICENSE)。
