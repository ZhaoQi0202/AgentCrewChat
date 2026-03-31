import pytest

from agentloom.skills.skill_import import (
    discover_skill_roots,
    parse_github_skill_url,
)


def test_parse_github_tree_url() -> None:
    o, r, ref, sp = parse_github_skill_url(
        "https://github.com/anthropics/skills/tree/main/skills"
    )
    assert o == "anthropics"
    assert r == "skills"
    assert ref == "main"
    assert sp == "skills"


def test_parse_github_repo_root() -> None:
    o, r, ref, sp = parse_github_skill_url("https://github.com/anthropics/skills")
    assert o == "anthropics"
    assert r == "skills"
    assert ref == "main"
    assert sp == ""


def test_discover_single_and_multi(tmp_path) -> None:
    one = tmp_path / "a"
    one.mkdir()
    (one / "SKILL.md").write_text("---\nname: a\n---\n", encoding="utf-8")
    assert discover_skill_roots(one) == [one.resolve()]

    root = tmp_path / "multi"
    root.mkdir()
    for n in ("x", "y"):
        d = root / n
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {n}\n---\n", encoding="utf-8")
    roots = discover_skill_roots(root)
    assert len(roots) == 2


def test_parse_rejects_non_github() -> None:
    with pytest.raises(ValueError):
        parse_github_skill_url("https://example.com/x")
