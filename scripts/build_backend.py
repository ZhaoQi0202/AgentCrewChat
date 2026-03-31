"""
PyInstaller 打包脚本 — 将 AgentLoom API 后端打包为单目录可执行程序。

用法:
  cd <project_root>
  python scripts/build_backend.py

输出:
  client/resources/backend/agentloom-api.exe  (Windows)
  client/resources/backend/agentloom-api      (macOS/Linux)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "client" / "resources" / "backend"


def main():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        # 单目录模式（比单文件启动更快）
        "--onedir",
        "--name", "agentloom-api",
        "--distpath", str(DIST_DIR),
        # 隐藏导入
        "--hidden-import", "agentloom.api",
        "--hidden-import", "agentloom.api.app",
        "--hidden-import", "agentloom.api.routes",
        "--hidden-import", "agentloom.api.routes.config",
        "--hidden-import", "agentloom.api.routes.tasks",
        "--hidden-import", "agentloom.api.routes.graph",
        "--hidden-import", "agentloom.graph.nodes.stubs",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        # 收集 langgraph 和 langchain 相关包
        "--collect-all", "langgraph",
        "--collect-all", "langchain_core",
        "--collect-all", "langchain_openai",
        "--collect-all", "langchain_anthropic",
        # 入口
        str(ROOT / "src" / "agentloom" / "api" / "server.py"),
    ]

    print(f"[build_backend] Running: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("[build_backend] PyInstaller failed!")
        sys.exit(1)

    print(f"[build_backend] Output: {DIST_DIR / 'agentloom-api'}")
    print("[build_backend] Done.")


if __name__ == "__main__":
    main()
