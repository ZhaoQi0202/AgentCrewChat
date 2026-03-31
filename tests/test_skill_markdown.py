from pathlib import Path

from agentloom.config.models import SkillEntry
from agentloom.config.skill_markdown import parse_skill_md_frontmatter, resolve_skill_row


def test_parse_frontmatter(tmp_path: Path) -> None:
    p = tmp_path / "SKILL.md"
    p.write_text(
        "---\nname: My Skill\ndescription: One line desc\n---\n\n# body\n",
        encoding="utf-8",
    )
    n, d = parse_skill_md_frontmatter(p)
    assert n == "My Skill"
    assert d == "One line desc"


def test_resolve_row_fallback_id(tmp_path: Path) -> None:
    root = tmp_path
    e = SkillEntry(id="only-id", skill_dir="")
    en, name, desc, sd = resolve_skill_row(root, e)
    assert en == "是"
    assert name == "only-id"
    assert desc == "—"
    assert sd == ""
