import json

from syntaris.contracts.runtime import ReplyConfig, TurnInput
from syntaris.reply.adapters import LlamaHttpReplyAdapter
from syntaris.reply.factory import build_reply_adapter


def _turn_input(message: str) -> TurnInput:
    return TurnInput(message=message, session_id=1, thread_id=1, mode="chat")


def test_deterministic_reply_backend_is_stable():
    adapter = build_reply_adapter(ReplyConfig(backend="deterministic"))

    first = adapter.generate(_turn_input("szia"))
    second = adapter.generate(_turn_input("szia"))

    assert first.text == second.text
    assert first.backend == "deterministic"
    assert first.degraded is True


def test_llama_http_without_required_config_gracefully_falls_back():
    adapter = build_reply_adapter(ReplyConfig(backend="llama-http", live_url="", live_model=""))

    result = adapter.generate(_turn_input("hello"))

    assert result.backend == "deterministic"
    assert result.degraded is True


def test_llama_http_extracts_structured_content_segments(monkeypatch):
    payload = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "Első sor"},
                        {"type": "text", "text": "Második sor"},
                    ]
                }
            }
        ]
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response())

    adapter = LlamaHttpReplyAdapter(
        ReplyConfig(backend="llama-http", live_url="http://localhost:1", live_model="x")
    )
    result = adapter.generate(_turn_input("teszt"))

    assert result.degraded is False
    assert result.backend == "llama-http"
    assert result.text == "Első sor\nMásodik sor"


def test_llama_http_empty_content_falls_back_via_safe_adapter(monkeypatch):
    payload = {"choices": [{"message": {"content": ""}}]}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response())

    adapter = build_reply_adapter(
        ReplyConfig(backend="llama-http", live_url="http://localhost:1", live_model="x")
    )
    result = adapter.generate(_turn_input("teszt"))

    assert result.degraded is True
    assert result.backend == "deterministic"
