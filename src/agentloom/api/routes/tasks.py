from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agentloom.tasks.workspace import create_task, list_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskInfo(BaseModel):
    id: str
    name: str
    path: str
    modified_at: str


class TaskCreateRequest(BaseModel):
    name: str


def _parse_task_dir(path) -> TaskInfo:
    """从任务目录名解析信息。格式: task_{timestamp}_{slug}"""
    dir_name = path.name
    m = re.match(r"task_(\d+)_(.+)", dir_name)
    if m:
        ts_ms = int(m.group(1))
        slug = m.group(2)
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    else:
        slug = dir_name
        stat = path.stat()
        dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    return TaskInfo(
        id=dir_name,
        name=slug.replace("-", " ").title(),
        path=str(path),
        modified_at=dt.isoformat(),
    )


@router.get("")
async def get_tasks() -> list[TaskInfo]:
    paths = list_tasks()
    return [_parse_task_dir(p) for p in paths]


@router.post("")
async def new_task(body: TaskCreateRequest) -> TaskInfo:
    try:
        path = create_task(body.name)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    return _parse_task_dir(path)
