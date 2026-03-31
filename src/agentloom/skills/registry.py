from pathlib import Path

from agentloom.config.loader import load_all
from agentloom.config.models import SkillEntry
from agentloom.paths import install_root


def task_skills_dir(task_workspace: Path) -> Path:
    return task_workspace.resolve() / ".agentloom" / "skills"


def list_task_skill_entries(task_workspace: Path) -> list[SkillEntry]:
    root = install_root().resolve()
    base = task_skills_dir(task_workspace)
    if not base.is_dir():
        return []
    out: list[SkillEntry] = []
    for d in sorted(base.iterdir()):
        if not d.is_dir() or not (d / "SKILL.md").is_file():
            continue
        try:
            rel = d.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        out.append(
            SkillEntry(
                id=d.name,
                skill_dir=rel,
                enabled=True,
                scope="task",
            )
        )
    return out


def merged_skills_for_agents(
    task_workspace: Path | None = None,
    *,
    config_root: Path | None = None,
) -> list[SkillEntry]:
    cfg = load_all(config_root)
    app = [s for s in cfg.skills if s.enabled and s.scope != "task"]
    by_id: dict[str, SkillEntry] = {s.id: s for s in app}
    if task_workspace is None:
        return list(by_id.values())
    for t in list_task_skill_entries(task_workspace):
        if t.enabled:
            by_id[t.id] = t
    return list(by_id.values())
