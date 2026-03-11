from __future__ import annotations

import re

from syntaris.contracts.runtime import (
    ActiveConversationState,
    PendingRouteProposal,
    RouteDecision,
    RouteDecisionAction,
    RouteMatch,
    ThreadSummaryView,
)

_RETURN_NAMED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("return_vissza", re.compile(r"^vissza a\s+([a-z0-9_-]+)\s+szálra$", re.IGNORECASE)),
    ("return_menjunk_vissza", re.compile(r"^menjünk vissza a\s+([a-z0-9_-]+)\s+szálra$", re.IGNORECASE)),
    ("switch_valtsunk", re.compile(r"^váltsunk a\s+([a-z0-9_-]+)\s+szálra$", re.IGNORECASE)),
)

_SWITCH_PREVIOUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("switch_previous_vissza", re.compile(r"^vissza az\s+előző\s+szálra$", re.IGNORECASE)),
    ("switch_previous_terjunk", re.compile(r"^térjünk vissza az\s+előző\s+témára$", re.IGNORECASE)),
)

_CREATE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("create_uj_szal", re.compile(r"^új szál:\s*([a-z0-9_-]+)$", re.IGNORECASE)),
    ("create_legyen_uj", re.compile(r"^legyen új szál:\s*([a-z0-9_-]+)$", re.IGNORECASE)),
    ("create_nyiss_uj", re.compile(r"^nyiss új szálat:\s*([a-z0-9_-]+)$", re.IGNORECASE)),
    ("topic_shift_mas_tema", re.compile(r"^más téma:\s*([a-z0-9_-]+)$", re.IGNORECASE)),
    ("topic_shift_uj_tema", re.compile(r"^új téma:\s*([a-z0-9_-]+)$", re.IGNORECASE)),
    ("topic_shift_egy_masik", re.compile(r"^egy másik dolog:\s*([a-z0-9_-]+)$", re.IGNORECASE)),
)

_SUGGESTIVE_NAMED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("suggestive_named_folytassuk", re.compile(r"^folytassuk a\s+([a-z0-9_-]+)(?:-t|öt|ot)?$", re.IGNORECASE)),
    ("suggestive_named_hol_tartottunk", re.compile(r"^hol tartottunk a\s+([a-z0-9_-]+)(?:-nél|nal|n)?$", re.IGNORECASE)),
    ("suggestive_named_mi_volt", re.compile(r"^mi volt a\s+([a-z0-9_-]+)(?:-nél|nal|n)?$", re.IGNORECASE)),
    ("suggestive_named_terjunk", re.compile(r"^térjünk vissza a\s+([a-z0-9_-]+)(?:-re|ra)?$", re.IGNORECASE)),
)

_SUGGESTIVE_PREVIOUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("suggestive_previous_folytassuk", re.compile(r"^folytassuk az\s+előzőt$", re.IGNORECASE)),
    ("suggestive_previous_mi_volt", re.compile(r"^mi volt az\s+előző\s+témában$", re.IGNORECASE)),
    ("suggestive_previous_terjunk", re.compile(r"^térjünk vissza arra$", re.IGNORECASE)),
)


def _proposal(
    *,
    message: str,
    active_state: ActiveConversationState,
    proposed_thread_key: str,
    reason: str,
    action: RouteDecisionAction,
    pattern_name: str | None,
    source: str,
) -> RouteDecision:
    return RouteDecision(
        action=action,
        reason=reason,
        thread_key=active_state.thread_key,
        match=RouteMatch(pattern_name=pattern_name, thread_key=proposed_thread_key) if pattern_name else None,
        created_thread=False,
        pending_proposal=PendingRouteProposal(
            held_user_message=message,
            proposed_thread_key=proposed_thread_key,
            current_thread_key=active_state.thread_key,
            reason=reason,
            match_pattern=pattern_name,
            source=source,
            proposed_at="",
        ),
    )


def resolve_route_decision(
    message: str,
    active_state: ActiveConversationState,
    known_threads: list[ThreadSummaryView],
    source: str = "talk_once",
) -> RouteDecision:
    text = message.strip()
    known_keys = {thread.thread_key for thread in known_threads}

    for pattern_name, pattern in _RETURN_NAMED_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        thread_key = match.group(1).strip().lower()
        return RouteDecision(
            action=RouteDecisionAction.SWITCH_EXISTING if thread_key in known_keys else RouteDecisionAction.NO_ROUTE_CHANGE,
            reason="matched_return_phrase" if thread_key in known_keys else "matched_return_phrase_unknown_thread",
            thread_key=thread_key if thread_key in known_keys else active_state.thread_key,
            match=RouteMatch(pattern_name=pattern_name, thread_key=thread_key),
            created_thread=False,
        )

    for pattern_name, pattern in _CREATE_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        thread_key = match.group(1).strip().lower()
        return RouteDecision(
            action=RouteDecisionAction.CREATE_AND_SWITCH if thread_key not in known_keys else RouteDecisionAction.SWITCH_EXISTING,
            reason="matched_create_phrase",
            thread_key=thread_key,
            match=RouteMatch(pattern_name=pattern_name, thread_key=thread_key),
            created_thread=thread_key not in known_keys,
        )

    for pattern_name, pattern in _SWITCH_PREVIOUS_PATTERNS:
        if not pattern.match(text):
            continue
        if active_state.previous_thread_key is None:
            return RouteDecision(
                action=RouteDecisionAction.NO_ROUTE_CHANGE,
                reason="matched_previous_phrase_without_previous",
                thread_key=active_state.thread_key,
                match=RouteMatch(pattern_name=pattern_name, thread_key=active_state.thread_key),
                created_thread=False,
            )
        return RouteDecision(
            action=RouteDecisionAction.SWITCH_PREVIOUS,
            reason="matched_previous_phrase",
            thread_key=active_state.previous_thread_key,
            match=RouteMatch(pattern_name=pattern_name, thread_key=active_state.previous_thread_key),
            created_thread=False,
        )

    for pattern_name, pattern in _SUGGESTIVE_NAMED_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        thread_key = match.group(1).strip().lower()
        if thread_key in known_keys and thread_key != active_state.thread_key:
            return _proposal(
                message=message,
                active_state=active_state,
                proposed_thread_key=thread_key,
                reason="matched_suggestive_named_thread_phrase",
                action=RouteDecisionAction.PROPOSE_SWITCH_EXISTING,
                pattern_name=pattern_name,
                source=source,
            )

    for pattern_name, pattern in _SUGGESTIVE_PREVIOUS_PATTERNS:
        if not pattern.match(text):
            continue
        if active_state.previous_thread_key is None:
            return RouteDecision(
                action=RouteDecisionAction.NO_ROUTE_CHANGE,
                reason="matched_suggestive_previous_without_previous",
                thread_key=active_state.thread_key,
                match=RouteMatch(pattern_name=pattern_name, thread_key=active_state.thread_key),
                created_thread=False,
            )
        return _proposal(
            message=message,
            active_state=active_state,
            proposed_thread_key=active_state.previous_thread_key,
            reason="matched_suggestive_previous_thread_phrase",
            action=RouteDecisionAction.PROPOSE_SWITCH_PREVIOUS,
            pattern_name=pattern_name,
            source=source,
        )

    return RouteDecision(
        action=RouteDecisionAction.CONTINUE_ACTIVE,
        reason="no_routing_phrase_match",
        thread_key=active_state.thread_key,
    )
