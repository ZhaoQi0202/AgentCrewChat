from __future__ import annotations

from pathlib import Path

from agentcrewchat.config.models import ShellPolicy

from .process_runner import run_process


def hit_high_risk(command: str, policy: ShellPolicy) -> bool:
    if not policy.high_risk_prefixes:
        return False
    s = command.lstrip()
    return any(s.startswith(p) for p in policy.high_risk_prefixes if p)


class ShellRunner:
    def __init__(self, policy: ShellPolicy) -> None:
        self._policy = policy

    def hit_high_risk(self, command: str) -> bool:
        return hit_high_risk(command, self._policy)

    def run(
        self,
        command: str,
        task_root: Path,
        *,
        timeout: float | None = None,
        max_stdout_bytes: int | None = None,
        max_stderr_bytes: int | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        if ".." in command:
            raise ValueError("command must not contain '..'")
        task_root = task_root.resolve()
        if self._policy.shell == "powershell":
            argv = ["powershell", "-NoProfile", "-Command", command]
        else:
            argv = ["cmd.exe", "/c", command]
        return run_process(
            argv,
            cwd=task_root,
            timeout=timeout,
            max_stdout_bytes=max_stdout_bytes,
            max_stderr_bytes=max_stderr_bytes,
            env=env,
        )
