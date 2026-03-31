# AgentLoom 第一版设计规格

## 1. 目标与范围

桌面客户端：基于**任务文件夹隔离**的受控多智能体协作。技术栈：**PySide6**；模型调用 **LangChain**；编排与状态 **LangGraph**；支持多家模型提供商。

## 2. 目录布局（均在安装根下，便携、须可写）

| 路径 | 用途 |
|------|------|
| `workspaces/task_<时间戳>_<任务名>/` | 任务隔离根：`.venv`、`pyproject.toml`、产出物、任务内 skills 等 |
| `config/` | JSON 多文件 + JSON Schema：MCP/skill 注册、Shell 策略、模型相关开关等 |
| `data/` | LangGraph checkpoint（如 SQLite）、运行索引、日志索引 |

不使用独立用户数据目录；同机多用户共用同一安装根。

## 3. Python 与 uv

- 任务初始化时在任务目录执行 **`uv venv`**，得到本地 `.venv`。
- 依赖通过 **`pyproject.toml`** / **`uv add`** 管理，禁止污染系统 Python。
- 执行 Python：**`uv run`** 或 **`<task>/.venv/Scripts/python.exe`**（由应用解析路径）。

## 4. 三栏 UI

- **左栏**：列举 `workspaces/` 下任务；新建任务即创建目录并完成 `uv venv`。
- **中栏**：顾问对话及任务控制消息；HITL 时同区或覆盖层展示确认/编辑。
- **右栏**：专家执行流：**思考 → 行动 → 结果**（含工具调用、命令行输出、错误）；Reviewer 结论单独高亮。

LangGraph 在 **Worker 线程**运行，经 **Qt 信号**向 UI 线程投递事件。

## 5. 运行时架构

**单进程方案（v1）**：PySide 主进程 + Worker 跑图；**`QProcess`/subprocess** 承载 `uv`、MCP 子进程、Shell 命令。

## 6. 五阶段与 LangGraph 状态要点

建议状态字段：`task_id`、`phase`、`consult_confidence`、`blueprint`（步骤、专家角色、工具 id、验收标准）、`mounted_tools`、`expert_runs`、`review_round`、`review_verdict`、`gap_decision`。

1. **Consultant**：连续追问至内部置信度 ≥ 阈值后进入 Architect。
2. **Architect**：读取合并后的 `config/` 工具清单；产出蓝图与差距分析。存在不可覆盖能力时 **interrupt**，用户必选方案（降级/改范围/终止/稍后补工具）后继续。
3. **HITL_Blueprint**：**interrupt**；可视化编辑蓝图；**Confirm & Loom** 后进入执行。
4. **ExpertSwarm**：按蓝图派发；仅使用已挂载 MCP、任务内脚本（`uv run`）、已安装 skills。
5. **Reviewer**：按蓝图验收标准审核；通过则交付；不通过则打回对应专家；**达最大审核轮数**时 **interrupt**：强制交付 / 回退改蓝图 / 终止。

## 7. 人工参与（HITL）

- 蓝图确认前必须暂停。
- **Skills 安装**及**敏感工具**使用前必须说明并确认。
- **差距分析**分支须用户决策。
- **审核达上限**须用户决策。
- **Shell**：不要求每次执行命令都确认；**首次**在应用或任务中开启 Shell 能力、或命中配置中的**高危模式/前缀**时再走 HITL；其余记录日志并在右栏展示。

## 8. 工具来源（第一版）

- **MCP**（配置驱动启动与挂载）。
- **任务内由 Agent 编写的 Python**（经该任务 `uv` 环境执行）。
- **Skills**：随包/用户级只读资源 + 内置 **find-skills** 检索安装到**当前任务**下约定目录（如 `.agentloom/skills/`），安装前 HITL。

第一版**不做向量检索**；架构师依赖 **`config/` 权威清单**（由 UI 可视化新增、校验后写入）。

## 9. 配置约定

- **格式**：**JSON** 多文件 + **JSON Schema** 校验后写入。
- **结构**：例如 `config/mcp/<id>.json`、`config/skills/<id>.json`、根级 `manifest.json`（版本、id 列表、校验元数据），支持原子更新与回滚思路。
- **架构师**：启动时合并加载为只读清单注入上下文。

## 10. 本机命令行（cmd / PowerShell）

- 在配置中**固定一种** Shell（cmd 或 PowerShell）。
- 由应用 **QProcess/subprocess** 执行，默认 **`cwd` = 当前任务根**；超时、环境变量、stdout/stderr 上限可配置；输出进入事件流。
- 路径与命令做基本防越界校验（细则在实现阶段细化）。

## 11. 嵌入式与打包注意

安装根须可写；若用户将程序置于不可写位置，需在文档或启动时提示。

---

*定稿日期：2026-03-30*
