import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, trace_last


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


def test_missing_info_open_questions_decision_and_evidence_queries(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-024 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="nincs még meg elég adat a recall minőséghez"))

    missing_info = talk_once(runtime, TalkRequest(message="mi hiányzik még?"))
    open_questions = talk_once(runtime, TalkRequest(message="milyen nyitott kérdések vannak?"))
    assumptions = talk_once(runtime, TalkRequest(message="mi csak feltételezés?"))
    decisions = talk_once(runtime, TalkRequest(message="milyen döntést kell meghozni?"))
    evidence = talk_once(runtime, TalkRequest(message="mihez kell még bizonyíték?"))

    for reply in (missing_info, open_questions, assumptions, decisions, evidence):
        assert "állapot" in reply.turn.assistant_reply.lower() or "hianyzo" in reply.turn.assistant_reply.lower()


def test_trace_contains_decision_readiness_fields(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="nincs még meg elég információ"))
    talk_once(runtime, TalkRequest(message="miért nem tudunk még továbbmenni?"))

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    wf = payloads["workframe_state_derived"]
    assert wf["query_family"] == "decision_readiness_query"
    assert "missing_info_status" in wf
    assert "decision_state" in wf
    assert "evidence_gap_status" in wf
