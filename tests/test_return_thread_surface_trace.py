import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, trace_last


def _runtime(tmp_path) -> RuntimeContext:
    return RuntimeContext(
        config=AppConfig(
            name="syntaris",
            environment="test",
            llm=LLMConfig(server_bin_path="", model_path=""),
            paths=AppPaths(data_dir=str(tmp_path / "data"), db_path=str(tmp_path / "data" / "runtime.db")),
            reply=ReplyConfig(),
            conversation=ConversationConfig(),
        )
    )


def test_recall_compare_prompts_do_not_collapse_to_direct_fallback(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a mai fókusz a visszatérés"))

    recall_prev = talk_once(runtime, TalkRequest(message="az előző szálon mi volt?"))
    compare_prev = talk_once(runtime, TalkRequest(message="hasonlítsd össze a mostanit az előző szállal"))

    assert recall_prev.turn.assistant_reply.strip() != "Rendben."
    assert compare_prev.turn.assistant_reply.strip() != "Rendben."

    trace = trace_last(runtime)
    parsed = {event.event_name: json.loads(event.payload) for event in trace.trace_events}
    assert parsed["turn_interpreted"]["kind"] == "compare_previous"
    assert parsed["response_plan_built"]["kind"] in {"structured", "clarification"}
