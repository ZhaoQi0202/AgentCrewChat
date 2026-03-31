import json

from agentloom.config.manifest import load_manifest
from agentloom.config.model_connection_store import (
    delete_model_connection_entry,
    list_model_connections,
    save_model_connection_entry,
)
from agentloom.config.models import ModelConnectionEntry


def test_save_list_delete_roundtrip(tmp_path):
    cfg = tmp_path / "config"
    cfg.mkdir(parents=True)
    (cfg / "manifest.json").write_text(
        json.dumps(
            {
                "version": "1",
                "mcp_ids": [],
                "skill_ids": [],
                "model_connection_ids": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    e = ModelConnectionEntry(
        id="my-openai",
        name="工作",
        provider="openai_compatible",
        base_url="",
        api_key="k",
        model="gpt-4o-mini",
    )
    save_model_connection_entry(e, config_root=cfg)
    rows = list_model_connections(cfg)
    assert len(rows) == 1
    assert rows[0].id == "my-openai"
    assert rows[0].name == "工作"
    m = load_manifest(cfg)
    assert m.model_connection_ids == ["my-openai"]
    delete_model_connection_entry("my-openai", config_root=cfg)
    assert list_model_connections(cfg) == []
    m2 = load_manifest(cfg)
    assert m2.model_connection_ids == []
