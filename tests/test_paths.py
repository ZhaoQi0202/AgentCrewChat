from agentloom.paths import install_root


def test_install_root_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    assert install_root() == tmp_path.resolve()
