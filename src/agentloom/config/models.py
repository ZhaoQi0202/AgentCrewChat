from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConfigValidationError(Exception):
    pass


class ShellPolicy(BaseModel):
    model_config = ConfigDict(extra="ignore")

    shell: Literal["cmd", "powershell"] = "cmd"
    high_risk_prefixes: list[str] = Field(default_factory=list)


class McpEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str | None = None
    description: str | None = None
    skill_dir: str = ""
    enabled: bool = True
    scope: Literal["app", "task"] = "app"


class ManifestRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: str = "1"
    mcp_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    shell: ShellPolicy | None = None


class LoadedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    mcp_ids: list[str]
    skill_ids: list[str]
    mcps: list[McpEntry]
    skills: list[SkillEntry]
    shell: ShellPolicy


class LlmSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    default_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-4-20250514"
