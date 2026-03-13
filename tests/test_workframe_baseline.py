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
    work = talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    objective = talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="ebben most az a fő probléma hogy a recall még nem elég erős"))

    assert "aktív munkaszálként" in work.turn.assistant_reply.lower()
    assert "aktív célt rögzítem" in objective.turn.assistant_reply.lower()

    blocker = talk_once(runtime, TalkRequest(message="mi a fő probléma?"))
    assert "Munkakeret" in blocker.turn.assistant_reply
    assert "Aktív cél" in blocker.turn.assistant_reply
    assert "Fő blokkert" in blocker.turn.assistant_reply

    next_step = talk_once(runtime, TalkRequest(message="mi a következő lépés?"))
    stuck = talk_once(runtime, TalkRequest(message="miben akadtunk el?"))
    assert "Következő lépés" in next_step.turn.assistant_reply
    assert "Javaslat" in next_step.turn.assistant_reply
    assert "Aktív cél: a rebuild-023 ticket lezarasa" in stuck.turn.assistant_reply


def test_chat_shift_acknowledged_without_generic_time_fallback(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    chat = talk_once(runtime, TalkRequest(message="most csak beszélgetünk"))

    assert "beszélgető módra váltunk" in chat.turn.assistant_reply
    assert "Értem az időhivatkozásokat" not in chat.turn.assistant_reply


def test_resume_keeps_grounded_context_and_trace_snapshot_focus_alignment(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="ebben most az a fő probléma hogy a recall még nem elég erős"))
    talk_once(runtime, TalkRequest(message="most csak beszélgetünk"))
    resumed = talk_once(runtime, TalkRequest(message="folytassuk innen"))

    assert "Folytathatjuk a korábbi munkát" in resumed.turn.assistant_reply
    assert "rebuild-023 ticket lezarasa" in resumed.turn.assistant_reply

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    assert "workframe_state_derived" in payloads
    assert payloads["workframe_state_derived"]["objective_status"] == "active"

    snapshot = thread_snapshot_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None
    assert snapshot.snapshot.workframe_state is not None
    assert snapshot.snapshot.workframe_state.objective_status.value == "active"

    focus = thread_focus_current(runtime)
    assert focus.found and focus.focus is not None
    assert focus.focus.workframe_state is not None
    assert focus.focus.workframe_state.objective_status.value == "active"
