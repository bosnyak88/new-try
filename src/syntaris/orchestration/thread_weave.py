from __future__ import annotations

import re

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
_EXPLICIT_CONCLUSION = re.compile(r"(?:tanulsag|konkluzio|levonhato)\s*(?::|hogy)?\s+(.+)$")


def detect_thread_weave_query_family(message: str) -> str | None:
    n = normalize_hungarian_for_match(message).strip()
    if any(p in n for p in _RELATION_MAIN_PATTERNS + _RELATION_SIDE_PATTERNS):
        return "thread_relation_query"
    if any(p in n for p in _CONCLUSION_QUERY_PATTERNS):
        return "conclusion_query"
    if any(p in n for p in _APPLICABILITY_QUERY_PATTERNS):
        return "applicability_query"
    return None


def derive_thread_weave_state(
    turns: list[ThreadContextTurn],
    current_message: str,
    *,
    active_thread_key: str,
    previous_thread_key: str | None,
    workframe_state: WorkframeState | None,
) -> ThreadWeaveState:
    relation = ThreadRelationKind.RELATION_UNKNOWN
    main_thread_key = active_thread_key
    related_thread_key = previous_thread_key
    detour_thread_key: str | None = None

    conclusion_status = ConclusionStatus.NONE
    conclusion_text: str | None = None
    applicability_status = ApplicabilityStatus.UNCERTAIN
    applicability_reason: str | None = "Kevés stabil jel van arról, hogy a régi konklúzió most is érvényes."

    for turn in turns:
        n = normalize_hungarian_for_match(turn.user_message)
        if "foszal" in n:
            relation = ThreadRelationKind.MAIN_THREAD
        if "mellekszal" in n:
            relation = ThreadRelationKind.SIDE_THREAD
            detour_thread_key = active_thread_key
        if "kiter" in n:
            relation = ThreadRelationKind.DETOUR
            detour_thread_key = active_thread_key
        if "tovabbra is a" in n and "foszal" in n:
            relation = ThreadRelationKind.RETURN_TO_MAIN

        explicit = _EXPLICIT_CONCLUSION.search(n)
        if explicit:
            conclusion_status = ConclusionStatus.EXPLICIT
            conclusion_text = explicit.group(1).strip(" .")
        elif any(t in n for t in ("ez a tanulsag", "ebbol az jon ki", "levonhato")):
            conclusion_status = ConclusionStatus.DERIVED
            conclusion_text = "A fő irányt tartani kell, a mellékszál csak kiegészítő."
        elif any(t in n for t in ("talan", "lehet hogy")) and "tanulsag" in n:
            conclusion_status = ConclusionStatus.TENTATIVE
            conclusion_text = "A konklúzió még bizonytalan."

    message_n = normalize_hungarian_for_match(current_message)
    if "visszater" in message_n or "foszal tovabbra" in message_n:
        relation = ThreadRelationKind.RETURN_TO_MAIN
    elif "mellekszal" in message_n:
        relation = ThreadRelationKind.SIDE_THREAD
    elif "kiter" in message_n:
        relation = ThreadRelationKind.DETOUR
    elif "ugyanahhoz a szalhoz" in message_n:
        relation = ThreadRelationKind.MAIN_THREAD if previous_thread_key is None else ThreadRelationKind.SIDE_THREAD

    if previous_thread_key is None and relation in {ThreadRelationKind.SIDE_THREAD, ThreadRelationKind.DETOUR}:
        relation = ThreadRelationKind.UNRELATED_THREAD

    if workframe_state is not None:
        if workframe_state.objective_status.value == "active" and workframe_state.blocker_status.value in {"explicit", "implied"}:
            applicability_status = ApplicabilityStatus.PARTIALLY_APPLICABLE
            applicability_reason = "A korábbi konklúzió részben vihető tovább, de a mostani blokker miatt csak feltételesen."
        if workframe_state.decision_state.value == "decision_blocked_by_missing_info":
            applicability_status = ApplicabilityStatus.NOT_APPLICABLE_NOW
            applicability_reason = "Hiányzó információ miatt a korábbi konklúzió most nem alkalmazható vakon."
        if workframe_state.decision_state.value == "decision_made":
            applicability_status = ApplicabilityStatus.SUPERSEDED_BY_NEW_CONTEXT
            applicability_reason = "Új döntés született, a régi konklúzió részben vagy teljesen meghaladott."

    if conclusion_status == ConclusionStatus.NONE:
        if workframe_state is not None and workframe_state.next_step_lines:
            conclusion_status = ConclusionStatus.DERIVED
            conclusion_text = workframe_state.next_step_lines[0]
        else:
            applicability_status = ApplicabilityStatus.UNCERTAIN
            applicability_reason = "Nincs még megalapozott konklúzió, ezért alkalmazhatóság sem állítható biztosan."

    return ThreadWeaveState(
        relation=relation,
        main_thread_key=main_thread_key,
        related_thread_key=related_thread_key,
        detour_thread_key=detour_thread_key,
        conclusion_status=conclusion_status,
        conclusion_text=conclusion_text,
        applicability_status=applicability_status,
        applicability_reason=applicability_reason,
    )
