import json

from syntaris.contracts.runtime import (
    AppConfig,
    AppPaths,
    ConversationConfig,
    LLMConfig,
    ReplyConfig,
    RuntimeContext,
    TalkRequest,
)
from syntaris.orchestration.talk import talk_once, thread_focus_current, trace_last


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


def test_relationship_frame_trace_and_focus_are_coherent(tmp_path):
    runtime = _runtime(tmp_path)

    talk_once(runtime, TalkRequest(message="én tervezlek és fejlesztelek"))
    talk_once(runtime, TalkRequest(message="a személyes kognitív rendszerem leszel"))
    talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))

    trace = trace_last(runtime)
    payloads = {event.event_name: json.loads(event.payload) for event in trace.trace_events}

    assert "thread_weave_state_derived" in payloads
    weave = payloads["thread_weave_state_derived"]
    assert weave["relation"] != "relation_unknown"
    assert weave["conclusion_status"] != "no_conclusion_established"
    assert weave["applicability_status"] != "applicability_uncertain"
    assert weave["query_family"] == "relationship_query"

    focus = thread_focus_current(runtime)
    assert focus.found and focus.focus is not None
    assert focus.focus.thread_weave_state is not None
    assert focus.focus.thread_weave_state.relation.value != "relation_unknown"
