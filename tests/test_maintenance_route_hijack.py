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


def test_maintenance_updates_do_not_fall_back_to_time_reference(tmp_path):
    runtime = _runtime(tmp_path)

    setup = talk_once(runtime, TalkRequest(message="most a rebuild-028 follow-up maintenance fixen dolgozunk"))
    set_blocker = talk_once(runtime, TalkRequest(message="a blocker most a config parse hiba"))
    ask_blocker = talk_once(runtime, TalkRequest(message="mi a blocker most?"))
    replace = talk_once(runtime, TalkRequest(message="most már más a helyzet: a config parse hiba megszűnt, a live megjelenítés maradt gond"))

    for result in (setup, set_blocker, ask_blocker, replace):
        assert "Értem az időhivatkozásokat" not in result.turn.assistant_reply

    assert "aktív munkaszál" in setup.turn.assistant_reply.lower()
    assert "explicit fő blokkert" in set_blocker.turn.assistant_reply.lower()
    assert "mostani" in ask_blocker.turn.assistant_reply.lower() and "config parse hiba" in ask_blocker.turn.assistant_reply.lower()


def test_scenario_a_state_completion_for_blocker_and_conclusion(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most a rebuild-028 follow-up maintenance fixen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a blocker most a config parse hiba"))
    talk_once(runtime, TalkRequest(message="most már más a helyzet: a config parse hiba megszűnt, a live megjelenítés maradt gond"))

    appl = talk_once(runtime, TalkRequest(message="a korábbi blocker még alkalmazható most?"))
    remained = talk_once(runtime, TalkRequest(message="mi maradt érvényes a korábbi tanulságból?"))
    reminder = talk_once(runtime, TalkRequest(message="mi csak emlékeztető értékű már?"))
    overwrite = talk_once(runtime, TalkRequest(message="felülírja ezt az új helyzet?"))
    current = talk_once(runtime, TalkRequest(message="mi a blocker most?"))

    for result in (appl, remained, reminder, overwrite, current):
        assert "Értem az időhivatkozásokat" not in result.turn.assistant_reply

    assert "superseded_by_new_context" in appl.turn.assistant_reply.lower() or "not_applicable_now" in appl.turn.assistant_reply.lower()
    assert "konklúzió" in remained.turn.assistant_reply.lower()
    assert "config parse hiba" in current.turn.assistant_reply.lower() or "live megjelenites" in current.turn.assistant_reply.lower()

    snapshot = thread_snapshot_current(runtime)
    focus = thread_focus_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None
    assert focus.found and focus.focus is not None
    assert snapshot.snapshot.workframe_state is not None
    assert focus.focus.workframe_state is not None
    assert snapshot.snapshot.workframe_state.blocker_status.value != "none"
    assert focus.focus.workframe_state.blocker_status.value != "none"
    assert snapshot.snapshot.thread_weave_state is not None
    assert focus.focus.thread_weave_state is not None
    assert snapshot.snapshot.thread_weave_state.conclusion_status.value != "no_conclusion_established"

    trace = trace_last(runtime)
    names = [e.event_name for e in trace.trace_events]
    assert "workframe_state_derived" in names
    assert "thread_weave_state_derived" in names
