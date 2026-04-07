from agentloom.graph.nodes.user_confirmation import is_user_confirmation


def test_confirm_yes():
    assert is_user_confirmation("好的，开始吧") is True
    assert is_user_confirmation("没问题") is True


def test_confirm_no():
    assert is_user_confirmation("把优先级改成 must") is False
    assert is_user_confirmation("") is False
