from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from agentloom.config.loader import (
    delete_skill_entry,
    load_all,
    save_mcp_entry,
    save_skill_entry,
)
from agentloom.config.llm_settings_store import load_llm_settings, save_llm_settings
from agentloom.config.model_connection_store import (
    allocate_connection_id,
    delete_model_connection_entry,
    list_model_connections,
    save_model_connection_entry,
)
from agentloom.config.models import (
    LlmSettings,
    McpEntry,
    ModelConnectionEntry,
    SkillEntry,
)
from agentloom.llm.connection_check import probe_model_connection
from agentloom.paths import install_root
from agentloom.skills.skill_import import import_skills_from_input

router = APIRouter(prefix="/config", tags=["config"])


# ── 模型连接 ─────────────────────────────────────────────


@router.get("/model-connections")
async def get_model_connections() -> list[ModelConnectionEntry]:
    return list_model_connections()


class ModelConnectionCreate(BaseModel):
    name: str
    provider: str = "openai_compatible"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    enabled: bool = True


@router.post("/model-connections")
async def create_model_connection(body: ModelConnectionCreate) -> ModelConnectionEntry:
    existing = {c.id for c in list_model_connections()}
    cid = allocate_connection_id(body.name, existing)
    entry = ModelConnectionEntry(id=cid, **body.model_dump())
    save_model_connection_entry(entry)
    return entry


@router.delete("/model-connections/{connection_id}")
async def remove_model_connection(connection_id: str) -> dict[str, str]:
    delete_model_connection_entry(connection_id)
    return {"status": "ok"}


@router.post("/model-connections/{connection_id}/probe")
async def probe_connection(connection_id: str) -> dict[str, object]:
    conns = list_model_connections()
    entry = next((c for c in conns if c.id == connection_id), None)
    if entry is None:
        raise HTTPException(404, "连接不存在")
    ok, msg = probe_model_connection(
        entry.provider, entry.base_url, entry.api_key, entry.model
    )
    return {"ok": ok, "message": msg}


# ── MCP 服务器 ────────────────────────────────────────────


@router.get("/mcps")
async def get_mcps() -> list[McpEntry]:
    cfg = load_all()
    return cfg.mcps


@router.post("/mcps")
async def create_mcp(body: McpEntry) -> McpEntry:
    save_mcp_entry(body)
    return body


@router.delete("/mcps/{mcp_id}")
async def remove_mcp(mcp_id: str) -> dict[str, str]:
    # 目前 loader 没有 delete_mcp_entry，手动实现
    import json
    from agentloom.config.manifest import load_manifest, write_manifest_dict
    from agentloom.paths import config_dir

    base = config_dir()
    path = base / "mcp" / f"{mcp_id}.json"
    if path.is_file():
        path.unlink()
    manifest = load_manifest(base)
    ids = [x for x in manifest.mcp_ids if x != mcp_id]
    updated = manifest.model_copy(update={"mcp_ids": ids})
    write_manifest_dict(updated.model_dump(mode="json"), config_root=base)
    return {"status": "ok"}


# ── 技能 ──────────────────────────────────────────────────


@router.get("/skills")
async def get_skills() -> list[SkillEntry]:
    cfg = load_all()
    return cfg.skills


class SkillImportRequest(BaseModel):
    text: str


@router.post("/skills/import")
async def import_skill(body: SkillImportRequest) -> list[SkillEntry]:
    try:
        entries = import_skills_from_input(body.text)
        for e in entries:
            save_skill_entry(e)
        return entries
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/skills/{skill_id}")
async def remove_skill(skill_id: str) -> dict[str, str]:
    delete_skill_entry(skill_id, install_root_for_payload=install_root())
    return {"status": "ok"}


# ── LLM 设置 ─────────────────────────────────────────────


@router.get("/llm-settings")
async def get_llm_settings() -> LlmSettings:
    return load_llm_settings()


@router.put("/llm-settings")
async def update_llm_settings(body: LlmSettings) -> LlmSettings:
    save_llm_settings(body)
    return body
