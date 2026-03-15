import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, trace_last, thread_snapshot_current


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


def _plan_payload(runtime: RuntimeContext) -> dict:
    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    return payloads["response_plan_built"]


def test_style_constraint_no_certainty_split_is_hard_override(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a gate2 finisher"))
    talk_once(runtime, TalkRequest(message="lehet hogy az orchestration a blokk"))

    result = talk_once(runtime, TalkRequest(message="ne bontsd biztosra meg feltételezésre, csak mondd el"))
    reply = result.turn.assistant_reply.lower()
    assert "ami biztos" not in reply
    assert "feltételezés" not in reply

    plan = _plan_payload(runtime)
    assert "no_certainty_split" in plan["style_constraints"]


def test_brief_recap_is_answered_not_clarified(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a gate2 recap teszt"))

    q1 = talk_once(runtime, TalkRequest(message="mit mondtam eddig erről röviden?"))
    q2 = talk_once(runtime, TalkRequest(message="emlékszel mire jutottunk, de röviden mondd"))

    assert "röviden itt tartunk" in q1.turn.assistant_reply.lower()
    assert "pontosíts" not in q1.turn.assistant_reply.lower()
    assert "röviden itt tartunk" in q2.turn.assistant_reply.lower()


def test_noisy_hu_chat_lock_and_anti_hijack(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="most ne dolgzunk csak beszelgesunk pls"))
    assert "beszélget" in result.turn.assistant_reply.lower() or "beszelget" in result.turn.assistant_reply.lower()

    plan = _plan_payload(runtime)
    assert plan["chat_lock_active"] is True


def test_mixed_mode_keeps_direct_question(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="csak reagálj normálisan, meg amúgy mi a blocker"))
    reply = result.turn.assistant_reply.lower()
    assert "blokk" in reply or "fő blokker" in reply or "fo blokker" in reply
    plan = _plan_payload(runtime)
    assert plan["direct_answer_present"] is True


def test_reflective_input_not_empty_ack(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="fáradt vagyok"))
    assert result.turn.assistant_reply.strip().lower() not in {"rendben.", "ok.", "oke."}


def test_next_step_user_facing_not_taxonomy_dump(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="mi a következő lépés?"))
    reply = result.turn.assistant_reply.lower()
    assert "munkakeret:" not in reply
    assert "status" not in reply


def test_reply_trace_snapshot_coherence_for_problem_turn(tmp_path):
    runtime = _runtime(tmp_path)
    turn = talk_once(runtime, TalkRequest(message="csak reagálj normálisan, meg amúgy mi a blocker"))
    plan = _plan_payload(runtime)
    snap = thread_snapshot_current(runtime)
    assert snap.found and snap.snapshot is not None
    last = snap.snapshot.snapshot_lines[-1]
    assert last.turn_id == turn.turn.turn_id
    assert last.assistant_reply == turn.turn.assistant_reply
    assert plan["reply_shape"] == "casual"
