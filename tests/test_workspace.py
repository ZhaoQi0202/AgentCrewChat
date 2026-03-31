import os
import re
import time

import pytest

from agentloom.paths import workspaces_dir


@pytest.fixture
def isolated_root(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    yield tmp_path


def test_create_task_dir_name_format(isolated_root, monkeypatch):
    from agentloom.tasks import workspace as ws

    monkeypatch.setattr(ws, "run_uv_venv", lambda _p: None)

    from agentloom.tasks.workspace import create_task

    p = create_task("my job")
    assert p.is_dir()
    assert p.parent == workspaces_dir()
    assert re.fullmatch(r"task_\d+_.+", p.name), p.name
    assert "my" in p.name and "job" in p.name.replace("-", " ")


def test_create_task_slugifies(isolated_root, monkeypatch):
    from agentloom.tasks import workspace as ws

    monkeypatch.setattr(ws, "run_uv_venv", lambda _p: None)
    from agentloom.tasks.workspace import create_task

    p = create_task("Hello World!!!")
    assert re.fullmatch(r"task_\d+_.+", p.name)
    assert "hello" in p.name
    assert "world" in p.name


def test_list_tasks_newest_first(isolated_root, monkeypatch):
    from agentloom.tasks import workspace as ws

    monkeypatch.setattr(ws, "run_uv_venv", lambda _p: None)
    from agentloom.tasks.workspace import create_task, list_tasks

    workspaces_dir().mkdir(parents=True, exist_ok=True)
    older = workspaces_dir() / "task_1111111111111111111_old"
    newer = workspaces_dir() / "task_2222222222222222222_new"
    older.mkdir()
    newer.mkdir()
    t0 = time.time() - 100
    t1 = time.time()
    os.utime(older, (t0, t0))
    os.utime(newer, (t1, t1))

    tasks = list_tasks()
    assert tasks[0] == newer
    assert tasks[1] == older

    create_task("z")
    tasks2 = list_tasks()
    assert tasks2[0].name.startswith("task_")
    assert "z" in tasks2[0].name
