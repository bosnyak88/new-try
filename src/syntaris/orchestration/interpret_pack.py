from __future__ import annotations

import re
from dataclasses import dataclass

from syntaris.contracts.runtime import InterpretCandidate as RuntimeInterpretCandidate
from syntaris.contracts.runtime import InterpretPack as RuntimeInterpretPack
from syntaris.contracts.runtime import InterpretUnit as RuntimeInterpretUnit
from syntaris.orchestration.text_normalize import normalize_hungarian_for_match


@dataclass(frozen=True)
class UtteranceUnit:
    text: str
    role: str


@dataclass(frozen=True)
class CandidateIntent:
    name: str
    score: int
    reason: str


@dataclass(frozen=True)
class WorkframeCandidate:
    workframe: str
    score: int
    reason: str


@dataclass(frozen=True)
class ThreadCandidate:
    relation: str
    score: int
    reason: str


@dataclass(frozen=True)
class InterpretPack:
    utterance_units: list[UtteranceUnit]
    candidate_intents: list[CandidateIntent]
    workframe_candidates: list[WorkframeCandidate]
    thread_candidates: list[ThreadCandidate]
    style_constraints_effective: list[str]
    evidence_need: str
    memory_need: str
    risk_flags: list[str]
    unknown_points: list[str]
    selected_intent: str
    selected_workframe: str
    selected_thread: str
    selected_reason: str
    rejected_reasons: list[str]


def to_runtime_interpret_pack(pack: InterpretPack) -> RuntimeInterpretPack:
    """Explicit canonical mapping from orchestration interpret-pack to runtime contract."""
    return RuntimeInterpretPack(
        utterance_units=[RuntimeInterpretUnit(text=u.text, role=u.role) for u in pack.utterance_units],
        candidate_intents=[RuntimeInterpretCandidate(name=i.name, score=i.score, reason=i.reason) for i in pack.candidate_intents],
        workframe_candidates=[RuntimeInterpretCandidate(name=i.workframe, score=i.score, reason=i.reason) for i in pack.workframe_candidates],
        thread_candidates=[RuntimeInterpretCandidate(name=i.relation, score=i.score, reason=i.reason) for i in pack.thread_candidates],
        style_constraints_effective=list(pack.style_constraints_effective),
        evidence_need=pack.evidence_need,
        memory_need=pack.memory_need,
        risk_flags=list(pack.risk_flags),
        unknown_points=list(pack.unknown_points),
        selected_intent=pack.selected_intent,
        selected_workframe=pack.selected_workframe,
        selected_thread=pack.selected_thread,
        selected_reason=pack.selected_reason,
        rejected_reasons=list(pack.rejected_reasons),
    )


def _select_intent(candidates: list[CandidateIntent], unknown_points: list[str]) -> str:
    if not candidates:
        return "unknown"
    top = candidates[0]
    if top.score <= 0:
        return "unknown"
    if top.name == "direct_answer" and top.score <= 1 and unknown_points:
        return "clarification_or_unknown"
    return top.name


def _select_workframe(candidates: list[WorkframeCandidate], previous_workframe: str) -> str:
    if not candidates:
        return previous_workframe
    top = candidates[0]
    if top.score <= 0:
        return previous_workframe
    return top.workframe


def _select_thread(candidates: list[ThreadCandidate]) -> str:
    if not candidates:
        return "uncertain"
    top = candidates[0]
    if top.score <= 0:
        return "uncertain"
    return top.relation


def _segment_units(message: str) -> list[UtteranceUnit]:
    raw = [part.strip(" ,") for part in re.split(r"[,.!?]|\s+de\s+|\s+amugy\s+|\s+amúgy\s+|\s+es\s+|\s+és\s+", message) if part.strip(" ,")]
    units: list[UtteranceUnit] = []
    for part in raw:
        n = normalize_hungarian_for_match(part)
        role = "background"
        if any(k in n for k in ("roviden", "ne listazz", "ne listaz", "csak reagalj normalisan", "ne bontsd biztosra", "tomoren")):
            role = "style_request"
        elif any(k in n for k in ("hol tartunk", "hol tartottunk", "folytassuk innen", "mire jutottunk", "elozo")):
            role = "thread_hint"
        elif any(k in n for k in ("chat", "beszelg", "dumal", "ne dolgozz")):
            role = "workframe_hint"
        elif any(k in n for k in ("nem tudom", "talan", "nem biztos")):
            role = "uncertainty"
        elif "?" in part or any(n.startswith(prefix) for prefix in ("mi ", "mit ", "hogyan", "hol ", "mikor", "ki ")):
            role = "direct_answer"
        units.append(UtteranceUnit(text=part, role=role))
    return units or [UtteranceUnit(text=message.strip(), role="background")]


def _style_constraints(message: str) -> list[str]:
    n = normalize_hungarian_for_match(message)
    found: list[str] = []
    if any(k in n for k in ("ne listazz", "ne listaz", "csak reagalj normalisan")):
        found.append("no_list")
    if "rovid" in n or "tomoren" in n:
        found.append("brief")
    if any(k in n for k in ("ne bontsd biztosra", "ne bontsd feltetelezesre")):
        found.append("no_certainty_split")
    if any(k in n for k in ("most ne dolgozzunk", "csak beszelg", "csak dumal", "csak reagalj normalisan")):
        found.append("casual_only")
    return found


def _candidate_intents(units: list[UtteranceUnit], normalized: str) -> list[CandidateIntent]:
    intents: list[CandidateIntent] = []
    direct_score = sum(2 for u in units if u.role == "direct_answer")
    if "mi a blocker" in normalized:
        direct_score += 2
    intents.append(CandidateIntent(name="direct_answer", score=direct_score, reason="direct question units"))

    chat_score = sum(3 for u in units if u.role == "workframe_hint")
    intents.append(CandidateIntent(name="chat_lock", score=chat_score, reason="explicit casual cues"))

    thread_score = sum(2 for u in units if u.role == "thread_hint")
    intents.append(CandidateIntent(name="thread_query", score=thread_score, reason="thread recall/resume cues"))

    if any(u.role == "uncertainty" for u in units):
        intents.append(CandidateIntent(name="clarification_or_unknown", score=2, reason="explicit uncertainty phrase"))

    return sorted(intents, key=lambda i: i.score, reverse=True)


def _workframe_candidates(normalized: str, previous: str) -> list[WorkframeCandidate]:
    out: list[WorkframeCandidate] = []
    chat_score = 0
    if any(k in normalized for k in ("most ne dolgozzunk", "csak beszelg", "csak dumal", "csak reagalj normalisan")):
        chat_score += 5
    if any(k in normalized for k in ("roviden", "ne listazz")):
        chat_score += 1
    out.append(WorkframeCandidate(workframe="chat", score=chat_score, reason="explicit chat lock or style cues"))

    recall_score = 0
    if any(k in normalized for k in ("hol tartottunk", "mire jutottunk", "folytassuk innen", "elozo szal")):
        recall_score += 4
    out.append(WorkframeCandidate(workframe="recall", score=recall_score, reason="recall/resume phrases"))

    work_score = 0
    if any(k in normalized for k in ("ticket", "feladat", "dolgozzunk", "blocker", "kovetkezo lepes")):
        work_score += 3
    out.append(WorkframeCandidate(workframe="work", score=work_score, reason="work execution cues"))

    if previous == "chat" and chat_score > 0 and work_score <= 1:
        out.append(WorkframeCandidate(workframe="chat", score=chat_score + 2, reason="chat lock stronger than weak work pullback"))

    return sorted(out, key=lambda c: c.score, reverse=True)


def _thread_candidates(normalized: str, has_previous_thread: bool) -> list[ThreadCandidate]:
    out = [ThreadCandidate(relation="current", score=1, reason="default active thread")]
    if any(k in normalized for k in ("hol tartottunk", "folytassuk innen", "mire jutottunk")):
        out.append(ThreadCandidate(relation="current", score=4, reason="resume from current thread cue"))
    if any(k in normalized for k in ("elozo szal", "az elozo")) and has_previous_thread:
        out.append(ThreadCandidate(relation="previous", score=4, reason="explicit previous thread cue"))
    if any(k in normalized for k in ("uj szal", "uj tema")):
        out.append(ThreadCandidate(relation="new", score=4, reason="explicit new thread cue"))
    if any(k in normalized for k in ("emlekszel", "folytassuk")) and not has_previous_thread:
        out.append(ThreadCandidate(relation="uncertain", score=3, reason="recall language without target thread evidence"))
    if any(k in normalized for k in ("historikus", "regi szal", "korabbi")):
        out.append(ThreadCandidate(relation="historical_requested", score=3, reason="historical recall asked"))
    return sorted(out, key=lambda c: c.score, reverse=True)


def build_interpret_pack(message: str, *, previous_workframe: str = "chat", has_previous_thread: bool = False) -> InterpretPack:
    normalized = normalize_hungarian_for_match(message).strip()
    units = _segment_units(message)
    style = _style_constraints(message)
    intents = _candidate_intents(units, normalized)
    workframes = _workframe_candidates(normalized, previous_workframe)
    threads = _thread_candidates(normalized, has_previous_thread)

    evidence_need = "needed" if any(k in normalized for k in ("forras", "log", "traceback", "bizonyitek")) else "not_needed"
    memory_need = "thread_recall" if any(k in normalized for k in ("hol tartottunk", "mire jutottunk", "folytassuk innen")) else "none"

    risk_flags: list[str] = []
    has_direct = any(i.name == "direct_answer" and i.score > 0 for i in intents)
    has_style_soft_lock = any(k in style for k in ("casual_only", "no_list", "brief"))
    if has_direct and has_style_soft_lock:
        risk_flags.append("mixed_turn_direct_plus_chat_lock")
    if sum(1 for token in ("most", "biztos", "fontos", "emlekszel") if token in normalized) >= 2:
        risk_flags.append("hijack_trigger_cluster")

    unknown_points: list[str] = []
    if any(c.relation == "uncertain" for c in threads):
        unknown_points.append("thread_target_ambiguous")
    if any(u.role == "uncertainty" for u in units):
        unknown_points.append("user_goal_unspecified")

    selected_intent = _select_intent(intents, unknown_points)
    selected_workframe = _select_workframe(workframes, previous_workframe)
    selected_thread = _select_thread(threads)
    selected_reason = f"intent={selected_intent};workframe={selected_workframe};thread={selected_thread}"
    rejected = [f"{i.name}:{i.reason}" for i in intents[1:3]]

    return InterpretPack(
        utterance_units=units,
        candidate_intents=intents,
        workframe_candidates=workframes,
        thread_candidates=threads,
        style_constraints_effective=style,
        evidence_need=evidence_need,
        memory_need=memory_need,
        risk_flags=risk_flags,
        unknown_points=unknown_points,
        selected_intent=selected_intent,
        selected_workframe=selected_workframe,
        selected_thread=selected_thread,
        selected_reason=selected_reason,
        rejected_reasons=rejected,
    )
