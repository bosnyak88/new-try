from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
import json

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


def test_hol_tartottunk_routes_to_recall_not_ordinary(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a mai fókusz a trace őszinteség"))
    out = talk_once(runtime, TalkRequest(message="hol tartottunk?"))
    assert out.turn.assistant_reply.strip() != "Rendben."

    trace = trace_last(runtime)
    plan = json.loads({e.event_name: e.payload for e in trace.trace_events}["response_plan_built"])
    assert plan["kind"] == "recall"
