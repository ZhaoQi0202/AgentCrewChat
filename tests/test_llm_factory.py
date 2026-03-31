import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.language_models.chat_models import BaseChatModel

from agentloom.llm.factory import get_chat_model


def test_openai_no_key_returns_fake(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    m = get_chat_model("openai")
    assert m._llm_type == "agentloom-fake-chat"
    assert m.invoke("hi").content == "fake"


def test_anthropic_no_key_returns_fake(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    m = get_chat_model("anthropic")
    assert m._llm_type == "agentloom-fake-chat"
    assert m.invoke("hi").content == "fake"


def test_unknown_provider_returns_fake(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    m = get_chat_model("other")
    assert m._llm_type == "agentloom-fake-chat"
    assert m.invoke("x").content == "fake"


def test_openai_with_key_uses_chat_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fake_real = MagicMock(spec=BaseChatModel)
    with patch("agentloom.llm.factory.ChatOpenAI", return_value=fake_real) as mock_cls:
        out = get_chat_model("openai", model="gpt-4o-mini")
    mock_cls.assert_called_once_with(api_key="sk-test", model="gpt-4o-mini")
    assert out is fake_real


def test_default_model_connection_overrides_legacy(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = tmp_path / "config"
    (cfg / "model_connections").mkdir(parents=True)
    conn = {
        "id": "c1",
        "name": "x",
        "provider": "openai_compatible",
        "base_url": "",
        "api_key": "sk-conn",
        "model": "gpt-4o-mini",
        "enabled": True,
    }
    (cfg / "model_connections" / "c1.json").write_text(
        json.dumps(conn, ensure_ascii=False), encoding="utf-8"
    )
    (cfg / "manifest.json").write_text(
        json.dumps(
            {
                "version": "1",
                "mcp_ids": [],
                "skill_ids": [],
                "model_connection_ids": ["c1"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (cfg / "settings.json").write_text(
        json.dumps(
            {
                "default_model_connection_id": "c1",
                "default_provider": "openai",
                "openai_api_key": "sk-legacy",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    fake_real = MagicMock(spec=BaseChatModel)
    with patch("agentloom.llm.factory.ChatOpenAI", return_value=fake_real) as mock_cls:
        out = get_chat_model(install_root=tmp_path)
    mock_cls.assert_called_once()
    call_kw = mock_cls.call_args.kwargs
    assert call_kw["api_key"] == "sk-conn"
    assert call_kw["model"] == "gpt-4o-mini"
    assert out is fake_real


def test_anthropic_with_key_uses_chat_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    fake_real = MagicMock(spec=BaseChatModel)
    with patch("agentloom.llm.factory.ChatAnthropic", return_value=fake_real) as mock_cls:
        out = get_chat_model("anthropic", model="claude-3-5-sonnet-20241022")
    mock_cls.assert_called_once_with(
        api_key="sk-ant-test", model="claude-3-5-sonnet-20241022"
    )
    assert out is fake_real
