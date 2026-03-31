import json
import shutil
from pathlib import Path

from pydantic import ValidationError

from agentloom.config.loader import save_skill_entry
from agentloom.config.models import SkillEntry
from agentloom.paths import config_dir, install_root

BUILTIN_RESOURCE_DIR: Path = (
    Path(__file__).resolve().parent.parent / "resources" / "builtin_skills"
)
DEFAULT_BUILTIN_IDS: tuple[str, ...] = ("find-skills", "skill-vetter")


def ensure_builtin_skill_configs() -> None:
    base = config_dir()
    root = install_root().resolve()
    base.mkdir(parents=True, exist_ok=True)
    data_root = root / "data" / "skills_install"
    data_root.mkdir(parents=True, exist_ok=True)
    for sid in DEFAULT_BUILTIN_IDS:
        src = BUILTIN_RESOURCE_DIR / sid
        if not (src / "SKILL.md").is_file():
            continue
        dest = data_root / sid
        json_p = base / "skills" / f"{sid}.json"
        prev: SkillEntry | None = None
        if json_p.is_file():
            try:
                raw = json.loads(json_p.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    prev = SkillEntry.model_validate(raw)
            except (json.JSONDecodeError, ValidationError):
                prev = None
        sd_old = (prev.skill_dir if prev else "").replace("\\", "/")
        need_copy = not (dest / "SKILL.md").is_file() or sd_old.startswith(
            "builtin_skills/"
        )
        if need_copy:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        rel = dest.relative_to(root).as_posix()
        if not json_p.is_file():
            save_skill_entry(
                SkillEntry(
                    id=sid,
                    skill_dir=rel,
                    enabled=True,
                    scope="app",
                )
            )
        elif prev is not None and sd_old.startswith("builtin_skills/"):
            save_skill_entry(prev.model_copy(update={"skill_dir": rel, "scope": "app"}))
