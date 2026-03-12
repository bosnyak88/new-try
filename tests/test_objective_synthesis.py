from syntaris.contracts.runtime import (
    AppConfig,
    AppPaths,
    ConversationConfig,
    LLMConfig,
    ReplyConfig,
    RuntimeContext,
    TalkRequest,
)
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


def test_structured_core_point_and_next_step(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="ebből mi a lényeg és mi legyen a következő?"))

    assert "Mi a kérés lényege?" in result.turn.assistant_reply
    assert "Következő lépés" in result.turn.assistant_reply


def test_support_labeling_surfaces_uncertainty(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="mi biztos ebben és mi csak feltételezés?"))

    assert result.turn.degraded is False
    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "[fallback]" not in result.turn.assistant_reply
    assert "Ami biztos" in result.turn.assistant_reply
    assert "Ami nyitott" in result.turn.assistant_reply


def test_diagnose_and_next_step_decomposition(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="mi a fő probléma és mit kell most tenni?"))

    assert result.turn.degraded is False
    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "[fallback]" not in result.turn.assistant_reply
    assert "Mi a fő probléma?" in result.turn.assistant_reply
    assert "Következő lépés" in result.turn.assistant_reply


def test_comparison_with_clear_target_is_structured(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="új szál: work"))
    talk_once(runtime, TalkRequest(message="vissza a default szálra"))
    result = talk_once(runtime, TalkRequest(message="hasonlítsd össze a mostanit az előző szállal"))

    assert result.output_kind != "correction_redirect"
    assert result.turn.degraded is False
    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "[fallback]" not in result.turn.assistant_reply
    assert "Miben egyezik és tér el a két célzott szál?" in result.turn.assistant_reply
    assert "Mostani szál:" in result.turn.assistant_reply
    assert "Előző szál:" in result.turn.assistant_reply
    assert "nincs stabil előzmény" not in result.turn.assistant_reply


def test_comparison_with_ambiguous_target_clarifies(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="hasonlítsd össze"))

    assert "Pontosíts" in result.turn.assistant_reply


def test_trace_exposes_objective_decomposition_evidence_synthesis(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="mi biztos ebben és mi csak feltételezés?"))
    trace = trace_last(runtime)

    names = [event.event_name for event in trace.trace_events]
    assert "objective_framed" in names
    assert "decomposition_built" in names
    assert "evidence_pack_built" in names
    assert "synthesis_plan_built" in names


def test_previous_thread_recall_remains_meaningful(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="új szál: work"))
    talk_once(runtime, TalkRequest(message="vissza a default szálra"))
    result = talk_once(runtime, TalkRequest(message="az előző szálon mi volt?"))

    assert result.turn.degraded is False
    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "[fallback]" not in result.turn.assistant_reply
    assert "Röviden itt tartottunk" in result.turn.assistant_reply

    trace = trace_last(runtime)
    events = {event.event_name: event.payload for event in trace.trace_events}
    assert "response_plan_built" in events
    assert '"kind": "recall"' in events["response_plan_built"]


def test_previous_thread_recall_accent_normalized_phrase(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="új szál: work"))
    talk_once(runtime, TalkRequest(message="vissza a default szálra"))
    result = talk_once(runtime, TalkRequest(message="az elozo szalon mi volt?"))

    assert result.turn.degraded is False
    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "Röviden itt tartottunk" in result.turn.assistant_reply


def test_previous_thread_recall_mojibake_phrase(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="új szál: work"))
    talk_once(runtime, TalkRequest(message="vissza a default szálra"))
    result = talk_once(runtime, TalkRequest(message="az elÅzÅ szÃ¡lon mi volt?"))

    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "Röviden itt tartottunk" in result.turn.assistant_reply


def test_compare_mojibake_phrase_still_structured(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="új szál: work"))
    talk_once(runtime, TalkRequest(message="vissza a default szálra"))
    result = talk_once(runtime, TalkRequest(message="hasonlÃ­tsd Ã¶ssze a mostanit az elÅzÅ szÃ¡llal"))

    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "Mostani szál:" in result.turn.assistant_reply
    assert "Előző szál:" in result.turn.assistant_reply
