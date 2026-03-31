from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from agentloom.graph.builder import build_graph
from agentloom.paths import install_root as default_install_root
from langgraph.types import Command


def split_stream_chunk(
    chunk: dict[str, Any],
) -> tuple[list[tuple[str, dict[str, Any]]], bool]:
    if "__interrupt__" in chunk:
        out: list[tuple[str, dict[str, Any]]] = []
        for key, val in chunk.items():
            if key == "__interrupt__":
                continue
            if isinstance(val, dict):
                out.append((key, val))
        return out, True
    pairs: list[tuple[str, dict[str, Any]]] = []
    for key, val in chunk.items():
        if isinstance(val, dict):
            pairs.append((key, val))
    return pairs, False


class GraphRunner(QObject):
    phase_event = Signal(str, dict)
    interrupted = Signal(str)
    finished = Signal()
    error = Signal(str)

    _request_start = Signal()
    _request_resume = Signal()

    def __init__(
        self,
        install_root: Path | None = None,
    ) -> None:
        super().__init__()
        self._install_root = install_root or default_install_root()
        self._thread_id = ""
        self._cfg: dict[str, Any] = {}
        self._graph: Any = None
        self._request_start.connect(self._on_start)
        self._request_resume.connect(self._on_resume)

    def request_start(self) -> None:
        self._request_start.emit()

    def request_resume(self) -> None:
        self._request_resume.emit()

    @Slot()
    def _on_start(self) -> None:
        try:
            self._thread_id = str(uuid.uuid4())
            self._cfg = {"configurable": {"thread_id": self._thread_id}}
            self._graph = build_graph(self._install_root)
            self._run_stream({"task_id": "ui-stub"})
        except Exception as e:
            self.error.emit(str(e))

    @Slot()
    def _on_resume(self) -> None:
        if self._graph is None:
            return
        try:
            self._run_stream(Command(resume={}))
        except Exception as e:
            self.error.emit(str(e))

    def _run_stream(self, input_obj: Any) -> None:
        assert self._graph is not None
        for chunk in self._graph.stream(
            input_obj, self._cfg, stream_mode="updates"
        ):
            parts, has_interrupt = split_stream_chunk(chunk)
            for node, upd in parts:
                self.phase_event.emit(node, upd)
            if has_interrupt:
                st = self._graph.get_state(self._cfg)
                nxt = st.next[0] if st.next else ""
                self.interrupted.emit(str(nxt))
                return
        self.finished.emit()
