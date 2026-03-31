from agentloom import bootstrap


def test_check_writable_root_tmp_path(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTLOOM_ROOT", str(tmp_path))
    assert bootstrap.check_writable_root() is True


def test_check_writable_root_no_parent(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agentloom.bootstrap.install_root",
        lambda: tmp_path / "missing" / "nested",
    )
    assert bootstrap.check_writable_root() is False
