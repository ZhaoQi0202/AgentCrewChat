import os
from pathlib import Path


def install_root() -> Path:
    env = os.environ.get("AGENTCREWCHAT_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def config_dir() -> Path:
    return install_root() / "config"


def data_dir() -> Path:
    return install_root() / "data"


def workspaces_dir() -> Path:
    return install_root() / "workspaces"
