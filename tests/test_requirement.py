import json
from pathlib import Path

from agentloom.tasks.requirement import save_requirement, load_requirement


def test_save_and_load_roundtrip(tmp_path: Path):
    req = {
        "project_name": "天气查询",
        "core_goal": "做一个天气查询网站",
        "constraints": {
            "tech_stack": ["Python", "FastAPI"],
            "platform": "web",
            "timeline": None,
        },
        "success_criteria": ["能按城市查天气"],
        "features": [
            {"name": "城市搜索", "description": "按城市名搜天气", "priority": "must"}
        ],
        "additional_notes": None,
        "raw_conversation_summary": "用户想做一个天气网站。",
    }
    save_requirement(tmp_path, req)
    loaded = load_requirement(tmp_path)
    assert loaded == req


def test_load_missing_returns_none(tmp_path: Path):
    assert load_requirement(tmp_path) is None


def test_save_creates_json_file(tmp_path: Path):
    save_requirement(tmp_path, {"core_goal": "test"})
    assert (tmp_path / "requirement.json").exists()
