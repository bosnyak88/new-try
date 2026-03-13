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
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    talk_once(runtime, TalkRequest(message="ebben most az a fő probléma hogy a recall még nem elég erős"))


def test_current_state_query_family(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    current_goal = talk_once(runtime, TalkRequest(message="mi a mostani cél?"))
    current_work = talk_once(runtime, TalkRequest(message="akkor most min dolgozunk?"))
    current_posture = talk_once(runtime, TalkRequest(message="ez most chat vagy munka?"))

    assert "mostani cél" in current_goal.turn.assistant_reply.lower()
    assert "rebuild-023" in current_goal.turn.assistant_reply
    assert "mostani munkakeret" in current_work.turn.assistant_reply.lower()
    assert "work" in current_posture.turn.assistant_reply
    assert "Értem az időhivatkozásokat" not in current_goal.turn.assistant_reply


def test_historical_state_recall_family(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    h_obj = talk_once(runtime, TalkRequest(message="mi volt az aktív cél?"))
    h_blk = talk_once(runtime, TalkRequest(message="mi volt a fő probléma?"))
    h_next = talk_once(runtime, TalkRequest(message="mi volt a következő lépés?"))

    for reply in (h_obj.turn.assistant_reply, h_blk.turn.assistant_reply, h_next.turn.assistant_reply):
        assert "Korábbi állapot" in reply
        assert reply.strip() != "Rendben."
        assert "mi volt" not in reply.lower().split("\n")[-1]


def test_uncertainty_and_proposal_semantics(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    talk_once(runtime, TalkRequest(message="lehet hogy a recall a blokk, de nem vagyok benne biztos"))
    talk_once(runtime, TalkRequest(message="jó lenne lezárni ezt a ticketet"))
    talk_once(runtime, TalkRequest(message="talán az lenne a következő lépés hogy megnézzük a trace-t"))

    certainty = talk_once(runtime, TalkRequest(message="mi biztos ebben és mi csak feltételezés?"))
    next_step_certainty = talk_once(runtime, TalkRequest(message="a következő lépés biztos, vagy csak javaslat?"))

    assert "Ami biztos" in certainty.turn.assistant_reply
    assert "Ami inkább javaslat/feltételezés" in certainty.turn.assistant_reply
    assert "javasolt következő lépés" in next_step_certainty.turn.assistant_reply.lower()


def test_continuity_focus_snapshot_trace_alignment(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)
    talk_once(runtime, TalkRequest(message="most csak beszélgetünk"))
    resumed = talk_once(runtime, TalkRequest(message="folytassuk innen"))

    assert "Folytathatjuk a korábbi munkát" in resumed.turn.assistant_reply

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    assert payloads["workframe_state_derived"]["query_family"] in {None, "current_state_query", "workframe_action_query", "historical_state_query", "uncertainty_query"}
    assert payloads["workframe_state_derived"]["objective_status"] == "active"

    snapshot = thread_snapshot_current(runtime)
    focus = thread_focus_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None and snapshot.snapshot.workframe_state is not None
    assert focus.found and focus.focus is not None and focus.focus.workframe_state is not None
    assert snapshot.snapshot.workframe_state.objective_status.value == "active"
    assert focus.focus.workframe_state.objective_status.value == "active"


def test_explicit_blocker_declaration_ack_and_objective_not_demoted(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="most ezen dolgozunk"))
    talk_once(runtime, TalkRequest(message="a cél most a rebuild-023 ticket lezárása"))
    blocker_decl = talk_once(runtime, TalkRequest(message="ebben most az a fő probléma hogy a recall még nem elég erős"))

    assert "explicit fő blokkert" in blocker_decl.turn.assistant_reply
    assert "Aktív cél változatlanul" in blocker_decl.turn.assistant_reply

    certainty = talk_once(runtime, TalkRequest(message="mi biztos ebben és mi csak feltételezés?"))
    assert "Aktív cél: a rebuild-023 ticket lezarasa" in certainty.turn.assistant_reply


def test_hedged_blocker_and_tentative_next_step_stay_uncertain_with_trace(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    hedged_blocker = talk_once(runtime, TalkRequest(message="lehet hogy a recall a blokk, de nem vagyok benne biztos"))
    hedged_step = talk_once(runtime, TalkRequest(message="talán az lenne a következő lépés hogy megnézzük a trace-t"))

    assert "lehetséges blokkerként" in hedged_blocker.turn.assistant_reply.lower()
    assert "javasolt következő lépésként" in hedged_step.turn.assistant_reply.lower()

    trace = trace_last(runtime)
    payloads = {e.event_name: json.loads(e.payload) for e in trace.trace_events}
    assert payloads["workframe_state_derived"]["uncertainty_marked"] is True


def test_weak_objective_proposal_not_generic_filler(tmp_path):
    runtime = _runtime(tmp_path)
    _seed(runtime)

    weak = talk_once(runtime, TalkRequest(message="jó lenne lezárni ezt a ticketet"))
    assert weak.turn.assistant_reply.strip() != "Rendben."
    assert "lehetséges cél-javaslat" in weak.turn.assistant_reply.lower()
