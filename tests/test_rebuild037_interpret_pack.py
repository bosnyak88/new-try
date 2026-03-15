import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.interpret_pack import build_interpret_pack
from syntaris.orchestration.talk import talk_once, trace_last


def _runtime(tmp_path) -> RuntimeContext:
    config = AppConfig(
        name="syntaris",
        environment="test",
        llm=LLMConfig(server_bin_path="", model_path=""),
        paths=AppPaths(data_dir=str(tmp_path / "data"), db_path=str(tmp_path / "data" / "runtime.db")),
        reply=ReplyConfig(),
        conversation=ConversationConfig(),
    )
    return RuntimeContext(config=config)


def test_interpret_pack_segments_noisy_hu_units():
    pack = build_interpret_pack("fáradt vagyok, de közben hol tartunk, és most csak beszélgetnék")
    assert len(pack.utterance_units) >= 2
    assert any(u.role == "thread_hint" for u in pack.utterance_units)
    assert "casual_only" in pack.style_constraints_effective


def test_interpret_pack_mixed_turn_keeps_direct_plus_chat_lock():
    pack = build_interpret_pack("oké, ne listázd, röviden mondd, amúgy mi a blocker")
    names = [c.name for c in pack.candidate_intents]
    assert "direct_answer" in names
    assert "chat_lock" in names
    assert "mixed_turn_direct_plus_chat_lock" in pack.risk_flags


def test_turn_trace_contains_interpret_pack_summary(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="oké, ne listázd, röviden mondd, amúgy mi a blocker"))
    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    interpreted = payloads["turn_interpreted"]
    assert interpreted["unit_count"] >= 2
    assert interpreted["selected_intent"] is not None
    assert isinstance(interpreted["workframe_candidate_summary"], list)


def test_ambiguous_resume_prefers_clarification_over_confident_wrong_route(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="nem tudom pontosan mit akarok, de folytassuk innen és mondd el röviden"))
    assert "pontosíts" in result.turn.assistant_reply.lower() or "pontosits" in result.turn.assistant_reply.lower()
