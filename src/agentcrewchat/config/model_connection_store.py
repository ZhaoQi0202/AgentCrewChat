import json
import re
import uuid
from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from agentcrewchat.paths import config_dir

from .manifest import load_manifest, write_manifest_dict
from .models import ConfigValidationError, ModelConnectionEntry


def iter_model_connection_files(config_root: Path | None = None) -> Iterator[Path]:
    base = config_dir() if config_root is None else config_root
    d = base / "model_connections"
    if not d.is_dir():
        return
    yield from sorted(d.glob("*.json"))


def _load_entry(path: Path) -> ModelConnectionEntry:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigValidationError(f"model connection must be JSON object: {path}")
    stem = path.stem
    if "id" not in raw:
        raw = {**raw, "id": stem}
    try:
        return ModelConnectionEntry.model_validate(raw)
    except ValidationError as e:
        raise ConfigValidationError(str(e)) from e


def load_model_connection(
    connection_id: str, config_root: Path | None = None
) -> ModelConnectionEntry | None:
    base = config_dir() if config_root is None else config_root
    path = base / "model_connections" / f"{connection_id}.json"
    if not path.is_file():
        return None
    return _load_entry(path)


def allocate_connection_id(name: str, existing: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower() or "connection"
    if len(base) > 48:
        base = base[:48]
    cand = base
    if cand not in existing:
        return cand
    for _ in range(24):
        cand = f"{base}-{uuid.uuid4().hex[:6]}"
        if cand not in existing:
            return cand
    return f"{base}-{uuid.uuid4().hex[:12]}"


def list_model_connections(config_root: Path | None = None) -> list[ModelConnectionEntry]:
    base = config_dir() if config_root is None else config_root
    manifest = load_manifest(base)
    by_id: dict[str, ModelConnectionEntry] = {}
    for p in iter_model_connection_files(base):
        e = _load_entry(p)
        by_id[e.id] = e
    out: list[ModelConnectionEntry] = []
    seen: set[str] = set()
    for cid in manifest.model_connection_ids:
        if cid in by_id:
            out.append(by_id[cid])
            seen.add(cid)
        else:
            out.append(
                ModelConnectionEntry(
                    id=cid,
                    name=cid,
                    provider="openai_compatible",
                    model="",
                    api_key="",
                    enabled=False,
                )
            )
    for eid in sorted(by_id.keys() - seen):
        out.append(by_id[eid])
    return out


def save_model_connection_entry(
    entry: ModelConnectionEntry, config_root: Path | None = None
) -> None:
    base = config_dir() if config_root is None else config_root
    d = base / "model_connections"
    d.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(base)
    payload = entry.model_dump(mode="json", exclude_none=True)
    path = d / f"{entry.id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ids = list(manifest.model_connection_ids)
    if entry.id not in ids:
        ids.append(entry.id)
    updated = manifest.model_copy(update={"model_connection_ids": ids})
    write_manifest_dict(updated.model_dump(mode="json"), config_root=base)


def delete_model_connection_entry(
    connection_id: str, config_root: Path | None = None
) -> None:
    base = config_dir() if config_root is None else config_root
    path = base / "model_connections" / f"{connection_id}.json"
    if path.is_file():
        path.unlink()
    manifest = load_manifest(base)
    ids = [x for x in manifest.model_connection_ids if x != connection_id]
    updated = manifest.model_copy(update={"model_connection_ids": ids})
    write_manifest_dict(updated.model_dump(mode="json"), config_root=base)
