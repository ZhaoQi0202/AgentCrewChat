from pathlib import Path

from agentloom.tasks.blueprint import save_blueprint, load_blueprint


def test_save_and_load_roundtrip(tmp_path: Path):
    bp = {
        "tasks": [
            {
                "id": "t1",
                "name": "实现后端 API",
                "goal": "创建 /api/weather 端点",
                "acceptance_criteria": ["返回 JSON", "错误处理"],
                "tools": ["shell", "python"],
                "depends_on": [],
            },
            {
                "id": "t2",
                "name": "实现前端页面",
                "goal": "创建天气查询页面",
                "acceptance_criteria": ["可输入城市名"],
                "tools": ["shell"],
                "depends_on": ["t1"],
            },
        ]
    }
    save_blueprint(tmp_path, bp)
    loaded = load_blueprint(tmp_path)
    assert loaded == bp
    assert len(loaded["tasks"]) == 2
    assert loaded["tasks"][1]["depends_on"] == ["t1"]


def test_load_missing_returns_none(tmp_path: Path):
    assert load_blueprint(tmp_path) is None


def test_save_creates_json_file(tmp_path: Path):
    save_blueprint(tmp_path, {"tasks": []})
    assert (tmp_path / "blueprint.json").exists()
