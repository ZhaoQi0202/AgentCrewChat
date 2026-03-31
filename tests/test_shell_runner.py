from pathlib import Path
from unittest.mock import patch

import pytest

from agentloom.config.models import ShellPolicy
from agentloom.runtime.shell_runner import ShellRunner, hit_high_risk


def test_hit_high_risk_empty_policy():
    p = ShellPolicy(high_risk_prefixes=[])
    assert hit_high_risk("anything", p) is False


def test_hit_high_risk_prefix_match():
    p = ShellPolicy(high_risk_prefixes=["rm ", "format "])
    assert hit_high_risk("rm -rf /", p) is True
    assert hit_high_risk("  format c:", p) is True
    assert hit_high_risk("echo rm -rf", p) is False


def test_hit_high_risk_ignores_empty_prefix_strings():
    p = ShellPolicy(high_risk_prefixes=["", "x"])
    assert hit_high_risk("xyz", p) is True
    assert hit_high_risk("abc", p) is False


def test_shell_runner_rejects_dotdot():
    r = ShellRunner(ShellPolicy())
    with pytest.raises(ValueError, match=r"\.\."):
        r.run("cd ..\\x", Path("."))


def test_shell_runner_cmd_argv(monkeypatch, tmp_path):
    r = ShellRunner(ShellPolicy(shell="cmd"))
    captured: dict = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = list(argv)
        captured["cwd"] = kwargs.get("cwd")
        return 0, "out", "err"

    with patch("agentloom.runtime.shell_runner.run_process", side_effect=fake_run):
        code, out, err = r.run("echo hi", tmp_path)
    assert code == 0 and out == "out" and err == "err"
    assert captured["argv"] == ["cmd.exe", "/c", "echo hi"]
    assert captured["cwd"] == tmp_path.resolve()


def test_shell_runner_powershell_argv(monkeypatch, tmp_path):
    r = ShellRunner(ShellPolicy(shell="powershell"))

    def fake_run(argv, **kwargs):
        return 0, "", ""

    with patch("agentloom.runtime.shell_runner.run_process", side_effect=fake_run) as m:
        r.run("Get-Date", tmp_path)
    m.assert_called_once()
    args, kwargs = m.call_args
    assert args[0] == ["powershell", "-NoProfile", "-Command", "Get-Date"]
    assert kwargs["cwd"] == tmp_path.resolve()
