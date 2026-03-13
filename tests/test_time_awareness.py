from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, RuntimeContext, TalkRequest
from syntaris.orchestration.talk import talk_once, trace_last


class FixedClock:
    def __init__(self, now: datetime):
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: int) -> None:
        self._now = self._now + timedelta(**kwargs)


def _runtime(tmp_path, clock: FixedClock) -> RuntimeContext:
    config = AppConfig(
        name="syntaris",
        environment="test",
        llm=LLMConfig(server_bin_path="", model_path=""),
        paths=AppPaths(data_dir=str(tmp_path / "data"), db_path=str(tmp_path / "data" / "runtime.db")),
        reply=ReplyConfig(),
        conversation=ConversationConfig(),
    )
    return RuntimeContext(config=config, clock=clock)


def test_daypart_greeting_morning_afternoon_evening(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 6, 30, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime(tmp_path, clock)

    morning = talk_once(runtime, TalkRequest(message="jó reggelt"))
    assert "Jó reggelt" in morning.turn.assistant_reply

    clock._now = datetime(2026, 1, 3, 13, 0, tzinfo=ZoneInfo("UTC"))
    afternoon = talk_once(runtime, TalkRequest(message="szia"))
    assert "délut" in afternoon.turn.assistant_reply.lower()

    clock._now = datetime(2026, 1, 3, 19, 0, tzinfo=ZoneInfo("UTC"))
    evening = talk_once(runtime, TalkRequest(message="szia"))
    assert "est" in evening.turn.assistant_reply.lower()


def test_session_gap_same_day_and_cross_day(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 8, 0, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime(tmp_path, clock)

    talk_once(runtime, TalkRequest(message="folytassuk innen"))
    clock.advance(hours=3)
    same_day = talk_once(runtime, TalkRequest(message="folytassuk innen"))
    assert "eltelt" in same_day.turn.assistant_reply.lower()

    clock.advance(days=1, hours=1)
    cross_day = talk_once(runtime, TalkRequest(message="folytassuk innen"))
    assert "tegnap" in cross_day.turn.assistant_reply.lower()
    assert "vártalak" not in cross_day.turn.assistant_reply.lower()


def test_relative_time_grounding_surfaces_in_trace(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 9, 15, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime(tmp_path, clock)

    result = talk_once(runtime, TalkRequest(message="ma, tegnap, holnap, most, majd"))
    assert result.turn.assistant_reply.strip() != "Rendben."

    trace = trace_last(runtime)
    events = {event.event_name: json.loads(event.payload) for event in trace.trace_events}

    interpreted = events["turn_interpreted"]
    assert set(["ma", "tegnap", "holnap", "most", "majd"]).issubset(set(interpreted["relative_time_terms"]))

    plan = events["response_plan_built"]
    assert plan["daypart"] is not None
    assert plan["continuity_class"] is not None
    assert any(item.startswith("tegnap:") for item in plan["relative_grounding"])


def test_owner_aware_entry_remains_stable(tmp_path):
    clock = FixedClock(datetime(2026, 1, 3, 10, 0, tzinfo=ZoneInfo("UTC")))
    runtime = _runtime(tmp_path, clock)

    checks = [
        "szia syntaris én Árpi vagyok",
        "én terveztem a rendszered",
        "folytassuk innen",
        "segíts a timesheetben",
        "a mai fókusz a syntaris",
    ]
    for msg in checks:
        reply = talk_once(runtime, TalkRequest(message=msg)).turn.assistant_reply
        assert reply.strip() != "Rendben."
