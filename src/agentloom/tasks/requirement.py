from __future__ import annotations

import json
from pathlib import Path

REQUIREMENT_FILE = "requirement.json"


def save_requirement(task_path: Path, req: dict) -> Path:
    """将结构化需求保存到 workspace 目录。"""
    fp = task_path / REQUIREMENT_FILE
    fp.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


def load_requirement(task_path: Path) -> dict | None:
    """从 workspace 加载需求，不存在则返回 None。"""
    fp = task_path / REQUIREMENT_FILE
    if not fp.exists():
        return None
    return json.loads(fp.read_text(encoding="utf-8"))
