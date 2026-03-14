import json

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, thread_focus_current, thread_snapshot_current, trace_last


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


def _seed(runtime: RuntimeContext) -> None:
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-025 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="a fő probléma most az hogy még nincs elég erős thread-weave logika"))
    talk_once(runtime, TalkRequest(message="közben kitértünk a live loop hibára"))
    talk_once(runtime, TalkRequest(message="de a főszál továbbra is a rebuild-025"))


def test_thread_relation_answers_and_trace(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    rel = talk_once(runtime, TalkRequest(message="mi volt csak mellékszál?"))
    main = talk_once(runtime, TalkRequest(message="mi a főszál most?"))

    assert "Szál-kapcsolat" in rel.turn.assistant_reply
    assert "live loop" in rel.turn.assistant_reply.lower()
    assert "Szál-kapcsolat" in main.turn.assistant_reply
    assert "rebuild-025" in main.turn.assistant_reply.lower()
    assert "unrelated_thread" not in rel.turn.assistant_reply
    assert "unrelated_thread" not in main.turn.assistant_reply

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    assert "thread_weave_state_derived" in payloads
    assert payloads["thread_weave_state_derived"]["relation"] in {
        "main_thread",
        "side_thread",
        "detour",
        "return_to_main",
        "unrelated_thread",
        "relation_unknown",
    }


def test_conclusion_and_applicability_surface(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    concl = talk_once(runtime, TalkRequest(message="mi ebből a tanulság?"))
    appl = talk_once(runtime, TalkRequest(message="ebből mi alkalmazható most?"))

    assert "Konklúzió állapot" in concl.turn.assistant_reply
    assert "kitérő" in concl.turn.assistant_reply.lower()
    assert "Mostani alkalmazhatóság" in appl.turn.assistant_reply
    assert ("minta" in appl.turn.assistant_reply.lower()) or ("kitérő" in appl.turn.assistant_reply.lower())


def test_snapshot_and_focus_include_thread_weave_state(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    snapshot = thread_snapshot_current(runtime)
    focus = thread_focus_current(runtime)

    assert snapshot.found and snapshot.snapshot is not None
    assert focus.found and focus.focus is not None
    assert snapshot.snapshot.thread_weave_state is not None
    assert focus.focus.thread_weave_state is not None


def test_detour_and_return_declarations_are_not_generic_filler(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-025 ticket lezárása"))

    detour = talk_once(runtime, TalkRequest(message="közben kitértünk a live loop hibára"))
    ret = talk_once(runtime, TalkRequest(message="de a főszál továbbra is a rebuild-025"))

    assert detour.turn.assistant_reply.strip() != "Rendben."
    assert "kitérő" in detour.turn.assistant_reply.lower()
    assert "live loop" in detour.turn.assistant_reply.lower()

    assert ret.turn.assistant_reply.strip() != "Rendben."
    assert "főszál" in ret.turn.assistant_reply.lower()
    assert "rebuild-025" in ret.turn.assistant_reply.lower()
