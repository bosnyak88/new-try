from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once


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


def test_applicability_superseded_by_new_context(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="a fő probléma most az hogy a config parse hiba blokkol"))
    talk_once(runtime, TalkRequest(message="most már más a helyzet: a config parse hiba megszűnt, a live megjelenítés maradt gond"))

    appl = talk_once(runtime, TalkRequest(message="a korábbi blocker még alkalmazható most?"))
    text = appl.turn.assistant_reply.lower()
    assert "superseded_by_new_context" in text or "not_applicable_now" in text
    assert "állapot-karbantartás" in text


def test_applicability_partial_and_current(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="közben kitértünk a live loop hibára"))
    partial = talk_once(runtime, TalkRequest(message="ebből mi alkalmazható most?"))
    assert "applicability_uncertain" in partial.turn.assistant_reply.lower()

    talk_once(runtime, TalkRequest(message="de a főszál továbbra is a rebuild-027"))
    current = talk_once(runtime, TalkRequest(message="ebből mi alkalmazható most?"))
    assert "applicable_now" in current.turn.assistant_reply.lower()
