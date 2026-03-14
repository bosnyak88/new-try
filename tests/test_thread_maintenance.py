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


def test_thread_lifecycle_park_return_close(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="tegyünk egy rövid kitérőt a live megjelenítésre"))

    parked = talk_once(runtime, TalkRequest(message="ezt most parkoljuk"))
    assert "parkolt" in parked.turn.assistant_reply.lower()
    assert "thread lifecycle: parked" in parked.turn.assistant_reply.lower()

    returned = talk_once(runtime, TalkRequest(message="vissza a főszálra"))
    assert "főszálra-visszatérés" in returned.turn.assistant_reply.lower()

    closed = talk_once(runtime, TalkRequest(message="lezártuk ezt a részt"))
    assert "lezárt" in closed.turn.assistant_reply.lower()
    assert "thread lifecycle: closed" in closed.turn.assistant_reply.lower()

    snapshot = thread_snapshot_current(runtime)
    focus = thread_focus_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None and snapshot.snapshot.thread_weave_state is not None
    assert focus.found and focus.focus is not None and focus.focus.thread_weave_state is not None
    assert snapshot.snapshot.thread_weave_state.thread_lifecycle.value == "closed"
    assert focus.focus.thread_weave_state.thread_lifecycle.value == "closed"

    trace = trace_last(runtime)
    payload = [e.payload for e in trace.trace_events if e.event_name == "thread_weave_state_derived"][-1]
    assert '"thread_lifecycle": "closed"' in payload
