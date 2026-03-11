from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from syntaris.contracts.runtime import ReplyConfig, TurnInput


@dataclass(frozen=True)
class ReplyOutput:
    text: str
    backend: str
    degraded: bool


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
        text = raw["choices"][0]["message"]["content"]
        return ReplyOutput(text=text, backend="llama-http", degraded=False)


class SafeReplyAdapter(ReplyAdapter):
    def __init__(self, preferred: ReplyAdapter, fallback: ReplyAdapter):
        self.preferred = preferred
        self.fallback = fallback

    def generate(self, turn_input: TurnInput) -> ReplyOutput:
        try:
            return self.preferred.generate(turn_input)
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
            return self.fallback.generate(turn_input)
