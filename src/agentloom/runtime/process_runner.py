from __future__ import annotations

import subprocess
from pathlib import Path


def run_process(
    argv: list[str],
    *,
    cwd: Path | str | None = None,
    timeout: float | None = None,
    max_stdout_bytes: int | None = None,
    max_stderr_bytes: int | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    cwd_s = str(cwd) if cwd is not None else None
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd_s,
            capture_output=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        out_b = e.stdout or b""
        err_b = e.stderr or b""
        if max_stdout_bytes is not None and len(out_b) > max_stdout_bytes:
            out_b = out_b[:max_stdout_bytes]
        if max_stderr_bytes is not None and len(err_b) > max_stderr_bytes:
            err_b = err_b[:max_stderr_bytes]
        return (
            -1,
            out_b.decode("utf-8", errors="replace"),
            err_b.decode("utf-8", errors="replace"),
        )
    out_b = completed.stdout or b""
    err_b = completed.stderr or b""
    if max_stdout_bytes is not None and len(out_b) > max_stdout_bytes:
        out_b = out_b[:max_stdout_bytes]
    if max_stderr_bytes is not None and len(err_b) > max_stderr_bytes:
        err_b = err_b[:max_stderr_bytes]
    return (
        completed.returncode,
        out_b.decode("utf-8", errors="replace"),
        err_b.decode("utf-8", errors="replace"),
    )
