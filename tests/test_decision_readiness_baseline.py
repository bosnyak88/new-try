import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, thread_focus_current, thread_snapshot_current, trace_last


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


def test_explicit_blocker_declaration_stays_on_update_path(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-024 ticket lezárása"))

    blocker = talk_once(runtime, TalkRequest(message="a fő probléma most az hogy nincs még elég erős recall"))

    assert "explicit fő blokkert" in blocker.turn.assistant_reply
    assert "Aktív cél változatlanul" in blocker.turn.assistant_reply


def test_meta_queries_do_not_materialize_open_question_text(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-024 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="a fő probléma most az hogy nincs még elég erős recall"))

    talk_once(runtime, TalkRequest(message="mi hiányzik még?"))
    talk_once(runtime, TalkRequest(message="mi csak feltételezés?"))
    state_probe = talk_once(runtime, TalkRequest(message="milyen nyitott kérdések vannak?"))

    lowered = state_probe.turn.assistant_reply.lower()
    assert "mi hiányzik még" not in lowered
    assert "mi csak feltételezés" not in lowered


def test_evidence_gap_query_is_recognized_and_never_filler(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-024 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="a fő probléma most az hogy nincs még elég erős recall"))

    evidence = talk_once(runtime, TalkRequest(message="mihez nincs még elég bizonyíték?"))

    assert evidence.turn.assistant_reply.strip() != "Rendben."
    assert "Bizonyíték-rés állapot" in evidence.turn.assistant_reply


def test_decision_meta_query_does_not_force_decision_made(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-024 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="a fő probléma most az hogy nincs még elég erős recall"))

    ask_decision = talk_once(runtime, TalkRequest(message="eldőlt már hogy mi legyen a következő lépés?"))
    assert "decision_made" not in ask_decision.turn.assistant_reply

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    wf = payloads["workframe_state_derived"]
    assert wf["decision_state"] != "decision_made"


def test_retained_state_hygiene_across_snapshot_focus_trace(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-024 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="a fő probléma most az hogy nincs még elég erős recall"))
    talk_once(runtime, TalkRequest(message="mi hiányzik még?"))
    talk_once(runtime, TalkRequest(message="milyen döntést kell meghozni?"))
    talk_once(runtime, TalkRequest(message="mit kell most tenni?"))

    snapshot = thread_snapshot_current(runtime)
    focus = thread_focus_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None and snapshot.snapshot.workframe_state is not None
    assert focus.found and focus.focus is not None and focus.focus.workframe_state is not None

    snap_state = snapshot.snapshot.workframe_state
    focus_state = focus.focus.workframe_state

    assert snap_state.blocker_status.value == "explicit"
    assert snap_state.objective_status.value == "active"
    assert snap_state.decision_state.value != "decision_made"
    assert snap_state.open_question_lines == []

    assert focus_state.blocker_status.value == "explicit"
    assert focus_state.objective_status.value == "active"
    assert focus_state.decision_state.value != "decision_made"

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    wf = payloads["workframe_state_derived"]
    assert wf["decision_state"] != "decision_made"
    assert wf["query_family"] in {"workframe_action_query", "decision_readiness_query", None}
