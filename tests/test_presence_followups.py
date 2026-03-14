from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once


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


def test_identity_relationship_followups_stay_coherent_including_help_query(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    talk_once(runtime, TalkRequest(message="a te neved syntaris"))
    talk_once(runtime, TalkRequest(message="én tervezlek és fejlesztelek"))
    talk_once(runtime, TalkRequest(message="a személyes kognitív rendszerem leszel"))

    who_you = talk_once(runtime, TalkRequest(message="ki vagy te?"))
    who_me = talk_once(runtime, TalkRequest(message="ki vagyok?"))
    relation = talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))
    certain = talk_once(runtime, TalkRequest(message="mit tudsz rólam biztosan?"))
    help_q = talk_once(runtime, TalkRequest(message="miben segítesz nekem?"))

    assert "syntaris" in who_you.turn.assistant_reply.lower()
    assert "Árpi" in who_me.turn.assistant_reply
    assert "kapcsolat" in relation.turn.assistant_reply.lower()
    assert "biztos" in certain.turn.assistant_reply.lower()
    assert "determinisztikus" in help_q.turn.assistant_reply.lower()
    assert "nem találok ki" in help_q.turn.assistant_reply.lower()
