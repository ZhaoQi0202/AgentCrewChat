from __future__ import annotations

import json
from pathlib import Path

BLUEPRINT_FILE = "blueprint.json"


def save_blueprint(task_path: Path, blueprint: dict) -> Path:
    """将 DAG 任务规划保存到 workspace 目录。"""
    fp = task_path / BLUEPRINT_FILE
    fp.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


def load_blueprint(task_path: Path) -> dict | None:
    """从 workspace 加载 blueprint，不存在则返回 None。"""
    fp = task_path / BLUEPRINT_FILE
    if not fp.exists():
        return None
    return json.loads(fp.read_text(encoding="utf-8"))
