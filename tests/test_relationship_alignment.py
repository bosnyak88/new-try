from syntaris.contracts.runtime import (
    AppConfig,
    AppPaths,
    ConversationConfig,
    LLMConfig,
    ReplyConfig,
    RuntimeContext,
    TalkRequest,
)
from syntaris.orchestration.talk import talk_once, thread_snapshot_current


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


def test_explicit_relationship_frame_is_not_filler_and_updates_weave_state(tmp_path):
    runtime = _runtime(tmp_path)

    talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    talk_once(runtime, TalkRequest(message="a te neved syntaris"))
    talk_once(runtime, TalkRequest(message="én tervezlek és fejlesztelek"))
    frame = talk_once(runtime, TalkRequest(message="a személyes kognitív rendszerem leszel"))
    relationship = talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))

    assert frame.turn.assistant_reply.strip() != "Rendben."
    assert "szerep" in frame.turn.assistant_reply.lower() or "kognitív" in frame.turn.assistant_reply.lower()
    assert relationship.turn.assistant_reply.strip() != "Rendben."
    assert "kapcsolat" in relationship.turn.assistant_reply.lower()

    snapshot = thread_snapshot_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None
    assert snapshot.snapshot.thread_weave_state is not None

    weave = snapshot.snapshot.thread_weave_state
    assert weave.relation.value != "relation_unknown"
    assert weave.conclusion_status.value != "no_conclusion_established"
    assert weave.applicability_status.value != "applicability_uncertain"


def test_relationship_alignment_coexists_with_owner_system_queries(tmp_path):
    runtime = _runtime(tmp_path)

    talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    talk_once(runtime, TalkRequest(message="a te neved syntaris"))
    talk_once(runtime, TalkRequest(message="én tervezlek és fejlesztelek"))
    talk_once(runtime, TalkRequest(message="a személyes kognitív rendszerem leszel"))

    who_owner = talk_once(runtime, TalkRequest(message="ki vagyok?"))
    who_system = talk_once(runtime, TalkRequest(message="ki vagy te?"))
    certain = talk_once(runtime, TalkRequest(message="mit tudsz rólam biztosan?"))

    assert "Árpi" in who_owner.turn.assistant_reply
    assert "Árpi" not in who_system.turn.assistant_reply
    assert "syntaris" in who_system.turn.assistant_reply.lower()
    assert "biztos" in certain.turn.assistant_reply.lower()
