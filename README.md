# AgentLoom

桌面端多智能体协作：按任务文件夹隔离与 **uv** 独立环境；从需求到蓝图、人在回路、专家执行与审核的流程骨架（**LangGraph**）；支持 **MCP**、本机命令行与 **Skills** 扩展（持续完善中）。

**仓库：** [github.com/ZhaoQi0202/AgentLoom](https://github.com/ZhaoQi0202/AgentLoom)

## 技术栈

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（依赖与任务内虚拟环境）
- PySide6（三栏界面）
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

- **GUI（默认）：** 在项目根（或已设置 `AGENTLOOM_ROOT` 的目录）下生成 `config/`、`data/`、`workspaces/`。
- **无界面：** `uv run python -m agentloom --cli`

安装根默认可写；若不可写，启动时会提示将程序置于可写目录。

## 界面与配置

| 能力 | 说明 |
|------|------|
| 左栏 | 任务列表；新建任务会创建 `workspaces/task_<时间戳>_<名称>/` 并初始化 uv 环境 |
| 中栏 | 对话区（占位） |
| 右栏 | 图谱运行事件 |
| 模型设置 | 工具栏「模型设置」→ 写入 `config/settings.json`（**勿提交**，已在 `.gitignore`） |
| MCP | 「添加 MCP」→ `config/mcp/<id>.json` + 更新 `manifest.json` |

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
