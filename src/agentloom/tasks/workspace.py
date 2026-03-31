import re
import subprocess
import time
from pathlib import Path

from agentloom.bootstrap import ensure_layout
from agentloom.paths import workspaces_dir


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "task"


def run_uv_venv(task_path: Path) -> None:
    subprocess.run(["uv", "venv"], cwd=task_path, check=True)


def create_task(name: str) -> Path:
    ensure_layout()
    slug = _slugify(name)
    ts = int(time.time() * 1000)
    dir_name = f"task_{ts}_{slug}"
    path = workspaces_dir() / dir_name
    path.mkdir(parents=True, exist_ok=False)
    run_uv_venv(path)
    return path


def list_tasks() -> list[Path]:
    ensure_layout()
    w = workspaces_dir()
    pat = re.compile(r"task_\d+_.+")
    tasks = [p for p in w.iterdir() if p.is_dir() and pat.fullmatch(p.name)]
    tasks.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
    return tasks
