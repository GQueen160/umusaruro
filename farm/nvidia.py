"""One open model on NVIDIA's hosted API.

The key stays on the server. Set NVIDIA_API_KEY from
https://build.nvidia.com/settings and, if you want another open model,
NVIDIA_MODEL. The default is Nemotron 3.5 Bolt. Locally the key is
read from the gitignored .env file.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "nvidia/nemotron-3.5-bolt-e4b"


class NvidiaError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def message_text(payload: dict) -> str:
    choice = payload["choices"][0]["message"]["content"]
    if isinstance(choice, list):
        parts = []
        for part in choice:
            if isinstance(part, dict):
                parts.append(str(part.get("text") or ""))
        choice = "".join(parts)
    text = str(choice or "").strip()
    if not text:
        raise KeyError("empty")
    return text


def complete(messages: list[dict], *, max_tokens: int, timeout: int = 20, transport=None) -> str:
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        raise NvidiaError("missing-key")
    model = os.environ.get("NVIDIA_MODEL", "").strip() or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if transport is not None:
        return transport(payload, key)
    return _post(payload, key, timeout)


def _post(payload: dict, key: str, timeout: int) -> str:
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise NvidiaError("failed") from exc
    try:
        return message_text(json.loads(raw))
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise NvidiaError("failed") from exc
