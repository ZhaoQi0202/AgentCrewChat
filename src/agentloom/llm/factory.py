import os
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel, SimpleChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from agentloom.config.llm_settings_store import load_llm_settings


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
    **kwargs: Any,
) -> BaseChatModel:
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
