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


def test_owner_and_system_identity_statements_are_captured_without_generic_filler(tmp_path):
    runtime = _runtime(tmp_path)

    owner = talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    system = talk_once(runtime, TalkRequest(message="a te neved syntaris"))
    who_owner = talk_once(runtime, TalkRequest(message="ki vagyok?"))
    who_system = talk_once(runtime, TalkRequest(message="ki vagy te?"))

    assert owner.turn.assistant_reply.strip() != "Rendben."
    assert "Árpi" in owner.turn.assistant_reply
    assert system.turn.assistant_reply.strip() != "Rendben."
    assert "syntaris" in system.turn.assistant_reply.lower()
    assert "Árpi" in who_owner.turn.assistant_reply
    assert "syntaris" in who_system.turn.assistant_reply.lower()



def test_relationship_framing_and_coherence_queries_stay_aligned(tmp_path):
    runtime = _runtime(tmp_path)

    talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    owner_relation = talk_once(runtime, TalkRequest(message="én tervezlek és fejlesztelek"))
    system_role = talk_once(runtime, TalkRequest(message="te a személyes kognitív rendszerem leszel"))
    relationship = talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))
    certain = talk_once(runtime, TalkRequest(message="mit tudsz rólam biztosan?"))

    assert owner_relation.turn.assistant_reply.strip() != "Rendben."
    assert "tervez" in owner_relation.turn.assistant_reply.lower() or "fejleszt" in owner_relation.turn.assistant_reply.lower()
    assert system_role.turn.assistant_reply.strip() != "Rendben."
    assert "személyes kognitív" in system_role.turn.assistant_reply.lower()

    relationship_lower = relationship.turn.assistant_reply.lower()
    assert "árpi" in relationship_lower
    assert "tervez" in relationship_lower or "fejleszt" in relationship_lower
    assert "szerep" in relationship_lower

    certain_lower = certain.turn.assistant_reply.lower()
    assert "explicit" in certain_lower
    assert "biztos" in certain_lower
    assert "emlékszem mindenre" not in certain_lower

    trace = trace_last(runtime)
    payload = {event.event_name: event.payload for event in trace.trace_events}["turn_interpreted"]
    parsed = json.loads(payload)
    assert parsed["memory_query"] == "what_known_certain"
