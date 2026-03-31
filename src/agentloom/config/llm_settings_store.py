import json
from pathlib import Path

from pydantic import ValidationError

from agentloom.paths import config_dir

from .models import ConfigValidationError, LlmSettings


def settings_path(install_root: Path | None = None) -> Path:
    if install_root is not None:
        return install_root / "config" / "settings.json"
    return config_dir() / "settings.json"


def load_llm_settings(install_root: Path | None = None) -> LlmSettings:
    path = settings_path(install_root)
    if not path.is_file():
        return LlmSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"settings.json 无效 JSON: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigValidationError("settings.json 须为 JSON 对象")
    try:
        return LlmSettings.model_validate(raw)
    except ValidationError as e:
        raise ConfigValidationError(str(e)) from e


def save_llm_settings(settings: LlmSettings, install_root: Path | None = None) -> None:
    path = settings_path(install_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = settings.model_dump(mode="json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
