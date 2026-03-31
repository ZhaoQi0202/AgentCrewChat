from unittest.mock import MagicMock, patch

from agentloom.llm.connection_check import (
    normalize_openai_base_url,
    probe_anthropic_connection,
    probe_openai_compatible,
)


def test_normalize_openai_base_url():
    assert normalize_openai_base_url("") == "https://api.openai.com/v1"
    assert normalize_openai_base_url("https://x.com") == "https://x.com/v1"
    assert normalize_openai_base_url("https://x.com/v1") == "https://x.com/v1"


def test_openai_no_key():
    ok, msg = probe_openai_compatible("https://api.openai.com/v1", "")
    assert ok is False
    assert "Key" in msg


def test_openai_success_mock():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_resp)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    with patch("agentloom.llm.connection_check.urllib.request.urlopen", return_value=mock_ctx):
        ok, msg = probe_openai_compatible("https://api.openai.com/v1", "sk-x")
    assert ok is True
    assert msg == "成功"


def test_anthropic_no_model():
    ok, msg = probe_anthropic_connection("", "k", "")
    assert ok is False
