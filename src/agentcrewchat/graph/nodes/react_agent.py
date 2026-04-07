"""ReAct Agent 执行器：思考→调用工具→观察→重复，直到任务完成。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from agentcrewchat.graph.event_bus import emit_event
from agentcrewchat.llm.factory import get_chat_model

MAX_ITERATIONS = 15


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_tool_result(stdout: str) -> str:
    """截断过长的工具输出。"""
    if len(stdout) > 2000:
        return stdout[:1000] + "\n...(输出截断)...\n" + stdout[-500:]
    return stdout


def run_react_agent(
    task_id: str,
    task_name: str,
    task_goal: str,
    acceptance_criteria: list[str],
    tools: list[BaseTool],
    workspace_path: str,
    thread_id: str = "",
    max_iterations: int = MAX_ITERATIONS,
    retry_feedback: str | None = None,
) -> dict[str, Any]:
    """运行一个 ReAct Agent 完成指定任务。

    通过 event_bus 实时推送执行进展到前端。

    返回:
        {
            "task_id": str,
            "task_name": str,
            "status": "completed" | "max_iterations" | "error",
            "output": str,  # Agent 的最终回复
            "tool_calls_count": int,
        }
    """
    criteria_text = "\n".join(f"  - {c}" for c in acceptance_criteria) if acceptance_criteria else "  - 无特定标准"

    system_prompt = (
        f"你是一个执行专家，正在项目群聊中完成分配给你的任务。\n\n"
        f"## 你的任务\n"
        f"任务名称: {task_name}\n"
        f"任务目标: {task_goal}\n"
        f"验收标准:\n{criteria_text}\n\n"
        f"## 工作目录\n"
        f"{workspace_path}\n\n"
        f"## 工作规则\n"
        f"1. 使用提供的工具来完成任务\n"
        f"2. 每次只做一步操作，观察结果后再决定下一步\n"
        f"3. 完成任务后，用简短活泼的语气总结你做了什么\n"
        f"4. 如果遇到问题，先尝试解决，实在不行再说明情况\n"
        f"5. 不要使用 Markdown 标题格式，像在工作群里汇报一样说话\n"
    )

    if retry_feedback:
        system_prompt += (
            f"\n## ⚠️ 重要：上一次执行未通过审核\n"
            f"审核反馈：{retry_feedback}\n"
            f"请根据反馈改进你的实现。\n"
        )

    messages: list = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请开始执行任务「{task_name}」"),
    ]

    llm = get_chat_model()
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    tool_map = {t.name: t for t in tools}
    total_tool_calls = 0

    # 发送开始事件
    start_msg = (
        f"收到审核反馈，重新修改「{task_name}」🔧" if retry_feedback
        else f"收到任务「{task_name}」，马上开始搞！💪"
    )
    emit_event(thread_id, {
        "type": "agent_output",
        "timestamp": _ts(),
        "phase": "experts",
        "agent": "experts",
        "content": start_msg,
        "metadata": {"agent_name": task_name, "task_id": task_id},
    })

    for iteration in range(max_iterations):
        # 发送思考事件
        emit_event(thread_id, {
            "type": "agent_thinking",
            "timestamp": _ts(),
            "phase": "experts",
            "agent": "experts",
            "metadata": {"agent_name": task_name, "task_id": task_id},
        })

        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            emit_event(thread_id, {
                "type": "agent_output",
                "timestamp": _ts(),
                "phase": "experts",
                "agent": "experts",
                "content": f"呃...出了点问题: {e}",
                "metadata": {"agent_name": task_name, "task_id": task_id},
            })
            return {
                "task_id": task_id,
                "task_name": task_name,
                "status": "error",
                "output": str(e),
                "tool_calls_count": total_tool_calls,
            }

        messages.append(response)

        # 检查是否有工具调用
        if not hasattr(response, "tool_calls") or not response.tool_calls:
            # Agent 完成了，输出最终回复
            final_output = response.content or "任务完成"
            emit_event(thread_id, {
                "type": "agent_output",
                "timestamp": _ts(),
                "phase": "experts",
                "agent": "experts",
                "content": final_output,
                "metadata": {"agent_name": task_name, "task_id": task_id},
            })
            return {
                "task_id": task_id,
                "task_name": task_name,
                "status": "completed",
                "output": final_output,
                "tool_calls_count": total_tool_calls,
            }

        # 执行工具调用
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            total_tool_calls += 1

            # 通知正在使用工具
            args_preview = json.dumps(tool_args, ensure_ascii=False)
            if len(args_preview) > 200:
                args_preview = args_preview[:200] + "..."
            emit_event(thread_id, {
                "type": "agent_output",
                "timestamp": _ts(),
                "phase": "experts",
                "agent": "experts",
                "content": f"🔧 调用 {tool_name}: {args_preview}",
                "metadata": {"agent_name": task_name, "task_id": task_id, "tool_call": True},
            })

            # 执行工具
            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                try:
                    result = tool_fn.invoke(tool_args)
                    result_str = _format_tool_result(str(result))
                except Exception as e:
                    result_str = f"工具执行失败: {e}"
            else:
                result_str = f"未知工具: {tool_name}"

            messages.append(ToolMessage(
                content=result_str,
                tool_call_id=tool_call["id"],
            ))

    # 达到最大迭代次数
    emit_event(thread_id, {
        "type": "agent_output",
        "timestamp": _ts(),
        "phase": "experts",
        "agent": "experts",
        "content": f"任务「{task_name}」达到最大执行步数({max_iterations})，先到这里吧",
        "metadata": {"agent_name": task_name, "task_id": task_id},
    })
    return {
        "task_id": task_id,
        "task_name": task_name,
        "status": "max_iterations",
        "output": messages[-1].content if messages else "达到最大迭代次数",
        "tool_calls_count": total_tool_calls,
    }
