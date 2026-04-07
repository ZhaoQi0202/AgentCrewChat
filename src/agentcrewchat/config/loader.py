import json
import shutil
from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from agentcrewchat.paths import config_dir

from .manifest import load_manifest, write_manifest_dict
from .models import ConfigValidationError, LoadedConfig, McpEntry, ShellPolicy, SkillEntry


def iter_skill_files(config_root: Path | None = None) -> Iterator[Path]:
    base = config_dir() if config_root is None else config_root
    skills_dir = base / "skills"
    if not skills_dir.is_dir():
        return
    yield from sorted(skills_dir.glob("*.json"))


def iter_mcp_files(config_root: Path | None = None) -> Iterator[Path]:
    base = config_dir() if config_root is None else config_root
    mcp_dir = base / "mcp"
    if not mcp_dir.is_dir():
        return
    yield from sorted(mcp_dir.glob("*.json"))


def _load_mcp_entry(path: Path) -> McpEntry:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigValidationError(f"mcp file must be a JSON object: {path}")
    stem_id = path.stem
    if "id" not in raw:
        raw = {**raw, "id": stem_id}
    try:
        return McpEntry.model_validate(raw)
    except ValidationError as e:
        raise ConfigValidationError(str(e)) from e


def _load_skill_entry(path: Path) -> SkillEntry:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigValidationError(f"skill file must be a JSON object: {path}")
    stem_id = path.stem
    if "id" not in raw:
        raw = {**raw, "id": stem_id}
    try:
        return SkillEntry.model_validate(raw)
    except ValidationError as e:
        raise ConfigValidationError(str(e)) from e


def save_skill_entry(entry: SkillEntry, config_root: Path | None = None) -> None:
    base = config_dir() if config_root is None else config_root
    skills_dir = base / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(base)
    payload = entry.model_dump(mode="json", exclude_none=True)
    path = skills_dir / f"{entry.id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ids = list(manifest.skill_ids)
    if entry.id not in ids:
        ids.append(entry.id)
    updated = manifest.model_copy(update={"skill_ids": ids})
    write_manifest_dict(updated.model_dump(mode="json"), config_root=base)


def delete_skill_entry(
    skill_id: str,
    config_root: Path | None = None,
    *,
    install_root_for_payload: Path | None = None,
) -> None:
    base = config_dir() if config_root is None else config_root
    path = base / "skills" / f"{skill_id}.json"
    skill_dir_rel = ""
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                skill_dir_rel = str(raw.get("skill_dir") or "")
        except (json.JSONDecodeError, OSError):
            pass
        path.unlink()
    manifest = load_manifest(base)
    ids = [x for x in manifest.skill_ids if x != skill_id]
    updated = manifest.model_copy(update={"skill_ids": ids})
    write_manifest_dict(updated.model_dump(mode="json"), config_root=base)
    if (
        install_root_for_payload
        and skill_dir_rel.replace("\\", "/").startswith("data/skills_install/")
    ):
        payload = (install_root_for_payload / skill_dir_rel.replace("\\", "/")).resolve()
        try:
            payload.relative_to(install_root_for_payload.resolve())
        except ValueError:
            return
        if payload.is_dir():
            shutil.rmtree(payload, ignore_errors=True)


def save_mcp_entry(entry: McpEntry, config_root: Path | None = None) -> None:
    base = config_dir() if config_root is None else config_root
    mcp_dir = base / "mcp"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(base)
    payload = entry.model_dump(mode="json", exclude_none=True)
    path = mcp_dir / f"{entry.id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ids = list(manifest.mcp_ids)
    if entry.id not in ids:
        ids.append(entry.id)
    updated = manifest.model_copy(update={"mcp_ids": ids})
    write_manifest_dict(updated.model_dump(mode="json"), config_root=base)


def load_all(config_root: Path | None = None) -> LoadedConfig:
    base = config_dir() if config_root is None else config_root
    try:
        manifest = load_manifest(base)
    except ConfigValidationError:
        raise
    mcps: list[McpEntry] = []
    for p in iter_mcp_files(base):
        mcps.append(_load_mcp_entry(p))
    by_id: dict[str, SkillEntry] = {}
    for p in iter_skill_files(base):
        e = _load_skill_entry(p)
        by_id[e.id] = e
    skills: list[SkillEntry] = []
    seen: set[str] = set()
    for sid in manifest.skill_ids:
        if sid in by_id:
            skills.append(by_id[sid])
        else:
            skills.append(SkillEntry(id=sid))
        seen.add(sid)
    for eid in sorted(by_id.keys() - seen):
        skills.append(by_id[eid])
    shell = manifest.shell if manifest.shell is not None else ShellPolicy()
    return LoadedConfig(
        version=manifest.version,
        mcp_ids=list(manifest.mcp_ids),
        skill_ids=list(manifest.skill_ids),
        mcps=mcps,
        skills=skills,
        shell=shell,
    )
