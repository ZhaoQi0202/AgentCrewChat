from unittest.mock import patch, MagicMock

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agentloom.graph.nodes.consultant_agent import (
    build_initial_greeting,
    consult_turn,
    extract_requirement,
    CONSULTANT_SYSTEM_PROMPT,
)


def test_build_initial_greeting_returns_string():
    greeting = build_initial_greeting()
    assert isinstance(greeting, str)
    assert len(greeting) > 10


def test_consult_turn_normal_response():
    """LLM 没有输出 summary 块时，is_ready 应为 False。"""
    fake_resp = MagicMock()
    fake_resp.content = "明白了！你打算用什么技术栈？"

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.consultant_agent.get_chat_model", return_value=fake_llm):
        history = [
            SystemMessage(content=CONSULTANT_SYSTEM_PROMPT),
            HumanMessage(content="我想做一个 todo 应用"),
        ]
        text, is_ready, summary = consult_turn(history)

    assert text == "明白了！你打算用什么技术栈？"
    assert is_ready is False
    assert summary is None


def test_consult_turn_with_summary_block():
    """LLM 输出含 requirement_summary 块时，is_ready 应为 True。"""
    response_text = (
        '需求看起来很清晰！这是摘要：\n'
        '```requirement_summary\n'
        '{"core_goal": "做一个 todo 应用", "features": []}\n'
        '```\n'
        '确认没问题的话点击启动项目~'
    )
    fake_resp = MagicMock()
    fake_resp.content = response_text

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.consultant_agent.get_chat_model", return_value=fake_llm):
        history = [
            SystemMessage(content=CONSULTANT_SYSTEM_PROMPT),
            HumanMessage(content="我想做一个 React 的 todo 应用"),
        ]
        text, is_ready, summary = consult_turn(history)

    assert is_ready is True
    assert summary is not None
    assert summary["core_goal"] == "做一个 todo 应用"


def test_extract_requirement():
    """extract_requirement 应返回包含核心字段的 dict。"""
    fake_resp = MagicMock()
    fake_resp.content = (
        '```requirement_summary\n'
        '{"project_name": "Todo", "core_goal": "做 todo 应用", '
        '"constraints": {"tech_stack": ["React"], "platform": "web", "timeline": null}, '
        '"success_criteria": ["能增删改查"], '
        '"features": [{"name": "添加任务", "description": "新增任务", "priority": "must"}], '
        '"additional_notes": null, '
        '"raw_conversation_summary": "用户想做一个 todo 应用"}\n'
        '```'
    )
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.consultant_agent.get_chat_model", return_value=fake_llm):
        history = [
            SystemMessage(content=CONSULTANT_SYSTEM_PROMPT),
            HumanMessage(content="做一个 todo 应用"),
            AIMessage(content="好！用什么技术栈？"),
            HumanMessage(content="React"),
        ]
        req = extract_requirement(history)

    assert req["core_goal"] == "做 todo 应用"
    assert "features" in req
