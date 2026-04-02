from unittest.mock import patch, MagicMock

from agentloom.graph.nodes.architect_agent import (
    generate_blueprint,
    _parse_blueprint,
    _gather_available_tools,
)


def test_parse_blueprint_valid():
    text = (
        '方案来了！\n'
        '```blueprint\n'
        '{"tasks": [{"id": "t1", "name": "test", "goal": "test goal", '
        '"acceptance_criteria": ["done"], "tools": ["shell"], "depends_on": []}]}\n'
        '```\n'
        '以上就是方案~'
    )
    bp = _parse_blueprint(text)
    assert bp is not None
    assert len(bp["tasks"]) == 1
    assert bp["tasks"][0]["id"] == "t1"


def test_parse_blueprint_missing():
    assert _parse_blueprint("没有 blueprint 块的文本") is None


def test_parse_blueprint_invalid_json():
    text = '```blueprint\n{invalid json}\n```'
    assert _parse_blueprint(text) is None


def test_gather_available_tools_always_has_builtins():
    """即使没有 skills 和 MCPs，内置能力也应该列出。"""
    with patch("agentloom.graph.nodes.architect_agent.merged_skills_for_agents", return_value=[]):
        with patch("agentloom.graph.nodes.architect_agent.load_all") as mock_cfg:
            mock_cfg.return_value = MagicMock(mcps=[])
            result = _gather_available_tools(None)
    assert "shell" in result
    assert "python" in result


def test_generate_blueprint_success():
    """generate_blueprint 应返回 (text, blueprint_dict)。"""
    fake_resp = MagicMock()
    fake_resp.content = (
        '方案出炉！\n'
        '```blueprint\n'
        '{"tasks": [{"id": "t1", "name": "后端", "goal": "写API", '
        '"acceptance_criteria": ["能用"], "tools": ["python", "shell"], "depends_on": []}]}\n'
        '```\n'
        '一共1个任务，开干！'
    )
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_resp

    with patch("agentloom.graph.nodes.architect_agent.get_chat_model", return_value=fake_llm):
        with patch("agentloom.graph.nodes.architect_agent.merged_skills_for_agents", return_value=[]):
            with patch("agentloom.graph.nodes.architect_agent.load_all") as mock_cfg:
                mock_cfg.return_value = MagicMock(mcps=[])
                text, bp = generate_blueprint({"core_goal": "做一个API"})

    assert bp is not None
    assert bp["tasks"][0]["name"] == "后端"
    assert "方案出炉" in text
