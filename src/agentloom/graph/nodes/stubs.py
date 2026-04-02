from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agentloom.graph.nodes.architect_agent import generate_blueprint
from agentloom.graph.state import AgentLoomState
from agentloom.llm.factory import get_chat_model
from agentloom.paths import workspaces_dir
from agentloom.tasks.blueprint import save_blueprint
from agentloom.tasks.requirement import load_requirement


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用 LLM 获取回复。"""
    llm = get_chat_model()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    resp = llm.invoke(messages)
    return resp.content


def consultant(state: AgentLoomState) -> dict[str, Any]:
    """需求分析师：传递已收集的需求摘要（实际对话在 WebSocket collect 阶段完成）。"""
    summary = state.get("user_request", "未提供任务描述")
    return {
        "phase": "consult",
        "consult_confidence": 1.0,
        "consult_summary": summary,
        "message": summary,
    }


def architect(state: AgentLoomState) -> dict[str, Any]:
    """架构设计师：读取需求和可用工具，生成 DAG 任务规划。"""
    task_id = state.get("task_id", "")
    task_path = workspaces_dir() / task_id if task_id else None

    # 读取结构化需求
    requirement = None
    if task_path and task_path.exists():
        requirement = load_requirement(task_path)
    if not requirement:
        requirement = {
            "core_goal": state.get("user_request", ""),
            "raw_conversation_summary": state.get("consult_summary", ""),
        }

    # 生成 blueprint
    message, blueprint = generate_blueprint(requirement, task_path)

    # 保存 blueprint.json 到 workspace
    if blueprint and task_path and task_path.exists():
        save_blueprint(task_path, blueprint)

    return {
        "phase": "architect",
        "blueprint": blueprint or {"raw": message},
        "architect_gap_notes": "",
        "message": message,
    }


def hitl_blueprint(state: AgentLoomState) -> dict[str, Any]:
    """方案审核员：展示架构师的任务规划，等待人工审核。"""
    blueprint = state.get("blueprint", {})
    tasks = blueprint.get("tasks", []) if isinstance(blueprint, dict) else []

    if tasks:
        summary_lines = ["架构师的任务规划如下：\n"]
        for t in tasks:
            deps = ", ".join(t.get("depends_on", [])) or "无"
            tools = ", ".join(t.get("tools", []))
            summary_lines.append(
                f"  [{t.get('id', '?')}] {t.get('name', '?')} — {t.get('goal', '')}\n"
                f"    工具: {tools} | 依赖: {deps}"
            )
        summary_lines.append("\n确认没问题回复「继续」，需要调整请说明修改意见。")
        msg = "\n".join(summary_lines)
    else:
        msg = "方案已提交，请审核上面架构设计师的方案。确认无误回复「继续」，需要调整请说明修改意见。"

    return {
        "phase": "hitl_blueprint",
        "message": msg,
    }


def experts(state: AgentLoomState) -> dict[str, Any]:
    """执行专家组：根据蓝图执行任务。"""
    user_request = state.get("user_request", "")
    blueprint = state.get("blueprint", {})
    blueprint_text = blueprint.get("raw", "") if isinstance(blueprint, dict) else str(blueprint)

    system = (
        "你是执行专家组。在一个项目群聊中，你的职责是汇报执行进展。\n"
        "要求：\n"
        "- 回复必须控制在100-200个字符以内\n"
        "- 用简洁的群聊对话风格，不要使用 Markdown 标题格式\n"
        "- 直接说：做了什么、关键结果、有无问题\n"
        "- 像在工作群里给同事发进度汇报一样说话\n"
    )
    user = f"需求：{user_request}\n蓝图：{blueprint_text}\n请汇报执行结果。"

    message = _call_llm(system, user)

    return {
        "phase": "experts",
        "expert_runs": [{"swarm_output": message}],
        "message": message,
    }


def reviewer(state: AgentLoomState) -> dict[str, Any]:
    """质量审查员：审查执行结果。"""
    user_request = state.get("user_request", "")
    blueprint = state.get("blueprint", {})
    blueprint_text = blueprint.get("raw", "") if isinstance(blueprint, dict) else str(blueprint)
    expert_runs = state.get("expert_runs", [])
    expert_text = ""
    for run in expert_runs:
        if isinstance(run, dict):
            expert_text += run.get("swarm_output", str(run)) + "\n"

    r = int(state.get("review_round", 0))

    system = (
        "你是质量审查员。在一个项目群聊中，你的职责是快速给出审查结论。\n"
        "要求：\n"
        "- 回复必须控制在100-200个字符以内\n"
        "- 用简洁的群聊对话风格，不要使用 Markdown 标题格式\n"
        "- 直接说：审查结论（通过/需修改）、关键问题\n"
        "- 最后必须包含 PASS 或 NEEDS_REVISION\n"
        "- 像在工作群里给同事发审查意见一样说话\n"
    )
    user = (
        f"需求：{user_request}\n蓝图：{blueprint_text}\n"
        f"执行结果：{expert_text}\n第{r + 1}轮审查，请给出结论。"
    )

    message = _call_llm(system, user)

    verdict = "pass" if "PASS" in message.upper() and "NEEDS_REVISION" not in message.upper() else "needs_revision"

    return {
        "phase": "review",
        "review_round": r + 1,
        "review_verdict": verdict,
        "message": message,
    }
