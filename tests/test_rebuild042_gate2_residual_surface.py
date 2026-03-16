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


def _trace_payload(runtime: RuntimeContext, event_name: str) -> dict:
    tr = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in tr.trace_events}
    return payloads[event_name]


def test_rebuild042_reflective_recap_casual_has_composition_and_natural_surface(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a gate 2 continuity javítás"))
    talk_once(runtime, TalkRequest(message="a blocker most a recap hijack"))
    turn = talk_once(runtime, TalkRequest(message="fáradt vagyok, de közben hol tartunk, és most csak beszélgetnék"))

    text = turn.turn.assistant_reply.lower()
    assert "fáradt" in text or "megterhelő" in text
    assert "röviden" in text
    assert "workframe" not in text
    assert "menu" not in text

    plan = _trace_payload(runtime, "response_plan_built")
    assert plan["composition_recap_used"] is True
    assert plan["composition_reflective_lead_used"] is True
    assert plan["surface_hijack_guarded"] is True


def test_rebuild042_recap_and_next_step_are_combined_not_recap_only(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a gate 2 continuity javítás"))
    talk_once(runtime, TalkRequest(message="a blocker most az hogy túl mechanikus a recap"))
    talk_once(runtime, TalkRequest(message="a következő lépés most a response-plan mixed continuity hardening"))
    turn = talk_once(runtime, TalkRequest(message="hol tartunk most és mi a következő lépés?"))

    text = turn.turn.assistant_reply.lower()
    assert "röviden" in text or "itt tartunk" in text
    assert "következő lépés" in text
    assert "csak ennyit látok" not in text

    plan = _trace_payload(runtime, "response_plan_built")
    assert plan["composition_recap_used"] is True
    assert plan["composition_next_step_used"] is True


def test_rebuild042_reflective_direct_blocker_honors_brief_and_no_list(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a blocker most a config parse hiba"))
    turn = talk_once(runtime, TalkRequest(message="szétesett vagyok, de röviden mondd mi a blocker, ne listázd"))

    text = turn.turn.assistant_reply.lower()
    assert "config parse hiba" in text
    assert "•" not in turn.turn.assistant_reply
    assert "- " not in turn.turn.assistant_reply

    plan = _trace_payload(runtime, "response_plan_built")
    assert "brief" in plan["style_constraints"]
    assert "no_list" in plan["style_constraints"]


def test_rebuild042_noisy_hu_mixed_turn_stays_natural_and_routed(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a gate 2 continuity javítás"))
    talk_once(runtime, TalkRequest(message="a következő lépés most a noisy hu mixed-turn regresszió zárása"))
    turn = talk_once(runtime, TalkRequest(message="hol tartunk most es mi a kov lepes csak reagalj normalisan"))

    text = turn.turn.assistant_reply.lower()
    assert "röviden" in text or "itt tartunk" in text
    assert "következő lépés" in text
    assert "workframe" not in text

    plan = _trace_payload(runtime, "response_plan_built")
    assert plan["surface_hijack_guarded"] is True


def test_rebuild042_pure_recap_path_still_works(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a gate 2 continuity javítás"))
    talk_once(runtime, TalkRequest(message="a blocker most a recap hijack"))
    turn = talk_once(runtime, TalkRequest(message="mire jutottunk röviden?"))

    text = turn.turn.assistant_reply.lower()
    assert "röviden" in text or "itt tartunk" in text

    plan = _trace_payload(runtime, "response_plan_built")
    assert plan["composition_recap_used"] is True


def test_rebuild042_noisy_recap_next_step_deduplicates_lines(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="hol tartunk most és mi a következő lépés?"))
    talk_once(runtime, TalkRequest(message="fáradt vagyok, de közben hol tartunk, és most csak beszélgetnék"))
    turn = talk_once(runtime, TalkRequest(message="hol tartunk es mi a kov lepes"))

    text = turn.turn.assistant_reply
    target = "Most még nincs stabil next-stepem; egy rövid célmondattal pontosíts, és abból adok konkrét lépést."
    assert text.count(target) <= 1

