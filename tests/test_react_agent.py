from unittest.mock import patch, MagicMock

from agentloom.graph.nodes.react_agent import run_react_agent


def test_react_agent_completes_without_tools():
    """没有工具调用时，Agent 应该直接返回 LLM 回复。"""
    fake_resp = MagicMock()
    fake_resp.content = "任务搞定了！文件��创建。"
    fake_resp.tool_calls = []

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp
    # bind_tools 不存在时直接用 llm
    fake_llm.bind_tools.return_value = fake_llm

    with patch("agentloom.graph.nodes.react_agent.get_chat_model", return_value=fake_llm):
        with patch("agentloom.graph.nodes.react_agent.emit_event"):
            result = run_react_agent(
                task_id="t1",
                task_name="测试任务",
                task_goal="测试目标",
                acceptance_criteria=["完成即可"],
                tools=[],
                workspace_path="/tmp/test",
                thread_id="test-thread",
            )

    assert result["status"] == "completed"
    assert result["task_id"] == "t1"
    assert "搞定" in result["output"]


def test_react_agent_handles_error():
    """LLM 调用失败时应返回 error 状态。"""
    fake_llm = MagicMock()
    fake_llm.bind_tools.return_value = fake_llm
    fake_llm.invoke.side_effect = Exception("LLM 连接失败")

    with patch("agentloom.graph.nodes.react_agent.get_chat_model", return_value=fake_llm):
        with patch("agentloom.graph.nodes.react_agent.emit_event"):
            result = run_react_agent(
                task_id="t1",
                task_name="测试任务",
                task_goal="测试目标",
                acceptance_criteria=[],
                tools=[],
                workspace_path="/tmp/test",
                thread_id="test-thread",
            )

    assert result["status"] == "error"
    assert "连接失败" in result["output"]
