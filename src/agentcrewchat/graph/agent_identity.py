"""Agent 身份注册表：集中管理固定 Agent 的名字、角色、主题色。"""
from __future__ import annotations

FIXED_AGENTS: dict[str, dict] = {
    "consultant": {"name": "晓柔", "role": "需求分析师", "color": "#7c3aed"},
    "architect":  {"name": "明哲", "role": "架构师",     "color": "#2563eb"},
    "reviewer":   {"name": "铁口", "role": "审核员",     "color": "#ea580c"},
}

_FALLBACK = {"role": "执行者", "color": "#0891b2"}


def get_agent_display(agent_id: str) -> dict:
    """返回 Agent 的显示信息 {name, role, color}。

    已知固定 Agent 返回预设值，未知 ID 返回 fallback。
    """
    if agent_id in FIXED_AGENTS:
        return dict(FIXED_AGENTS[agent_id])
    return {"name": agent_id, **_FALLBACK}
