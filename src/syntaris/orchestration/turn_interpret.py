from __future__ import annotations

import re

from syntaris.contracts.runtime import RecallRequest, RecallTargetKind, TurnInterpretation, TurnInterpretationKind

_CURRENT_RECALL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recall_current_hol_tartottunk", re.compile(r"^hol\s+tartottunk\??$", re.IGNORECASE)),
    ("recall_current_mirol_beszeltunk", re.compile(r"^mir[őo]l\s+besz[ée]lt[üu]nk\s+az\s+el[őo]bb\??$", re.IGNORECASE)),
)

_PREVIOUS_RECALL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recall_previous_elozo_szal", re.compile(r"^az\s+el[őo]z[őo]\s+sz[áa]lon\s+mi\s+volt\??$", re.IGNORECASE)),
)

_NAMED_PATTERNS: tuple[tuple[str, re.Pattern[str], TurnInterpretationKind], ...] = (
    (
        "resume_named_hozd_vissza",
        re.compile(r"^a\s+([a-z0-9_-]+)\s+sz[áa]lat\s+hozd\s+vissza$", re.IGNORECASE),
        TurnInterpretationKind.RESUME_NAMED,
    ),
    (
        "recall_named_mi_volt",
        re.compile(r"^a\s+([a-z0-9_-]+)\s+sz[áa]lon\s+mi\s+volt\??$", re.IGNORECASE),
        TurnInterpretationKind.RECALL_NAMED,
    ),
)

_PREVIOUS_RESUME_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("resume_previous_hozd_vissza", re.compile(r"^hozd\s+vissza\s+az\s+el[őo]z[őo]\s+sz[áa]lat$", re.IGNORECASE)),
)

_AMBIGUOUS_RESUME_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("resume_ambiguous_folytassuk_onnan", re.compile(r"^folytassuk\s+onnan\??$", re.IGNORECASE)),
)


def interpret_turn(message: str) -> TurnInterpretation:
    text = message.strip()

    for pattern_name, pattern, kind in _NAMED_PATTERNS:
        match = pattern.match(text)
        if match:
            return TurnInterpretation(
                kind=kind,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.NAMED, thread_key=match.group(1).strip().lower()),
            )

    for pattern_name, pattern in _PREVIOUS_RECALL_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.RECALL_PREVIOUS,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.PREVIOUS),
            )

    for pattern_name, pattern in _PREVIOUS_RESUME_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.RESUME_PREVIOUS,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.PREVIOUS),
            )

    for pattern_name, pattern in _CURRENT_RECALL_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.RECALL_CURRENT,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.CURRENT),
            )

    for pattern_name, pattern in _AMBIGUOUS_RESUME_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.CLARIFICATION_NEEDED,
                pattern_name=pattern_name,
                clarification_reason="resume_target_ambiguous",
            )

    return TurnInterpretation(kind=TurnInterpretationKind.ORDINARY)
