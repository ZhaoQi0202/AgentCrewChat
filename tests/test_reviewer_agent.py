from unittest.mock import patch, MagicMock

from agentloom.graph.nodes.reviewer_agent import review_task, _VERDICT_PATTERN


def test_verdict_pattern_pass():
    assert _VERDICT_PATTERN.search("很好！VERDICT:PASS").group(1) == "PASS"


def test_verdict_pattern_fail():
    assert _VERDICT_PATTERN.search("不行。VERDICT:FAIL").group(1) == "FAIL"


def test_verdict_pattern_missing():
    assert _VERDICT_PATTERN.search("没有标记的文本") is None


def test_review_task_pass():
    """审核通过时应返回 (True, message)。"""
    fake_resp = MagicMock()
    fake_resp.content = "代码没问题，接口规范，错误处理到位。VERDICT:PASS"

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.reviewer_agent.get_chat_model", return_value=fake_llm):
        with patch("agentloom.graph.nodes.reviewer_agent.emit_event"):
            passed, msg = review_task(
                task_id="t1",
                task_name="后端API",
                task_goal="创建天气查询端点",
                acceptance_criteria=["返回JSON", "错误处理"],
                agent_output="已创建 /api/weather 端点，测试通过",
                thread_id="test",
            )

    assert passed is True
    assert "PASS" in msg


def test_review_task_fail():
    """审核不通过时应返回 (False, message)。"""
    fake_resp = MagicMock()
    fake_resp.content = "缺少错误处理，传空值会崩溃。VERDICT:FAIL"

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.reviewer_agent.get_chat_model", return_value=fake_llm):
        with patch("agentloom.graph.nodes.reviewer_agent.emit_event"):
            passed, msg = review_task(
                task_id="t1",
                task_name="后端API",
                task_goal="创建天气查询端点",
                acceptance_criteria=["错误处理"],
                agent_output="创建了端点但没加校验",
                thread_id="test",
            )

    assert passed is False
    assert "FAIL" in msg


def test_review_task_no_verdict_defaults_to_fail():
    """如果 LLM 没有输出 VERDICT 标记，默认为 fail。"""
    fake_resp = MagicMock()
    fake_resp.content = "嗯...不太���定这个算不算完成"

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.reviewer_agent.get_chat_model", return_value=fake_llm):
        with patch("agentloom.graph.nodes.reviewer_agent.emit_event"):
            passed, _ = review_task(
                task_id="t1",
                task_name="测试",
                task_goal="目标",
                acceptance_criteria=[],
                agent_output="产出",
                thread_id="test",
            )

    assert passed is False
