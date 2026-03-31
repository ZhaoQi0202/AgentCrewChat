from agentloom import paths
from agentloom.paths import install_root


def check_writable_root() -> bool:
    root = install_root()
    test_file = root / ".write_test"
    try:
        test_file.write_text("", encoding="utf-8")
        test_file.unlink()
        return True
    except OSError:
        return False


def ensure_layout() -> None:
    for d in (paths.config_dir(), paths.data_dir(), paths.workspaces_dir()):
        d.mkdir(parents=True, exist_ok=True)
