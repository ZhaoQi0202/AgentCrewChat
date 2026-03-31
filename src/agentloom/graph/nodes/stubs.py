from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agentloom.graph.state import AgentLoomState
from agentloom.llm.factory import get_chat_model


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
    """Consultant: 分析用户需求，输出结构化需求摘要。"""
    user_request = state.get("user_request", "未提供任务描述")

    system = (
        "你是一位资深需求分析师 (Consultant)。你的职责是：\n"
        "1. 理解用户的任务需求\n"
        "2. 拆解为清晰的功能点\n"
        "3. 评估需求明确度 (0-1)\n"
        "4. 指出潜在的风险和模糊点\n\n"
        "用中文回答，使用 Markdown 格式。"
    )
    user = f"请分析以下任务需求：\n\n{user_request}"

    message = _call_llm(system, user)

    return {
        "phase": "consult",
        "consult_confidence": 0.9,
        "consult_summary": message,
        "message": message,
    }


def architect(state: AgentLoomState) -> dict[str, Any]:
    """Architect: 基于需求分析设计技术方案和执行蓝图。"""
    user_request = state.get("user_request", "")
    consult_summary = state.get("consult_summary", "")

    system = (
        "你是一位技术架构师 (Architect)。你的职责是：\n"
        "1. 基于需求分析结果，设计技术方案\n"
        "2. 选择合适的技术栈\n"
        "3. 将方案拆解为 3-6 个可执行步骤\n"
        "4. 定义验收标准\n\n"
        "输出格式要求：\n"
        "- 技术栈选择及理由\n"
        "- 执行步骤（编号列表）\n"
        "- 验收标准（编号列表）\n\n"
        "用中文回答，使用 Markdown 格式。"
    )
    user = (
        f"原始需求：\n{user_request}\n\n"
        f"需求分析结果：\n{consult_summary}\n\n"
        "请设计技术方案和执行蓝图。"
    )

    message = _call_llm(system, user)

    return {
        "phase": "architect",
        "blueprint": {"raw": message},
        "architect_gap_notes": "",
        "message": message,
    }


def hitl_blueprint(state: AgentLoomState) -> dict[str, Any]:
    """HITL Blueprint: 等待人工审核蓝图，通过后继续。"""
    return {
        "phase": "hitl_blueprint",
        "message": (
            "**蓝图已提交审核**\n\n"
            "请查看上方 Architect 的方案，确认是否符合预期。\n"
            "如需调整请说明修改意见，确认无误请回复「继续」。"
        ),
    }


def experts(state: AgentLoomState) -> dict[str, Any]:
    """Expert Swarm: 根据蓝图执行具体任务。"""
    user_request = state.get("user_request", "")
    blueprint = state.get("blueprint", {})
    blueprint_text = blueprint.get("raw", "") if isinstance(blueprint, dict) else str(blueprint)

    system = (
        "你是一组专家团队 (Expert Swarm)。你的职责是：\n"
        "1. 按照蓝图中的步骤逐一执行\n"
        "2. 为每个步骤给出具体的实现方案或代码片段\n"
        "3. 记录每个步骤的执行结果\n\n"
        "以技术专家的视角，给出详实的执行报告。\n"
        "用中文回答，使用 Markdown 格式。代码用代码块标注语言。"
    )
    user = (
        f"原始需求：\n{user_request}\n\n"
        f"执行蓝图：\n{blueprint_text}\n\n"
        "请逐步执行蓝图并报告结果。"
    )

    message = _call_llm(system, user)

    return {
        "phase": "experts",
        "expert_runs": [{"swarm_output": message}],
        "message": message,
    }


def reviewer(state: AgentLoomState) -> dict[str, Any]:
    """Reviewer: 审查执行结果，决定是否通过。"""
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
        "你是一位代码审查员 (Reviewer)。你的职责是：\n"
        "1. 对照需求和蓝图，审查专家团队的执行结果\n"
        "2. 检查是否满足所有验收标准\n"
        "3. 给出审查结论：PASS 或 NEEDS_REVISION\n"
        "4. 列出优点和待改进项\n\n"
        "用中文回答，使用 Markdown 格式。\n"
        "最后一行必须是：`结论: PASS` 或 `结论: NEEDS_REVISION`"
    )
    user = (
        f"原始需求：\n{user_request}\n\n"
        f"执行蓝图：\n{blueprint_text}\n\n"
        f"执行结果：\n{expert_text}\n\n"
        f"这是第 {r + 1} 轮审查，请给出审查意见。"
    )

    message = _call_llm(system, user)

    verdict = "pass" if "PASS" in message.upper() and "NEEDS_REVISION" not in message.upper() else "needs_revision"

    return {
        "phase": "review",
        "review_round": r + 1,
        "review_verdict": verdict,
        "message": message,
    }
