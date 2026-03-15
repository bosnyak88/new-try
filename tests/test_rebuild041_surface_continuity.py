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


def _plan_payload(runtime: RuntimeContext) -> dict:
    tr = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in tr.trace_events}
    return payloads["response_plan_built"]


def test_rebuild041_mixed_reflective_recap_next_step(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a gate 2 continuity javítás"))
    talk_once(runtime, TalkRequest(message="a blocker most a recap hijack"))
    turn = talk_once(runtime, TalkRequest(message="fáradt vagyok, de közben hol tartunk, és most csak beszélgetnék"))

    text = turn.turn.assistant_reply.lower()
    assert "röviden" in text or "itt tartunk" in text
    assert "fáradt" in text or "megterhelő" in text
    assert "beszélgető módban maradunk" not in text

    plan = _plan_payload(runtime)
    assert plan["composition_recap_used"] is True
    assert plan["composition_reflective_lead_used"] is True
    assert plan["surface_hijack_guarded"] is True


def test_rebuild041_recap_plus_next_step_not_recap_only(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a cél most a gate 2 continuity javítás"))
    talk_once(runtime, TalkRequest(message="a következő lépés most az hogy frissitsuk a response plan trace mezőket"))
    turn = talk_once(runtime, TalkRequest(message="hol tartunk most és mi a következő lépés?"))

    text = turn.turn.assistant_reply.lower()
    assert "következő lépés" in text or "next-step" in text
    assert "röviden" in text or "itt tartunk" in text

    plan = _plan_payload(runtime)
    assert plan["composition_recap_used"] is True
    assert plan["composition_next_step_used"] is True


def test_rebuild041_reflective_casual_is_natural(tmp_path):
    runtime = _runtime(tmp_path)
    turn = talk_once(runtime, TalkRequest(message="most kicsit szétesett vagyok, csak reagálj normálisan"))

    text = turn.turn.assistant_reply.lower()
    assert "beszélgető módban maradunk" not in text
    assert "szétes" in text or "megterhelő" in text or "értem" in text


def test_rebuild041_blocker_brief_no_list_stays_direct(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a blocker most a config parse hiba"))
    turn = talk_once(runtime, TalkRequest(message="ne listázd, röviden mondd: mi a blocker?"))

    text = turn.turn.assistant_reply.lower()
    assert "config parse hiba" in text
    assert "•" not in turn.turn.assistant_reply
