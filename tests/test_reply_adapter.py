from syntaris.contracts.runtime import ReplyConfig, TurnInput
from syntaris.reply.factory import build_reply_adapter


def test_deterministic_reply_backend_is_stable():
    adapter = build_reply_adapter(ReplyConfig(backend="deterministic"))

    first = adapter.generate(TurnInput(message="szia"))
    second = adapter.generate(TurnInput(message="szia"))

    assert first.text == second.text
    assert first.backend == "deterministic"
    assert first.degraded is True


def test_llama_http_without_required_config_gracefully_falls_back():
    adapter = build_reply_adapter(ReplyConfig(backend="llama-http", live_url="", live_model=""))

    result = adapter.generate(TurnInput(message="hello"))

    assert result.backend == "deterministic"
    assert result.degraded is True
