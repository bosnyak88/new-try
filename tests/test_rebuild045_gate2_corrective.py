import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.live_loop import run_live_loop, run_live_loop_interactive
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


def _plan_payload(runtime: RuntimeContext) -> dict:
    tr = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in tr.trace_events}
    return payloads["response_plan_built"]


def test_rebuild045_relative_time_does_not_hijack_direct_status_question(tmp_path):
    runtime = _runtime(tmp_path)
    turn = talk_once(runtime, TalkRequest(message="Most akkor kész vagy nincs?"))

    text = turn.turn.assistant_reply
    assert "Értem az időhivatkozásokat" not in text
    assert text.lower().startswith("még nincs kész")



def test_rebuild045_internal_state_labels_not_leaked_to_surface(tmp_path):
    runtime = _runtime(tmp_path)
    turn = talk_once(runtime, TalkRequest(message="Mi hiányzik most a Gate 2 lezárásához?"))

    text = turn.turn.assistant_reply
    for leaked in (
        "no_missing_info_established",
        "no_open_question_established",
        "unknown_or_not_established",
        "no_decision_established",
        "evidence_sufficient",
    ):
        assert leaked not in text



def test_rebuild045_recap_next_step_grounded_not_plain_recap(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a blocker most a direct-answer-first bukás"))
    turn = talk_once(runtime, TalkRequest(message="Hol tartunk most és mi a következő lépés?"))

    text = turn.turn.assistant_reply.lower()
    assert "röviden itt tartunk" in text
    assert "következő lépés" in text



def test_rebuild045_live_loop_empty_input_is_silent_and_exit_clean(tmp_path):
    runtime = _runtime(tmp_path)

    result = run_live_loop(runtime, ["", "   ", "szia", "/kilep"])
    errors = [item for item in result.outputs if item.kind == "error"]
    assert not errors
    assert result.outputs[-1].kind == "exit"



def test_rebuild045_live_loop_keyboard_interrupt_treated_as_exit(tmp_path):
    runtime = _runtime(tmp_path)

    def _interrupt(_prompt: str) -> str:
        raise KeyboardInterrupt

    result = run_live_loop_interactive(runtime, input_func=_interrupt)
    assert result.outputs[-1].kind == "exit"



def test_rebuild045_trace_direct_answer_present_matches_direct_surface(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="Mi a fő gond jelenleg?"))

    plan = _plan_payload(runtime)
    assert plan["direct_answer_present"] is True
    assert plan["clarification_needed"] is False


def test_rebuild045_reflective_continuity_does_not_fall_into_time_hijack(tmp_path):
    runtime = _runtime(tmp_path)
    turn = talk_once(runtime, TalkRequest(message="Őszintén most tele a fejem, de kérlek normálisan vedd fel a fonalat."))

    text = turn.turn.assistant_reply.lower()
    assert "értem az időhivatkozásokat" not in text
    assert "röviden" in text or "fonalat" in text
