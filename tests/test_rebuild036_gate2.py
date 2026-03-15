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


def test_chat_lock_and_style_obedience_no_list(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ne dolgozzunk, csak beszélgessünk egy kicsit"))
    result = talk_once(runtime, TalkRequest(message="nem kérek listát, csak reagálj normálisan"))
    reply = result.turn.assistant_reply
    assert "•" not in reply
    assert "- " not in reply

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    plan = payloads["response_plan_built"]
    assert plan["chat_lock_active"] is True
    assert "no_list" in plan["style_constraints"]
    assert plan["reply_shape"] == "casual"


def test_direct_answer_first_no_ack_collapse(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="mit mondtam eddig erről röviden?"))
    assert result.turn.assistant_reply.strip().lower() not in {"rendben.", "ok.", "oke."}

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    plan = payloads["response_plan_built"]
    assert plan["direct_answer_required"] is True
    assert plan["direct_answer_present"] is True
    assert plan["ack_collapse_risk"] is False


def test_anti_hijack_guard_does_not_force_work_mode(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ne dolgozzunk, csak beszélgessünk"))
    result = talk_once(runtime, TalkRequest(message="most fontos, emlékszel hol tartottunk?"))
    assert "Munkakeret:" not in result.turn.assistant_reply

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    assert payloads["response_plan_built"]["anti_hijack_guarded"] is True
