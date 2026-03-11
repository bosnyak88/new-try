from syntaris.contracts.runtime import ReplyConfig, TurnInput
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
