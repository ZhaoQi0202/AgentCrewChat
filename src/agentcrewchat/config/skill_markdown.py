import re
from pathlib import Path

from agentcrewchat.config.models import SkillEntry
from agentcrewchat.config.skill_paths import skill_markdown_path


def parse_skill_md_frontmatter(skill_md: Path) -> tuple[str | None, str | None]:
    if not skill_md.is_file():
        return None, None
    text = skill_md.read_text(encoding="utf-8")
    if not text.lstrip().startswith("---"):
        return None, None
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None, None
    fm = m.group(1)
    name_m = re.search(r"(?m)^name:\s*(.+?)\s*$", fm)
    desc_m = re.search(r"(?m)^description:\s*(.+?)\s*$", fm)
    name = name_m.group(1).strip().strip("\"'") if name_m else None
    desc = desc_m.group(1).strip().strip("\"'") if desc_m else None
    return name, desc


def resolve_skill_row(install_root: Path, entry: SkillEntry) -> tuple[str, str, str, str]:
    enabled = "是" if entry.enabled else "否"
    sd = entry.skill_dir.replace("\\", "/")
    name: str | None = None
    desc: str | None = None
    if sd:
        try:
            md = skill_markdown_path(install_root, sd)
            name, desc = parse_skill_md_frontmatter(md)
        except ValueError:
            pass
    if not name:
        name = entry.name or entry.id
    if not desc:
        desc = entry.description or "—"
    return enabled, name, desc, sd
