from __future__ import annotations

import asyncio
import json
import queue
import threading
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agentloom.graph.builder import build_graph
from agentloom.graph.stream_util import split_stream_chunk
from agentloom.config.loader import load_all
from langgraph.types import Command

router = APIRouter(tags=["graph"])

_sessions: dict[str, dict[str, Any]] = {}

_SENTINEL = object()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


_AGENT_LABELS: dict[str, str] = {
    "consultant": "需求分析师",
    "architect": "架构设计师",
    "hitl_blueprint": "方案审核员",
    "experts": "执行专家组",
    "reviewer": "质量审查员",
}


def _build_collect_system_prompt() -> str:
    """构建需求收集 agent 的 system prompt，包含工具信息。"""
    tools_info = ""
    try:
        cfg = load_all()
        if cfg.mcps:
            tools_info += "可用的 MCP 工具：\n"
            for entry in cfg.mcps:
                name = entry.name or entry.command or entry.id
                tools_info += f"- {name}\n"
        if cfg.skills:
            tools_info += "可用的技能：\n"
            for entry in cfg.skills:
                if entry.enabled:
                    desc = entry.description or ""
                    tools_info += f"- {entry.name or entry.id}: {desc}\n"
    except Exception:
        tools_info = "（暂无工具信息）"

    return (
        "你是需求分析师，在一个项目群聊中负责收集用户的真实需求。\n"
        "规则：\n"
        "- 回复必须控制在100-200个字符以内\n"
        "- 用简洁友好的群聊对话风格\n"
        "- 先做简短自我介绍，然后顺势询问用户想做什么\n"
        "- 根据用户回复判断需求是否足够清晰\n"
        "- 如果需要补充信息，继续提问（每次只问一个问题）\n"
        "- 如果需求已经明确，回复格式必须是：\n"
        "  「需求已明确：<简短总结>。是否启动项目？」\n"
        "- 如果判断当前工具无法完成需求，如实告知用户\n\n"
        f"当前可用的工具和技能：\n{tools_info}"
    )


async def _handle_collect(websocket: WebSocket, session_id: str, msg: dict) -> None:
    """处理需求收集多轮对话。"""
    from agentloom.llm.factory import get_chat_model
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    session = _sessions.get(session_id)

    if session is None or session.get("mode") != "collect":
        # 首次：发送需求分析师加入群聊 + 自我介绍
        system_prompt = _build_collect_system_prompt()

        await websocket.send_json({
            "type": "phase_start",
            "timestamp": _ts(),
            "phase": "consultant",
            "agent": "consultant",
            "content": "需求分析师 加入群聊",
        })
        await websocket.send_json({
            "type": "agent_thinking",
            "timestamp": _ts(),
            "phase": "consultant",
            "agent": "consultant",
            "content": "",
        })

        llm = get_chat_model()
        resp = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="（用户刚创建了项目组，请自我介绍并询问需求）"),
        ])
        reply = resp.content

        await websocket.send_json({
            "type": "agent_output",
            "timestamp": _ts(),
            "phase": "consultant",
            "agent": "consultant",
            "content": reply,
        })

        history: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "（用户刚创建了项目组，请自我介绍并询问需求）"},
            {"role": "assistant", "content": reply},
        ]
        _sessions[session_id] = {
            "mode": "collect",
            "history": history,
            "system_prompt": system_prompt,
        }

    else:
        # 后续轮次：用户回复
        user_msg = msg.get("content", "")
        history = session["history"]
        system_prompt = session["system_prompt"]

        history.append({"role": "user", "content": user_msg})

        await websocket.send_json({
            "type": "agent_thinking",
            "timestamp": _ts(),
            "phase": "consultant",
            "agent": "consultant",
            "content": "",
        })

        llm = get_chat_model()
        messages = [SystemMessage(content=system_prompt)]
        for h in history[1:]:  # skip system
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                messages.append(AIMessage(content=h["content"]))

        resp = llm.invoke(messages)
        reply = resp.content

        await websocket.send_json({
            "type": "agent_output",
            "timestamp": _ts(),
            "phase": "consultant",
            "agent": "consultant",
            "content": reply,
        })

        history.append({"role": "assistant", "content": reply})
        session["history"] = history


def _iter_graph_events(graph: Any, input_obj: Any, cfg: dict) -> Iterator[dict[str, Any]]:
    # Before starting stream, predict the first node and send thinking
    try:
        st = graph.get_state(cfg)
        for nxt_node in (st.next or []):
            label = _AGENT_LABELS.get(nxt_node, nxt_node)
            yield {
                "type": "phase_start",
                "timestamp": _ts(),
                "phase": nxt_node,
                "agent": nxt_node,
                "content": f"{label} 加入群聊",
            }
            yield {
                "type": "agent_thinking",
                "timestamp": _ts(),
                "phase": nxt_node,
                "agent": nxt_node,
                "content": "",
            }
    except Exception:
        pass  # First start has no state yet

    for chunk in graph.stream(input_obj, cfg, stream_mode="updates"):
        parts, has_interrupt = split_stream_chunk(chunk)
        for node, upd in parts:
            phase = upd.get("phase", node)
            content = upd.get("message") or json.dumps(upd, ensure_ascii=False, default=str)
            yield {
                "type": "agent_output",
                "timestamp": _ts(),
                "phase": phase,
                "agent": node,
                "content": content,
            }
            # After each node completes, check for next node and send thinking
            try:
                st = graph.get_state(cfg)
                for nxt_node in (st.next or []):
                    if nxt_node == node:
                        continue
                    label = _AGENT_LABELS.get(nxt_node, nxt_node)
                    yield {
                        "type": "phase_start",
                        "timestamp": _ts(),
                        "phase": nxt_node,
                        "agent": nxt_node,
                        "content": f"{label} 加入群聊",
                    }
                    yield {
                        "type": "agent_thinking",
                        "timestamp": _ts(),
                        "phase": nxt_node,
                        "agent": nxt_node,
                        "content": "",
                    }
            except Exception:
                pass
        if has_interrupt:
            st = graph.get_state(cfg)
            nxt = st.next[0] if st.next else ""
            label = _AGENT_LABELS.get(nxt, nxt)
            interrupt_msg = f"{label} 等待人工审核"
            yield {
                "type": "hitl_interrupt",
                "timestamp": _ts(),
                "phase": nxt,
                "agent": nxt,
                "content": interrupt_msg,
            }
            return
    yield {
        "type": "task_complete",
        "timestamp": _ts(),
        "content": "项目执行完成",
    }


async def _pump_graph_to_ws(
    websocket: WebSocket, graph: Any, input_obj: Any, cfg: dict,
    session_id: str = "",
) -> bool:
    """Returns True if completed normally, False if paused."""
    q: queue.Queue[Any] = queue.Queue()

    def worker() -> None:
        try:
            for ev in _iter_graph_events(graph, input_obj, cfg):
                q.put(ev)
        except BaseException as exc:
            q.put({
                "type": "error",
                "timestamp": _ts(),
                "content": str(exc),
            })
        finally:
            q.put(_SENTINEL)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        session = _sessions.get(session_id, {})
        if session.get("paused"):
            return False
        try:
            item = await asyncio.wait_for(asyncio.to_thread(q.get), timeout=0.5)
        except asyncio.TimeoutError:
            continue
        if item is _SENTINEL:
            break
        await websocket.send_json(item)
    return True


@router.websocket("/ws/graph/{session_id}")
async def graph_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    graph = None
    cfg: dict[str, Any] = {}
    thread_id = ""

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            if action == "collect":
                await _handle_collect(websocket, session_id, msg)

            elif action == "confirm_start":
                # User confirmed to start project after requirement collection
                session = _sessions.get(session_id)
                collected = ""
                if session and session.get("mode") == "collect":
                    history = session.get("history", [])
                    user_msgs = [h["content"] for h in history if h["role"] == "user" and not h["content"].startswith("（")]
                    collected = "\n".join(user_msgs)
                    _sessions.pop(session_id, None)

                task_id = msg.get("task_id", "api-task")
                user_request = collected or msg.get("user_request", task_id)
                thread_id = str(uuid.uuid4())
                cfg = {"configurable": {"thread_id": thread_id}}
                graph = build_graph()

                await websocket.send_json({
                    "type": "phase_start",
                    "timestamp": _ts(),
                    "phase": "pending",
                    "content": "项目已启动，Agent 正在就位…",
                })

                await _pump_graph_to_ws(
                    websocket, graph,
                    {"task_id": task_id, "user_request": user_request},
                    cfg, session_id=session_id,
                )

                _sessions[session_id] = {"graph": graph, "cfg": cfg}

            elif action == "start":
                task_id = msg.get("task_id", "api-task")
                user_request = msg.get("user_request", task_id)
                thread_id = str(uuid.uuid4())
                cfg = {"configurable": {"thread_id": thread_id}}
                graph = build_graph()

                await websocket.send_json({
                    "type": "phase_start",
                    "timestamp": _ts(),
                    "phase": "pending",
                    "content": "项目已启动，Agent 正在就位…",
                })

                await _pump_graph_to_ws(
                    websocket,
                    graph,
                    {"task_id": task_id, "user_request": user_request},
                    cfg,
                    session_id=session_id,
                )

                _sessions[session_id] = {"graph": graph, "cfg": cfg}

            elif action == "resume":
                feedback = msg.get("feedback", {})
                session = _sessions.get(session_id)
                if session is None or session["graph"] is None:
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": _ts(),
                        "content": "会话不存在或已结束",
                    })
                    continue

                graph = session["graph"]
                cfg = session["cfg"]
                resume_input = Command(resume=feedback if feedback else {})

                session["paused"] = False
                await _pump_graph_to_ws(websocket, graph, resume_input, cfg, session_id=session_id)

            elif action == "pause":
                session = _sessions.get(session_id)
                if session:
                    session["paused"] = True
                await websocket.send_json({
                    "type": "phase_complete",
                    "timestamp": _ts(),
                    "content": "项目已暂停",
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "timestamp": _ts(),
                    "content": f"未知操作: {action}",
                })

    except WebSocketDisconnect:
        _sessions.pop(session_id, None)
    except Exception as exc:
        try:
            await websocket.send_json({
                "type": "error",
                "timestamp": _ts(),
                "content": str(exc),
            })
        except Exception:
            pass
        _sessions.pop(session_id, None)
