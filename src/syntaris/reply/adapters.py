from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from syntaris.contracts.runtime import ReplyConfig, TurnInput


@dataclass(frozen=True)
class ReplyOutput:
    text: str
    backend: str
    degraded: bool


def _coerce_response_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                normalized = item.strip()
                if normalized:
                    parts.append(normalized)
                continue
            if isinstance(item, dict):
                normalized = str(item.get("text") or item.get("content") or "").strip()
                if normalized:
                    parts.append(normalized)
        return "\n".join(parts).strip()
    if isinstance(value, dict):
        normalized = str(value.get("text") or value.get("content") or "").strip()
        return normalized
    return ""


def _extract_llama_text(raw: dict[str, Any]) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("missing_choices")

    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("invalid_choice")

    message = first.get("message")
    if isinstance(message, dict):
        text = _coerce_response_text(message.get("content"))
        if text:
            return text

    text = _coerce_response_text(first.get("text"))
    if text:
        return text

    text = _coerce_response_text(first.get("output_text"))
    if text:
        return text

    raise ValueError("empty_content")


class ReplyAdapter:
    def generate(self, turn_input: TurnInput) -> ReplyOutput:
        raise NotImplementedError


class DeterministicReplyAdapter(ReplyAdapter):
    def generate(self, turn_input: TurnInput) -> ReplyOutput:
        return ReplyOutput(
            text=f"[fallback] Deterministic reply: {turn_input.message}",
            backend="deterministic",
            degraded=True,
        )


class LlamaHttpReplyAdapter(ReplyAdapter):
    def __init__(self, config: ReplyConfig):
        self.config = config

    def generate(self, turn_input: TurnInput) -> ReplyOutput:
        payload = {
            "model": self.config.live_model,
            "messages": [{"role": "user", "content": turn_input.message}],
            "temperature": 0,
        }
        request = urllib.request.Request(
            url=f"{self.config.live_url.rstrip('/')}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text = _extract_llama_text(raw)
        return ReplyOutput(text=text, backend="llama-http", degraded=False)


class SafeReplyAdapter(ReplyAdapter):
    def __init__(self, preferred: ReplyAdapter, fallback: ReplyAdapter):
        self.preferred = preferred
        self.fallback = fallback

    def generate(self, turn_input: TurnInput) -> ReplyOutput:
        try:
            return self.preferred.generate(turn_input)
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, TypeError, IndexError):
            return self.fallback.generate(turn_input)
