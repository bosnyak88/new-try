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


def test_workframe_objective_blocker_next_step_flow(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="ebben most az a fő probléma hogy a recall még nem elég erős"))

    blocker = talk_once(runtime, TalkRequest(message="mi a fő probléma?"))
    assert "Munkakeret" in blocker.turn.assistant_reply
    assert "Fő blokkert" in blocker.turn.assistant_reply

    next_step = talk_once(runtime, TalkRequest(message="mi a következő lépés?"))
    assert "Következő lépés" in next_step.turn.assistant_reply
    assert "Javaslat" in next_step.turn.assistant_reply


def test_workframe_honest_when_no_objective_or_blocker(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most csak beszélgetünk"))
    result = talk_once(runtime, TalkRequest(message="mit kell most tenni?"))

    assert "nincs még egyértelműen rögzítve" in result.turn.assistant_reply
    assert "nincs megalapozottan rögzítve" in result.turn.assistant_reply


def test_workframe_trace_snapshot_focus_alignment(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="írj egy rövid tervet"))

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    assert "workframe_state_derived" in payloads
    assert payloads["workframe_state_derived"]["workframe"] in {"planning", "work"}

    snapshot = thread_snapshot_current(runtime)
    assert snapshot.found
    assert snapshot.snapshot is not None

    focus = thread_focus_current(runtime)
    assert focus.found
    assert focus.focus is not None
