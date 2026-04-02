import tempfile
from pathlib import Path

from agentloom.graph import AgentLoomState, build_graph


def test_graph_compiles() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        root = Path(td)
        g = build_graph(install_root=root)
        assert g is not None


def test_invoke_interrupts_before_hitl_blueprint() -> None:
    """图运行 consultant(透传) → architect 后，在 hitl_blueprint 前中断。"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        root = Path(td)
        g = build_graph(install_root=root)
        cfg = {"configurable": {"thread_id": "t1"}}
        out: AgentLoomState = g.invoke({"task_id": "x"}, cfg)
        assert out.get("phase") == "architect"
        assert out.get("consult_confidence") == 1.0
        assert "blueprint" in out
