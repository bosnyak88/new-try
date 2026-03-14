from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, thread_focus_current, thread_snapshot_current


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


def test_memory_maintenance_resolved_and_historical(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a blocker most a config parse hiba"))
    talk_once(runtime, TalkRequest(message="most már más a helyzet: a config parse hiba megszűnt, a live megjelenítés maradt gond"))

    reminder = talk_once(runtime, TalkRequest(message="mi csak emlékeztető értékű már?"))
    assert "applicability" in reminder.turn.assistant_reply.lower() or "alkalmazhat" in reminder.turn.assistant_reply.lower()
    assert "állapot-karbantartás" in reminder.turn.assistant_reply.lower()

    snapshot = thread_snapshot_current(runtime)
    focus = thread_focus_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None
    assert focus.found and focus.focus is not None
    assert snapshot.snapshot.thread_weave_state is not None
    assert focus.focus.thread_weave_state is not None
    assert snapshot.snapshot.thread_weave_state.temporary_state_lifecycle.value in {
        "resolved_temporary_state",
        "superseded_temporary_state",
        "archived_inactive_state",
    }
