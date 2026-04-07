from pathlib import Path


def validate_skill_dir(install_root: Path, skill_dir: str) -> Path:
    s = skill_dir.strip().replace("\\", "/")
    parts = [p for p in s.split("/") if p]
    if not parts or ".." in parts:
        raise ValueError("技能目录须为非空相对路径且不含 ..")
    root = install_root.resolve()
    target = root.joinpath(*parts).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("技能目录须位于安装根目录下") from None
    return target


def skill_markdown_path(install_root: Path, skill_dir: str) -> Path:
    return validate_skill_dir(install_root, skill_dir) / "SKILL.md"
