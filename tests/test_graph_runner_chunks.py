from agentloom.ui.worker import split_stream_chunk


def test_split_node_only() -> None:
    parts, intr = split_stream_chunk(
        {"consultant": {"phase": "consult", "consult_confidence": 1.0}}
    )
    assert intr is False
    assert parts == [("consultant", {"phase": "consult", "consult_confidence": 1.0})]


def test_split_interrupt_only() -> None:
    parts, intr = split_stream_chunk({"__interrupt__": ()})
    assert intr is True
    assert parts == []


def test_split_mixed() -> None:
    parts, intr = split_stream_chunk(
        {"architect": {"phase": "architect"}, "__interrupt__": ()}
    )
    assert intr is True
    assert parts == [("architect", {"phase": "architect"})]
