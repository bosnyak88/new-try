import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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


class FixedClock:
    def __init__(self, now: datetime):
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: int) -> None:
        self._now = self._now + timedelta(**kwargs)


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


def _runtime_with_clock(tmp_path, clock: FixedClock) -> RuntimeContext:
    config = AppConfig(
        name="syntaris",
        environment="test",
        llm=LLMConfig(server_bin_path="", model_path=""),
        paths=AppPaths(data_dir=str(tmp_path / "data"), db_path=str(tmp_path / "data" / "runtime.db")),
        reply=ReplyConfig(),
        conversation=ConversationConfig(),
    )
    return RuntimeContext(config=config, clock=clock)


def test_stable_name_query_and_correction_supersedes(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="én Árpi vagyok"))
    correction = talk_once(runtime, TalkRequest(message="javítás: a nevem Péter"))
    result = talk_once(runtime, TalkRequest(message="ki vagyok?"))

    assert correction.turn.assistant_reply.strip() != "Rendben."
    assert "jav" in correction.turn.assistant_reply.lower() or "rögz" in correction.turn.assistant_reply.lower()
    assert "Péter" in result.turn.assistant_reply
    assert "Árpi" not in result.turn.assistant_reply


def test_owner_relation_and_system_role_and_scoped_focus(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="én terveztem a rendszered"))
    relation = talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))
    assert "tervez" in relation.turn.assistant_reply.lower() or "creator" in relation.turn.assistant_reply.lower()

    talk_once(runtime, TalkRequest(message="ez az én személyes rendszerem"))
    role = talk_once(runtime, TalkRequest(message="mi a szereped?"))
    assert "személyes" in role.turn.assistant_reply.lower()

    talk_once(runtime, TalkRequest(message="a mai fókusz a syntaris"))
    focus = talk_once(runtime, TalkRequest(message="mi a mostani fókusz?"))
    assert "syntaris" in focus.turn.assistant_reply.lower()



def test_system_framing_capture_ack_is_not_bare(tmp_path):
    runtime = _runtime(tmp_path)
    result = talk_once(runtime, TalkRequest(message="ez az én személyes rendszerem"))

    assert result.turn.assistant_reply.strip() != "Rendben."
    assert "szerep" in result.turn.assistant_reply.lower() or "rögz" in result.turn.assistant_reply.lower()


def test_relationship_and_role_answers_do_not_overclaim(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="én terveztem a rendszered"))

    relationship = talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))
    assert "tervez" in relationship.turn.assistant_reply.lower()
    assert "társ-rendszer" not in relationship.turn.assistant_reply.lower()

    role = talk_once(runtime, TalkRequest(message="mi a szereped?"))
    assert "nincs" in role.turn.assistant_reply.lower() or "nem" in role.turn.assistant_reply.lower()
    assert "társ-rendszer" not in role.turn.assistant_reply.lower()


def test_what_do_you_know_is_grounded_and_trace_marks_capture(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="én Árpi vagyok"))
    talk_once(runtime, TalkRequest(message="most a munkáról akarok beszélni"))
    answer = talk_once(runtime, TalkRequest(message="mit tudsz rólam biztosan?"))

    assert "explicit" in answer.turn.assistant_reply.lower() or "biztos" in answer.turn.assistant_reply.lower()
    assert "emlékszem mindenre" not in answer.turn.assistant_reply.lower()

    trace = trace_last(runtime)
    payload = {event.event_name: event.payload for event in trace.trace_events}["turn_interpreted"]
    parsed = json.loads(payload)
    assert parsed["memory_query"] == "what_known_certain"

    talk_once(runtime, TalkRequest(message="én terveztem a rendszered"))
    capture_trace = trace_last(runtime)
    names = [event.event_name for event in capture_trace.trace_events]
    assert "explicit_claims_captured" in names


def test_day_scoped_focus_active_then_cross_day_expires(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 8, 0, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime_with_clock(tmp_path, clock)

    talk_once(runtime, TalkRequest(message="a mai fókusz a syntaris"))
    same_day = talk_once(runtime, TalkRequest(message="mi a mostani fókusz?"))
    assert "aktív" in same_day.turn.assistant_reply.lower()
    assert "syntaris" in same_day.turn.assistant_reply.lower()

    clock.advance(days=1)
    next_day = talk_once(runtime, TalkRequest(message="mi a mostani fókusz?"))
    assert "legutóbbi fókusz" in next_day.turn.assistant_reply.lower()
    assert "lejárt" in next_day.turn.assistant_reply.lower()


def test_session_and_thread_direction_answered_from_scoped_state(tmp_path):
    runtime = _runtime(tmp_path)
    talk_once(runtime, TalkRequest(message="ma beszélgetni szeretnék"))
    chat_direction = talk_once(runtime, TalkRequest(message="miről akartam most beszélni?"))
    assert "beszélget" in chat_direction.turn.assistant_reply.lower()

    talk_once(runtime, TalkRequest(message="most a munkáról akarok beszélni"))
    work_direction = talk_once(runtime, TalkRequest(message="miről akartam most beszélni?"))
    assert "munka" in work_direction.turn.assistant_reply.lower()


def test_short_gap_continuity_keeps_temporary_state_active(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 9, 0, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime_with_clock(tmp_path, clock)

    talk_once(runtime, TalkRequest(message="a mai fókusz a syntaris"))
    clock.advance(minutes=20)
    talk_once(runtime, TalkRequest(message="folytassuk innen"))
    result = talk_once(runtime, TalkRequest(message="mi a mostani fókusz?"))
    assert "aktív" in result.turn.assistant_reply.lower()
    assert "syntaris" in result.turn.assistant_reply.lower()


def test_active_state_question_honestly_reports_recent_or_expired(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 9, 0, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime_with_clock(tmp_path, clock)

    talk_once(runtime, TalkRequest(message="most a munkáról akarok beszélni"))
    active = talk_once(runtime, TalkRequest(message="mi maradt aktív mostanról?"))
    assert "releváns" in active.turn.assistant_reply.lower()
    assert "munka" in active.turn.assistant_reply.lower()

    clock.advance(days=2)
    expired = talk_once(runtime, TalkRequest(message="mi maradt aktív mostanról?"))
    assert "már nem aktív" in expired.turn.assistant_reply.lower()
