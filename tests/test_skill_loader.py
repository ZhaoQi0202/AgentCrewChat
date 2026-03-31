import json

import pytest

from agentloom.config.loader import delete_skill_entry, load_all, save_skill_entry
from agentloom.config.models import SkillEntry
from agentloom.paths import config_dir


def test_save_and_load_skill(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    root = config_dir()
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(
        json.dumps({"version": "1", "mcp_ids": [], "skill_ids": []}),
        encoding="utf-8",
    )
    e = SkillEntry(
        id="t1",
        name="Test",
        description="d",
        skill_dir="builtin_skills/x",
        enabled=False,
    )
    save_skill_entry(e)
    cfg = load_all()
    assert len(cfg.skills) == 1
    assert cfg.skills[0].id == "t1"
    assert cfg.skills[0].enabled is False
    assert cfg.skills[0].skill_dir == "builtin_skills/x"
    delete_skill_entry("t1")
    cfg2 = load_all()
    assert cfg2.skill_ids == []


def test_skill_path_rejects_escape(tmp_path):
    from agentloom.config.skill_paths import validate_skill_dir

    root = tmp_path / "app"
    root.mkdir()
    with pytest.raises(ValueError):
        validate_skill_dir(root, "../etc")


def test_ensure_builtin_seeds_when_skill_md_exists(monkeypatch, tmp_path):
    import json

    from agentloom.config import builtin_skills as bs
    from agentloom.bootstrap import ensure_layout

    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    res = tmp_path / "res"
    for name in ("find-skills", "skill-vetter"):
        d = res / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    monkeypatch.setattr(bs, "BUILTIN_RESOURCE_DIR", res)
    ensure_layout()
    assert (tmp_path / "data" / "skills_install" / "find-skills" / "SKILL.md").is_file()
    p = config_dir() / "skills" / "find-skills.json"
    assert p.is_file()
    assert json.loads(p.read_text(encoding="utf-8"))["skill_dir"].startswith(
        "data/skills_install/"
    )
