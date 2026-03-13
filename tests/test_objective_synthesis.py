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
    assert '"kind": "recall_previous"' in events["turn_interpreted"]
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

    trace = trace_last(runtime)
    events = {event.event_name: event.payload for event in trace.trace_events}
    assert '"kind": "compare_previous"' in events["turn_interpreted"]
    assert '"selected_strategy": "structured_answer"' in events["answer_strategy_selected"]


def test_personal_entry_simple_greeting_is_hungarian_and_non_fallback(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="szia"))

    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "Szia" in result.turn.assistant_reply
    assert "miben" in result.turn.assistant_reply.lower()


def test_personal_entry_self_intro_acknowledges_name_without_fake_memory(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="én Árpi vagyok"))

    assert "Árpi" in result.turn.assistant_reply
    assert "emlékszem" not in result.turn.assistant_reply.lower()
    assert result.turn.assistant_reply.count("?") <= 1


def test_personal_entry_creator_framing_and_return_route_are_distinct(tmp_path):
    runtime = _runtime(tmp_path)

    creator = talk_once(runtime, TalkRequest(message="én terveztem a rendszered"))
    back = talk_once(runtime, TalkRequest(message="folytassuk innen"))

    assert "tervezed" in creator.turn.assistant_reply or "fejleszted" in creator.turn.assistant_reply
    assert "visszakapcsoltam" in back.turn.assistant_reply
    assert creator.turn.assistant_reply != back.turn.assistant_reply


def test_personal_entry_trace_and_identity_persistence(tmp_path):
    runtime = _runtime(tmp_path)

    talk_once(runtime, TalkRequest(message="szia syntaris én Árpi vagyok"))
    trace = trace_last(runtime)
    payload = {event.event_name: event.payload for event in trace.trace_events}["turn_interpreted"]
    parsed = json.loads(payload)
    assert parsed["kind"] == "personal_entry"
    assert parsed["personal_entry_kind"] == "self_intro"
    assert parsed["owner_name"] == "Árpi"

    result = talk_once(runtime, TalkRequest(message="szia"))
    assert "Árpi" in result.turn.assistant_reply


def test_intake_bridge_personal_chat_and_help_and_focus_and_resume_are_distinct(tmp_path):
    runtime = _runtime(tmp_path)

    intro = talk_once(runtime, TalkRequest(message="szia syntaris én Árpi vagyok"))
    chat = talk_once(runtime, TalkRequest(message="ma beszélgetni szeretnék"))
    help_turn = talk_once(runtime, TalkRequest(message="segíts a timesheetben"))
    focus = talk_once(runtime, TalkRequest(message="a mai fókusz a syntaris"))
    resume = talk_once(runtime, TalkRequest(message="folytassuk a syntarist"))

    assert intro.turn.assistant_reply.strip() != "Rendben."
    assert chat.turn.assistant_reply.strip() != "Rendben."
    assert help_turn.turn.assistant_reply.strip() != "Rendben."
    assert focus.turn.assistant_reply.strip() != "Rendben."
    assert resume.turn.assistant_reply.strip() != "Rendben."

    assert "foglalkoztat" in chat.turn.assistant_reply.lower()
    assert "elakadt" in help_turn.turn.assistant_reply.lower() or "konkrét" in help_turn.turn.assistant_reply.lower()
    assert "fókusz" in focus.turn.assistant_reply.lower()
    assert "folytassuk" in resume.turn.assistant_reply.lower() or "fonalat" in resume.turn.assistant_reply.lower()

    for reply in (chat.turn.assistant_reply, help_turn.turn.assistant_reply, focus.turn.assistant_reply, resume.turn.assistant_reply):
        assert reply.count("?") <= 1


def test_focus_direction_intake_captured_in_trace(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most a munkáról akarok beszélni"))

    trace = trace_last(runtime)
    payload = {event.event_name: event.payload for event in trace.trace_events}["turn_interpreted"]
    parsed = json.loads(payload)

    assert parsed["kind"] == "personal_entry"
    assert parsed["personal_entry_kind"] == "focus_setting_intake"
    assert parsed["declared_direction"] == "munka"
