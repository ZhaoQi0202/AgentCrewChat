from agentloom import paths


def ensure_layout() -> None:
    for d in (paths.config_dir(), paths.data_dir(), paths.workspaces_dir()):
        d.mkdir(parents=True, exist_ok=True)
