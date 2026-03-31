import json

from agentloom.config.loader import save_skill_entry
from agentloom.config.models import SkillEntry
from agentloom.paths import config_dir
from agentloom.skills.registry import merged_skills_for_agents, list_task_skill_entries


def test_merged_app_and_task(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    cr = config_dir()
    cr.mkdir(parents=True)
    (cr / "manifest.json").write_text(
        json.dumps({"version": "1", "mcp_ids": [], "skill_ids": ["a"]}),
        encoding="utf-8",
    )
    save_skill_entry(
        SkillEntry(
            id="a",
            skill_dir="data/skills_install/x",
            enabled=True,
            scope="app",
        )
    )
    task = tmp_path / "workspaces" / "t1"
    sk = task / ".agentloom" / "skills" / "a"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text("---\nname: task-a\n---\n", encoding="utf-8")
    merged = merged_skills_for_agents(task_workspace=task)
    ids = {e.id: e.skill_dir for e in merged}
    assert "a" in ids
    assert ".agentloom/skills/a" in ids["a"].replace("\\", "/")


def test_list_task_only(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    task = tmp_path / "workspaces" / "t2"
    sk = task / ".agentloom" / "skills" / "k1"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text("---\nname: k\n---\n", encoding="utf-8")
    lst = list_task_skill_entries(task)
    assert len(lst) == 1
    assert lst[0].id == "k1"
    assert lst[0].scope == "task"
