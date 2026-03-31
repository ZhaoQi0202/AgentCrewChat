import os
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel, SimpleChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from agentloom.config.llm_settings_store import load_llm_settings
from agentloom.config.model_connection_store import load_model_connection
from agentloom.config.models import ModelConnectionEntry
from agentloom.paths import config_dir
from agentloom.llm.connection_check import normalize_openai_base_url


class _FixedFakeChatModel(SimpleChatModel):
    @property
    def _llm_type(self) -> str:
        return "agentloom-fake-chat"

    def _call(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> str:
        return "fake"


def _fake_chat_model() -> BaseChatModel:
    return _FixedFakeChatModel()


def _config_root(install_root: Path | None) -> Path:
    if install_root is not None:
        return (install_root / "config").resolve()
    return config_dir()


def _chat_from_connection(entry: ModelConnectionEntry, **kwargs: Any) -> BaseChatModel:
    key = (entry.api_key or "").strip()
    if not key:
        return _fake_chat_model()
    model = (entry.model or "").strip() or (
        "gpt-4o-mini" if entry.provider == "openai_compatible" else "claude-sonnet-4-20250514"
    )
    if entry.provider == "anthropic":
        root = (entry.base_url or "").strip().rstrip("/")
        kw: dict[str, Any] = {
            "api_key": key,
            "model": kwargs.pop("model", model),
            **kwargs,
        }
        if root:
            kw["base_url"] = root
        return ChatAnthropic(**kw)
    base = normalize_openai_base_url(entry.base_url)
    return ChatOpenAI(
        api_key=key,
        model=kwargs.pop("model", model),
        base_url=base,
        **kwargs,
    )


def _resolved_keys(
    install_root: Path | None,
) -> tuple[str, str | None, str | None, str, str]:
    s = load_llm_settings(install_root)
    oa = (s.openai_api_key or os.environ.get("OPENAI_API_KEY") or "").strip() or None
    an = (s.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY") or "").strip() or None
    return (s.default_provider, oa, an, s.openai_model, s.anthropic_model)


def get_chat_model(
    provider: str | None = None,
    *,
    install_root: Path | None = None,
    connection_id: str | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    s = load_llm_settings(install_root)
    cfg_root = _config_root(install_root)
    cid = (connection_id or s.default_model_connection_id or "").strip()
    if cid:
        ent = load_model_connection(cid, config_root=cfg_root)
        if ent is not None and ent.enabled:
            return _chat_from_connection(ent, **kwargs)
    default_p, oa_key, an_key, oa_model, an_model = _resolved_keys(install_root)
    key = (provider or default_p).lower().strip()
    if key == "openai":
        if oa_key:
            return ChatOpenAI(api_key=oa_key, model=kwargs.pop("model", oa_model), **kwargs)
        return _fake_chat_model()
    if key == "anthropic":
        if an_key:
            return ChatAnthropic(
                api_key=an_key,
                model=kwargs.pop("model", an_model),
                **kwargs,
            )
        return _fake_chat_model()
    return _fake_chat_model()
