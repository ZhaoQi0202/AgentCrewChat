"""工具注册表：根据工具 ID 列表创建 LangChain Tool 实例。"""
from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.tools import BaseTool

from agentcrewchat.tools.python_tool import create_python_tool
from agentcrewchat.tools.shell_tool import create_shell_tool

logger = logging.getLogger(__name__)

# 工具 ID → 创建函数的映射
_BUILTIN_TOOL_FACTORIES: dict[str, callable] = {
    "shell": create_shell_tool,
    "python": create_python_tool,
}


def _load_mcp_tools(mcp_id: str, install_root: Path | None) -> list[BaseTool]:
    """从 config/mcp/<mcp_id>.json 读取 MCP 配置，实例化工具列表。"""
    try:
        from agentcrewchat.config.loader import load_all
        from agentcrewchat.paths import config_dir

        cfg_root = (install_root / "config").resolve() if install_root else config_dir()
        cfg = load_all(cfg_root)
        entry = next((m for m in cfg.mcps if m.id == mcp_id), None)
        if entry is None:
            logger.warning("MCP 配置未找到: %s", mcp_id)
            return []
        logger.info("已加载 MCP 配置: %s (command=%s)", mcp_id, entry.command)
        # TODO: 连接 MCP 服务器并获取工具列表（Batch 2+）
        logger.warning("MCP 工具运行时尚未实现，跳过: %s", mcp_id)
        return []
    except Exception:
        logger.error("加载 MCP 工具失败: %s", mcp_id, exc_info=True)
        return []


def _load_skill_tools(
    skill_id: str, install_root: Path | None, task_id: str | None
) -> list[BaseTool]:
    """从 Skills 注册表查找（先项目级再全局级），加载工具。"""
    try:
        from agentcrewchat.config.loader import load_all
        from agentcrewchat.paths import config_dir

        cfg_root = (install_root / "config").resolve() if install_root else config_dir()
        cfg = load_all(cfg_root)
        entry = next((s for s in cfg.skills if s.id == skill_id and s.enabled), None)
        if entry is None:
            logger.warning("Skill 配置未找到或已禁用: %s", skill_id)
            return []
        logger.info("已加载 Skill 配置: %s (dir=%s)", skill_id, entry.skill_dir)
        # TODO: 将 Skill 转换为 LangChain Tool（Batch 2+）
        logger.warning("Skill 工具运行时尚未实现，跳过: %s", skill_id)
        return []
    except Exception:
        logger.error("加载 Skill 工具失败: %s", skill_id, exc_info=True)
        return []


def create_tools_for_task(
    tool_ids: list[str],
    workspace: Path,
    *,
    install_root: Path | None = None,
    task_id: str | None = None,
) -> list[BaseTool]:
    """根据工具 ID 列表创建绑定到 workspace 的 LangChain Tool 实例。

    支持的 ID 格式：
    - shell / python — 内置工具
    - mcp:<mcp_id> — MCP 工具
    - skill:<skill_id> — Skills 工具
    未识别的 ID 会记录警告日志。
    """
    tools: list[BaseTool] = []
    seen: set[str] = set()
    for tid in tool_ids:
        if tid in seen:
            continue
        seen.add(tid)
        if tid in _BUILTIN_TOOL_FACTORIES:
            tools.append(_BUILTIN_TOOL_FACTORIES[tid](workspace))
        elif tid.startswith("mcp:"):
            tools.extend(_load_mcp_tools(tid[4:], install_root))
        elif tid.startswith("skill:"):
            tools.extend(_load_skill_tools(tid[6:], install_root, task_id))
        else:
            logger.warning("Unknown tool ID in blueprint: %s", tid)
    return tools
