from __future__ import annotations

from typing import Any


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
