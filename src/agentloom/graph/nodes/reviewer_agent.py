"""Reviewer Agent：审核单个任务的执行结果。"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agentloom.graph.event_bus import emit_event
from agentloom.llm.factory import get_chat_model

REVIEWER_SYSTEM_PROMPT = """\
你是一位毒舌但专业的质量审查员，正在项目群聊中审核同事的工作成果。

## 你的审核方式
1. 对比任务目标和验收标准，检查实际产出是否达标
2. 审核通过时大方夸赞，不通过时犀利指出问题但给出具体建议
3. 语气像在工作群里跟同事开玩笑但说正事

## 输出格式
你的回复必须包含一个审核结论标记（放在回复的最后一行）：
- 通过：VERDICT:PASS
- 不通过：VERDICT:FAIL

## 示例
通过："代码过了一遍，没毛病��稳得一批！接口设计很规范，错误处理也到位。VERDICT:PASS"
不通过："哥们儿这个接口少了错误处理，用户传个空值直接炸了💥 建议加个参数校验。VERDICT:FAIL"

## 规则
- 回复控制在 200 字以内
- 不要使用 Markdown 标题格式
- 必须在最后一行包含 VERDICT:PASS 或 VERDICT:FAIL
"""

_VERDICT_PATTERN = re.compile(r"VERDICT:(PASS|FAIL)", re.IGNORECASE)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def review_task(
    task_id: str,
    task_name: str,
    task_goal: str,
    acceptance_criteria: list[str],
    agent_output: str,
    thread_id: str = "",
) -> tuple[bool, str]:
    """审核单个任务的执行结果。

    Args:
        task_id: 任务 ID
        task_name: 任务名称
        task_goal: 任务目标
        acceptance_criteria: 验收标准列表
        agent_output: Agent 的执行产出
        thread_id: event_bus 路由 ID

    Returns:
        (passed: bool, review_message: str)
    """
    criteria_text = "\n".join(f"  - {c}" for c in acceptance_criteria) if acceptance_criteria else "  - 无明确验收标准"

    user_prompt = (
        f"请审核以下任务的执行结果：\n\n"
        f"任务名称: {task_name}\n"
        f"任务目标: {task_goal}\n"
        f"验收标准:\n{criteria_text}\n\n"
        f"执行产出:\n{agent_output}\n\n"
        f"请给出你的审核结论。"
    )

    # 发送思考事件
    emit_event(thread_id, {
        "type": "agent_thinking",
        "timestamp": _ts(),
        "phase": "review",
        "agent": "reviewer",
    })

    llm = get_chat_model()
    resp = llm.invoke([
        SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    message = resp.content

    # 解析审核结论
    match = _VERDICT_PATTERN.search(message)
    passed = match.group(1).upper() == "PASS" if match else False

    # 发送审核结果事件
    status_emoji = "✅" if passed else "❌"
    emit_event(thread_id, {
        "type": "agent_output",
        "timestamp": _ts(),
        "phase": "review",
        "agent": "reviewer",
        "content": f"{status_emoji} @{task_name} 的审核结果：\n{message}",
        "metadata": {"task_id": task_id, "verdict": "pass" if passed else "fail"},
    })

    return passed, message
