from agentloom.graph.orchestrator import _topological_sort


def test_topological_sort_linear():
    """线性依赖：t1 → t2 → t3"""
    tasks = [
        {"id": "t1", "depends_on": []},
        {"id": "t2", "depends_on": ["t1"]},
        {"id": "t3", "depends_on": ["t2"]},
    ]
    layers = _topological_sort(tasks)
    assert len(layers) == 3
    assert [t["id"] for t in layers[0]] == ["t1"]
    assert [t["id"] for t in layers[1]] == ["t2"]
    assert [t["id"] for t in layers[2]] == ["t3"]


def test_topological_sort_parallel():
    """并行：t1 和 t2 无依赖，t3 依赖两者"""
    tasks = [
        {"id": "t1", "depends_on": []},
        {"id": "t2", "depends_on": []},
        {"id": "t3", "depends_on": ["t1", "t2"]},
    ]
    layers = _topological_sort(tasks)
    assert len(layers) == 2
    layer0_ids = {t["id"] for t in layers[0]}
    assert layer0_ids == {"t1", "t2"}
    assert [t["id"] for t in layers[1]] == ["t3"]


def test_topological_sort_single():
    """单个任务"""
    tasks = [{"id": "t1", "depends_on": []}]
    layers = _topological_sort(tasks)
    assert len(layers) == 1
    assert layers[0][0]["id"] == "t1"


def test_topological_sort_empty():
    """空任务列表"""
    assert _topological_sort([]) == []
