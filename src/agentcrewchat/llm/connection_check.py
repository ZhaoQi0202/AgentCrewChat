from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any


def normalize_openai_base_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u:
        return "https://api.openai.com/v1"
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _anthropic_base(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u:
        return "https://api.anthropic.com"
    return u


def probe_openai_compatible(
    base_url: str, api_key: str, timeout: float = 15.0
) -> tuple[bool, str]:
    key = (api_key or "").strip()
    if not key:
        return False, "未填写 API Key"
    base = normalize_openai_base_url(base_url)
    req_url = f"{base}/models"
    req = urllib.request.Request(
        req_url,
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if 200 <= resp.status < 300:
                return True, "成功"
            return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"HTTP {e.code}: {body or e.reason}"
    except urllib.error.URLError as e:
        return False, str(e.reason or e)
    except TimeoutError:
        return False, "超时"
    except OSError as e:
        return False, str(e)


def probe_anthropic_connection(
    base_url: str, api_key: str, model: str, timeout: float = 30.0
) -> tuple[bool, str]:
    key = (api_key or "").strip()
    if not key:
        return False, "未填写 API Key"
    m = (model or "").strip()
    if not m:
        return False, "未填写模型名"
    root = _anthropic_base(base_url)
    req_url = f"{root}/v1/messages"
    body: dict[str, Any] = {
        "model": m,
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "."}],
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        req_url,
        data=data,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if 200 <= resp.status < 300:
                return True, "成功"
            return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        body_t = e.read().decode("utf-8", errors="replace")[:300]
        return False, f"HTTP {e.code}: {body_t or e.reason}"
    except urllib.error.URLError as e:
        return False, str(e.reason or e)
    except TimeoutError:
        return False, "超时"
    except OSError as e:
        return False, str(e)


def probe_model_connection(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    timeout: float = 20.0,
) -> tuple[bool, str]:
    if provider == "anthropic":
        return probe_anthropic_connection(base_url, api_key, model, timeout=timeout)
    return probe_openai_compatible(base_url, api_key, timeout=timeout)
