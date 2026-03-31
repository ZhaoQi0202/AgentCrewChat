from __future__ import annotations

from pathlib import Path

from .process_runner import run_process


class UvRunner:
    @staticmethod
    def venv_create(
        task_path: Path,
        *,
        timeout: float | None = None,
        max_stdout_bytes: int | None = None,
        max_stderr_bytes: int | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        return run_process(
            ["uv", "venv"],
            cwd=task_path,
            timeout=timeout,
            max_stdout_bytes=max_stdout_bytes,
            max_stderr_bytes=max_stderr_bytes,
            env=env,
        )
