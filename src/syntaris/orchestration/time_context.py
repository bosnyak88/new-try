from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from syntaris.contracts.runtime import (
    ContinuityClass,
    DaypartKind,
    RelativeTimeGrounding,
    RuntimeContext,
    SessionGapKind,
    TimeContext,
)


@dataclass(frozen=True)
class RelativeTerms:
    terms: list[str]


def _resolve_zoneinfo(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(
            f"Időzóna-adat nem elérhető ehhez: {timezone_name}. "
            "Ellenőrizd a rendszer tzadatát vagy a Python tzdata csomagot."
        ) from exc


def resolve_now_local(context: RuntimeContext) -> datetime:
    now_utc = context.clock.now()
    tz = _resolve_zoneinfo(context.config.time.timezone)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    return now_utc.astimezone(tz)


def resolve_daypart(now_local: datetime) -> DaypartKind:
    hour = now_local.hour
    if 5 <= hour <= 8:
        return DaypartKind.REGGEL
    if 9 <= hour <= 11:
        return DaypartKind.DELELOTT
    if 12 <= hour <= 17:
        return DaypartKind.DELUTAN
    if 18 <= hour <= 22:
        return DaypartKind.ESTE
    return DaypartKind.EJJEL


def resolve_gap_kind(now_local: datetime, last_turn_at: datetime | None) -> tuple[SessionGapKind, int | None]:
    if last_turn_at is None:
        return SessionGapKind.UNKNOWN, None
    delta = now_local - last_turn_at
    minutes = max(0, int(delta.total_seconds() // 60))
    if now_local.date() != last_turn_at.date():
        return SessionGapKind.CROSS_DAY, minutes
    if minutes < 5:
        return SessionGapKind.IMMEDIATE, minutes
    if minutes < 60:
        return SessionGapKind.SHORT, minutes
    return SessionGapKind.SAME_DAY_LONG, minutes


def continuity_from_gap(gap_kind: SessionGapKind) -> ContinuityClass:
    if gap_kind == SessionGapKind.IMMEDIATE:
        return ContinuityClass.SAME_SESSION
    if gap_kind == SessionGapKind.SHORT:
        return ContinuityClass.SHORT_GAP_SAME_DAY
    if gap_kind == SessionGapKind.SAME_DAY_LONG:
        return ContinuityClass.LONG_GAP_SAME_DAY
    if gap_kind == SessionGapKind.CROSS_DAY:
        return ContinuityClass.CROSS_DAY
    return ContinuityClass.NEW_OR_UNKNOWN


def ground_relative_terms(now_local: datetime, terms: list[str]) -> list[RelativeTimeGrounding]:
    grounded: list[RelativeTimeGrounding] = []
    for term in terms:
        if term == "most":
            label = "jelen időpont"
        elif term == "ma":
            label = f"mai nap ({now_local.date().isoformat()})"
        elif term == "tegnap":
            label = f"tegnapi nap ({(now_local - timedelta(days=1)).date().isoformat()})"
        elif term == "holnap":
            label = f"holnapi nap ({(now_local + timedelta(days=1)).date().isoformat()})"
        elif term == "majd":
            label = "későbbi, nem konkretizált idő"
        elif term == "ma reggel":
            label = f"ma reggel ({now_local.date().isoformat()}, reggel)"
        elif term == "ma délután":
            label = f"ma délután ({now_local.date().isoformat()}, délután)"
        else:
            continue
        grounded.append(RelativeTimeGrounding(term=term, resolved_label=label))
    return grounded


def build_time_context(
    context: RuntimeContext,
    last_turn_at: datetime | None,
    relative_terms: list[str] | None = None,
) -> TimeContext:
    now_local = resolve_now_local(context)
    last_local = last_turn_at.astimezone(_resolve_zoneinfo(context.config.time.timezone)) if last_turn_at is not None else None
    gap_kind, gap_minutes = resolve_gap_kind(now_local, last_local)
    grounded = ground_relative_terms(now_local, relative_terms or [])
    return TimeContext(
        timezone=context.config.time.timezone,
        now_local_iso=now_local.isoformat(),
        daypart=resolve_daypart(now_local),
        gap_kind=gap_kind,
        gap_minutes=gap_minutes,
        last_turn_local_iso=last_local.isoformat() if last_local is not None else None,
        continuity_class=continuity_from_gap(gap_kind),
        relative_grounding=grounded,
    )
