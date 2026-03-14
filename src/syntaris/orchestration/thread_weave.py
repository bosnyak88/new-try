from __future__ import annotations

import re
from dataclasses import dataclass

from syntaris.contracts.runtime import (
    ApplicabilityStatus,
    ConclusionStatus,
    ThreadContextTurn,
    ThreadRelationKind,
    ThreadWeaveState,
    WorkframeState,
)
from syntaris.orchestration.text_normalize import normalize_hungarian_for_match

_RELATION_MAIN_PATTERNS = (
    "mi a foszal most",
    "melyik volt a foszal",
)
_RELATION_SIDE_PATTERNS = (
    "mi volt csak mellekszal",
    "mellekszal",
    "kitero",
)
_CONCLUSION_QUERY_PATTERNS = (
    "mi ebbol a tanulsag",
    "mi a konkluzio",
    "mit lehet ebbol levonni",
)
_APPLICABILITY_QUERY_PATTERNS = (
    "ebbol mi alkalmazhato most",
    "ez ugyanaz a mintazat",
    "hasznalhato ez most is",
    "mi ervenyes meg ebbol",
)

_DETOUR_DECLARATION = re.compile(r"(?:kozben\s+)?kiter(?:tunk|tem|t)\s+(?:a\s+)?(.+)$")
_RETURN_MAIN_DECLARATION = re.compile(r"(?:de\s+)?a\s+foszal\s+tovabbra\s+is\s+(?:a\s+)?(.+)$")
_MAIN_DECLARATION = re.compile(r"(?:a\s+foszal\s+(?:most\s+)?)?(?:a\s+)?rebuild-\d+[^.?!]*")
_EXPLICIT_CONCLUSION = re.compile(r"(?:tanulsag|konkluzio|levonhato)\s*(?::|hogy)?\s+(.+)$")


@dataclass(frozen=True)
class _WeaveScan:
    main_topic: str | None = None
    detour_topic: str | None = None
    had_detour: bool = False
    had_return_to_main: bool = False


def detect_thread_weave_query_family(message: str) -> str | None:
    n = normalize_hungarian_for_match(message).strip()
    if any(p in n for p in _RELATION_MAIN_PATTERNS + _RELATION_SIDE_PATTERNS):
        return "thread_relation_query"
    if any(p in n for p in _CONCLUSION_QUERY_PATTERNS):
        return "conclusion_query"
    if any(p in n for p in _APPLICABILITY_QUERY_PATTERNS):
        return "applicability_query"
    return None


def detect_thread_weave_update_kind(message: str) -> str | None:
    n = normalize_hungarian_for_match(message).strip()
    if _DETOUR_DECLARATION.search(n):
        return "detour_declared"
    if _RETURN_MAIN_DECLARATION.search(n):
        return "return_to_main_declared"
    return None


def _clean_topic(text: str) -> str:
    return text.strip(" .,!?:;")


def _scan_weave(turns: list[ThreadContextTurn], current_message: str, workframe_state: WorkframeState | None) -> _WeaveScan:
    main_topic = _clean_topic(workframe_state.objective_text) if workframe_state is not None and workframe_state.objective_text else None
    detour_topic: str | None = None
    had_detour = False
    had_return_to_main = False

    for turn in [*turns, ThreadContextTurn(turn_id=-1, turn_index=-1, user_message=current_message, assistant_reply="", backend="deterministic", degraded=False)]:
        n = normalize_hungarian_for_match(turn.user_message)
        if detour := _DETOUR_DECLARATION.search(n):
            topic = _clean_topic(detour.group(1))
            if topic:
                detour_topic = topic
            had_detour = True
        if ret := _RETURN_MAIN_DECLARATION.search(n):
            topic = _clean_topic(ret.group(1))
            if topic:
                main_topic = topic
            had_return_to_main = True
        if main_topic is None:
            if _MAIN_DECLARATION.search(n):
                main_topic = _clean_topic(_MAIN_DECLARATION.search(n).group(0))
    return _WeaveScan(main_topic=main_topic, detour_topic=detour_topic, had_detour=had_detour, had_return_to_main=had_return_to_main)


def derive_thread_weave_state(
    turns: list[ThreadContextTurn],
    current_message: str,
    *,
    active_thread_key: str,
    previous_thread_key: str | None,
    workframe_state: WorkframeState | None,
) -> ThreadWeaveState:
    scan = _scan_weave(turns, current_message, workframe_state)
    message_n = normalize_hungarian_for_match(current_message)

    relation = ThreadRelationKind.RELATION_UNKNOWN
    if scan.had_detour and scan.had_return_to_main:
        relation = ThreadRelationKind.RETURN_TO_MAIN
    elif scan.had_detour:
        relation = ThreadRelationKind.DETOUR
    elif scan.main_topic is not None:
        relation = ThreadRelationKind.MAIN_THREAD

    if "mellekszal" in message_n or "kitero" in message_n:
        relation = ThreadRelationKind.SIDE_THREAD if scan.detour_topic is not None else ThreadRelationKind.RELATION_UNKNOWN
    elif "foszal" in message_n and scan.main_topic is not None:
        relation = ThreadRelationKind.RETURN_TO_MAIN if scan.had_return_to_main else ThreadRelationKind.MAIN_THREAD

    conclusion_status = ConclusionStatus.NONE
    conclusion_text: str | None = None
    for turn in turns:
        n = normalize_hungarian_for_match(turn.user_message)
        explicit = _EXPLICIT_CONCLUSION.search(n)
        if explicit:
            conclusion_status = ConclusionStatus.EXPLICIT
            conclusion_text = _clean_topic(explicit.group(1))

    if conclusion_status == ConclusionStatus.NONE:
        if scan.had_detour and scan.main_topic:
            conclusion_status = ConclusionStatus.DERIVED
            if scan.had_return_to_main:
                conclusion_text = f"Volt kitérő ({scan.detour_topic or 'mellékszál'}), de a főszál maradt: {scan.main_topic}."
            else:
                conclusion_text = f"Megjelent egy kitérő ({scan.detour_topic or 'mellékszál'}), és érdemes visszazárni a főszálra: {scan.main_topic}."
        elif workframe_state is not None and workframe_state.next_step_lines:
            conclusion_status = ConclusionStatus.DERIVED
            conclusion_text = workframe_state.next_step_lines[0]

    applicability_status = ApplicabilityStatus.UNCERTAIN
    applicability_reason = "Kevés stabil jel van arról, hogy a korábbi konklúzió most is érvényes."
    if scan.had_detour and scan.had_return_to_main and scan.main_topic:
        applicability_status = ApplicabilityStatus.APPLICABLE_NOW
        applicability_reason = "A minta most is használható: kitérőt jelölünk, majd visszaállunk a főszálra."
    elif scan.had_detour and scan.main_topic:
        applicability_status = ApplicabilityStatus.PARTIALLY_APPLICABLE
        applicability_reason = "A kitérő-felismerés hasznos, de még nincs explicit visszatérés a főszálra."

    if workframe_state is not None:
        if workframe_state.decision_state.value == "decision_blocked_by_missing_info":
            applicability_status = ApplicabilityStatus.NOT_APPLICABLE_NOW
            applicability_reason = "Hiányzó információ miatt a minta csak korlátozottan alkalmazható most."
        elif workframe_state.decision_state.value == "decision_made":
            applicability_status = ApplicabilityStatus.SUPERSEDED_BY_NEW_CONTEXT
            applicability_reason = "Új döntési helyzet miatt a korábbi minta részben meghaladott."

    if conclusion_status == ConclusionStatus.NONE:
        applicability_status = ApplicabilityStatus.UNCERTAIN
        applicability_reason = "Nincs még elég megalapozott konklúzió, így az alkalmazhatóság is bizonytalan."

    related = previous_thread_key
    if scan.detour_topic:
        related = scan.detour_topic

    return ThreadWeaveState(
        relation=relation,
        main_thread_key=scan.main_topic or active_thread_key,
        related_thread_key=related,
        detour_thread_key=scan.detour_topic,
        conclusion_status=conclusion_status,
        conclusion_text=conclusion_text,
        applicability_status=applicability_status,
        applicability_reason=applicability_reason,
    )
