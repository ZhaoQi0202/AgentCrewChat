"""DAG Orchestrator：按依赖关系调度多个 ReAct Agent 执行任务。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentloom.graph.event_bus import emit_event
from agentloom.graph.nodes.react_agent import run_react_agent
from agentloom.tools.tool_registry import create_tools_for_task


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _topological_sort(tasks: list[dict]) -> list[list[dict]]:
    """将任务按 DAG 依赖关系分层排序。

    返回: [[第一层任务], [第二层任务], ...]
    每层内的任务互相无依赖，可以并行执行。
    """
    task_map = {t["id"]: t for t in tasks}
    in_degree = {t["id"]: 0 for t in tasks}
    dependents: dict[str, list[str]] = {t["id"]: [] for t in tasks}

    for t in tasks:
        for dep in t.get("depends_on", []):
            if dep in task_map:
                in_degree[t["id"]] += 1
                dependents[dep].append(t["id"])

    layers = []
    remaining = set(in_degree.keys())

    while remaining:
        # 找出入度为 0 的任务
        ready = [tid for tid in remaining if in_degree[tid] == 0]
        if not ready:
            # 有循环依赖，把剩余的都放一层
            ready = list(remaining)
        layer = [task_map[tid] for tid in ready]
        layers.append(layer)
        for tid in ready:
            remaining.discard(tid)
            for dep_id in dependents.get(tid, []):
                in_degree[dep_id] -= 1

    return layers


def _save_task_output(workspace: Path, task_id: str, result: dict) -> None:
    """保存单个任务的执行结果到 workspace。"""
    output_dir = workspace / "task_outputs"
    output_dir.mkdir(exist_ok=True)
    fp = output_dir / f"{task_id}.json"
    fp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def run_orchestration(
    blueprint: dict,
    workspace: Path,
    thread_id: str = "",
) -> list[dict[str, Any]]:
    """按 DAG 依赖关系执行所有任务。

    Args:
        blueprint: 架构师生成的任务规划（含 tasks 列表）
        workspace: 项目组工作目录
        thread_id: event_bus 路由 ID

    Returns:
        所有任务的执行结果列表
    """
    tasks = blueprint.get("tasks", [])
    if not tasks:
        emit_event(thread_id, {
            "type": "agent_output",
            "timestamp": _ts(),
            "phase": "experts",
            "agent": "experts",
            "content": "蓝图里没有任务，没啥好干的 🤷",
        })
        return []

    layers = _topological_sort(tasks)
    all_results: list[dict] = []
    completed_tasks: dict[str, dict] = {}

    emit_event(thread_id, {
        "type": "phase_start",
        "timestamp": _ts(),
        "phase": "experts",
        "agent": "experts",
        "content": f"开始执行！一共 {len(tasks)} 个任务，分 {len(layers)} 层依次推进",
    })

    for layer_idx, layer in enumerate(layers):
        if len(layer) > 1:
            names = "、".join(t["name"] for t in layer)
            emit_event(thread_id, {
                "type": "agent_output",
                "timestamp": _ts(),
                "phase": "experts",
                "agent": "experts",
                "content": f"📋 第 {layer_idx + 1} 层：{names}（这些任务可以并行，当前逐个执行）",
            })

        for task in layer:
            task_id = task["id"]
            task_name = task.get("name", task_id)
            task_goal = task.get("goal", "")
            criteria = task.get("acceptance_criteria", [])
            tool_ids = task.get("tools", [])
            deps = task.get("depends_on", [])

            # @上游 Agent 互动
            if deps:
                dep_names = [completed_tasks[d]["task_name"] for d in deps if d in completed_tasks]
                if dep_names:
                    mentions = "、".join(f"@{n}" for n in dep_names)
                    emit_event(thread_id, {
                        "type": "agent_output",
                        "timestamp": _ts(),
                        "phase": "experts",
                        "agent": "experts",
                        "content": f"{mentions} 的产出我看到了，接下来轮到我「{task_name}」了！",
                        "metadata": {"agent_name": task_name, "task_id": task_id},
                    })

            # 创建工具并执行
            tools = create_tools_for_task(tool_ids, workspace)
            result = run_react_agent(
                task_id=task_id,
                task_name=task_name,
                task_goal=task_goal,
                acceptance_criteria=criteria,
                tools=tools,
                workspace_path=str(workspace),
                thread_id=thread_id,
            )

            completed_tasks[task_id] = result
            all_results.append(result)

            # 保存单个任务结果
            _save_task_output(workspace, task_id, result)

            # 通知下游
            status_emoji = "✅" if result["status"] == "completed" else "⚠️"
            emit_event(thread_id, {
                "type": "agent_output",
                "timestamp": _ts(),
                "phase": "experts",
                "agent": "experts",
                "content": f"{status_emoji} 任务「{task_name}」执行完毕（状态: {result['status']}，工具调用: {result['tool_calls_count']}次）",
                "metadata": {"agent_name": task_name, "task_id": task_id},
            })

    # 汇总
    completed_count = sum(1 for r in all_results if r["status"] == "completed")
    emit_event(thread_id, {
        "type": "agent_output",
        "timestamp": _ts(),
        "phase": "experts",
        "agent": "experts",
        "content": f"🎯 所有任务执行完毕！{completed_count}/{len(tasks)} 个任务成功完成",
    })

    return all_results
