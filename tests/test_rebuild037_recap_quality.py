import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
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


def _plan(runtime: RuntimeContext) -> dict:
    tr = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in tr.trace_events}
    return payloads["response_plan_built"]


def test_recap_quality_sequence_a(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ne dolgozzunk, csak beszélgessünk"))
    talk_once(runtime, TalkRequest(message="fáradt vagyok"))
    recap = talk_once(runtime, TalkRequest(message="mit mondtam eddig erről röviden?"))

    text = recap.turn.assistant_reply.lower()
    assert "röviden itt tartunk" in text
    assert "fáradt" in text
    assert "beszélget" in text or "kötetlen" in text

    plan = _plan(runtime)
    assert plan["kind"] == "recall"
    assert (plan.get("recap_included_turn_count") or 0) >= 2


def test_recap_quality_sequence_b_not_last_turn_only(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="csak reagálj normálisan, meg amúgy mi a blocker"))
    talk_once(runtime, TalkRequest(message="most ne dolgzunk csak beszelgesunk pls"))
    recap = talk_once(runtime, TalkRequest(message="emlékszel mire jutottunk, de röviden mondd"))

    text = recap.turn.assistant_reply.lower()
    assert "blokker" in text or "blocker" in text
    assert "beszélget" in text or "kötetlen" in text


def test_recap_avoids_meta_recap_loop(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="ne bontsd biztosra meg feltételezésre, csak mondd el"))
    first = talk_once(runtime, TalkRequest(message="mit mondtam eddig erről röviden?"))
    second = talk_once(runtime, TalkRequest(message="emlékszel mire jutottunk, de röviden mondd"))

    assert "mit mondtam eddig erről röviden" not in second.turn.assistant_reply.lower()
    assert first.turn.assistant_reply != second.turn.assistant_reply


def test_recap_trace_window_is_meaningful(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ne dolgozzunk, csak beszélgessünk"))
    talk_once(runtime, TalkRequest(message="fáradt vagyok"))
    talk_once(runtime, TalkRequest(message="csak reagálj normálisan, meg amúgy mi a blocker"))
    talk_once(runtime, TalkRequest(message="mit mondtam eddig erről röviden?"))

    plan = _plan(runtime)
    assert (plan.get("recap_source_turn_count") or 0) >= 3
    assert (plan.get("recap_included_turn_count") or 0) >= 2
