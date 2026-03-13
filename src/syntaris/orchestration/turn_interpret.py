from __future__ import annotations

import re

from syntaris.contracts.runtime import (
    ClaimCapture,
    ClaimKind,
    ClaimScope,
    MemoryQueryKind,
    PersonalEntryKind,
    PersonalEntrySignal,
    RecallRequest,
    RecallTargetKind,
    TurnInterpretation,
    TurnInterpretationKind,
)
from syntaris.orchestration.text_normalize import normalize_hungarian_for_match

_CURRENT_RECALL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recall_current_hol_tartottunk", re.compile(r"^hol\s+tartottunk\??$", re.IGNORECASE)),
    ("recall_current_mirol_beszeltunk", re.compile(r"^mir[őo]l\s+besz[ée]lt[üu]nk\s+az\s+el[őo]bb\??$", re.IGNORECASE)),
)

_PREVIOUS_RECALL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recall_previous_elozo_szal", re.compile(r"^az\s+el[őo]z[őo]\s+sz[áa]lon\s+mi\s+volt\??$", re.IGNORECASE)),
)

_COMPARE_PREVIOUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "compare_previous_hasonlitsd_ossze",
        re.compile(r"^hasonl[íi]tsd\s+össze\s+a\s+mostanit\s+az\s+el[őo]z[őo]\s+sz[áa]llal\??$", re.IGNORECASE),
    ),
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

_OWNER_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:^|\s)én\s+([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\s+vagyok(?:\s|$)", re.IGNORECASE),
    re.compile(r"(?:^|\s)([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\s+vagyok(?:\s|$)", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:javitas[:\s]+)?a\s+nevem\s+([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)(?:\s|$)", re.IGNORECASE),
)


def _extract_owner_name(text: str) -> str | None:
    for pattern in _OWNER_NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            raw = match.group(1).strip()
            return raw[:1].upper() + raw[1:].lower()
    return None


def _extract_declared_focus(normalized: str) -> str | None:
    if "a mai fokusz a " in normalized:
        return normalized.split("a mai fokusz a ", maxsplit=1)[1].strip(" .!?") or None
    return None


def _extract_relative_time_terms(normalized: str) -> list[str]:
    terms: list[str] = []
    for term in ("most", "ma", "tegnap", "holnap", "majd", "ma reggel", "ma delutan"):
        if term in normalized:
            mapped = "ma délután" if term == "ma delutan" else term
            if mapped not in terms:
                terms.append(mapped)
    return terms


def _extract_system_role(normalized: str) -> str | None:
    if "a szereped" in normalized and "szemelyes rendszerem" in normalized:
        return "személyes rendszered"
    if "a szereped" in normalized and "hogy" in normalized:
        return "személyes rendszered"
    if "ez az en szemelyes rendszerem" in normalized:
        return "személyes rendszered"
    return None


def _memory_query_kind(normalized: str) -> MemoryQueryKind | None:
    if normalized in {"ki vagyok", "ki vagyok?", "hogy hivnak", "hogy hivnak?"}:
        return MemoryQueryKind.WHO_AM_I
    if normalized in {"mit tudsz rolam biztosan", "mit tudsz rolam biztosan?"}:
        return MemoryQueryKind.WHAT_KNOWN_CERTAIN
    if normalized in {"mi a kapcsolatunk", "mi a kapcsolatunk?"}:
        return MemoryQueryKind.RELATIONSHIP
    if normalized in {"mi a szereped", "mi a szereped?"}:
        return MemoryQueryKind.SYSTEM_ROLE
    if normalized in {"mi a mostani fokusz", "mi a mostani fokusz?", "mirol akartam most beszelni", "mirol akartam most beszelni?"}:
        return MemoryQueryKind.CURRENT_FOCUS
    return None


def _claim_captures(owner_name: str | None, owner_framing: bool, system_role: str | None, declared_focus: str | None, declared_direction: str | None) -> list[ClaimCapture]:
    captures: list[ClaimCapture] = []
    if owner_name is not None:
        captures.append(ClaimCapture(kind=ClaimKind.OWNER_NAME, value=owner_name, scope=ClaimScope.STABLE))
    if owner_framing:
        captures.append(ClaimCapture(kind=ClaimKind.OWNER_RELATION, value="creator", scope=ClaimScope.STABLE))
    if system_role is not None:
        captures.append(ClaimCapture(kind=ClaimKind.SYSTEM_ROLE, value=system_role, scope=ClaimScope.STABLE))
    if declared_focus is not None:
        captures.append(ClaimCapture(kind=ClaimKind.CURRENT_FOCUS, value=declared_focus, scope=ClaimScope.THREAD))
    if declared_direction is not None:
        captures.append(ClaimCapture(kind=ClaimKind.CURRENT_DIRECTION, value=declared_direction, scope=ClaimScope.THREAD))
    return captures


def interpret_turn(message: str) -> TurnInterpretation:
    text = message.strip()
    raw_lower = text.lower()
    normalized = normalize_hungarian_for_match(text)

    owner_name = _extract_owner_name(text)
    relative_terms = _extract_relative_time_terms(normalized)
    owner_framing = any(
        phrase in normalized
        for phrase in (
            "en terveztem a rendszered",
            "en fejlesztelek",
            "en epitettem a rendszered",
            "a te rendszergedet en terveztem",
        )
    )
    return_entry = any(
        phrase in normalized
        for phrase in ("folytassuk innen", "vissza syntarisra", "vissza szintarisra")
    )
    greeting = normalized in {"szia", "szia syntaris", "szia szintaris", "jo reggelt", "jo estet", "jo ejt", "szep jo reggelt"} or normalized.startswith("szia syntaris ")

    personal_chat_intake = any(phrase in normalized for phrase in ("ma beszelgetni szeretnek", "csak beszelgessunk", "ma inkabb csak dumalnek"))
    concrete_help_intake = any(
        phrase in normalized
        for phrase in ("segits a timesheetben", "dolgozzunk a syntarison", "nezzuk meg ezt a problemat", "most valami konkret segitseg kell")
    )
    declared_focus = _extract_declared_focus(normalized)
    system_role = _extract_system_role(normalized)
    declared_direction: str | None = None
    if "most a munkarol akarok beszelni" in normalized:
        declared_direction = "munka"
    elif "ma az adminra fokuszaljunk" in normalized:
        declared_direction = "admin"

    memory_query = _memory_query_kind(normalized)

    resume_intake = any(
        phrase in normalized
        for phrase in ("folytassuk a syntarist", "menjunk tovabb innen", "vegyuk fel innen a fonalat")
    )

    captures = _claim_captures(owner_name, owner_framing, system_role, declared_focus, declared_direction)

    if owner_framing:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_owner_framing",
            personal_entry=PersonalEntrySignal(
                kind=PersonalEntryKind.OWNER_FRAMING,
                owner_name=owner_name,
                owner_relation="creator",
            ),
            claim_capture=captures,
            relative_time_terms=relative_terms,
        )

    if owner_name is not None and ("en " in normalized and " vagyok" in normalized):
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_self_intro",
            personal_entry=PersonalEntrySignal(kind=PersonalEntryKind.SELF_INTRO, owner_name=owner_name),
            claim_capture=captures,
            relative_time_terms=relative_terms,
        )

    if declared_focus is not None or declared_direction is not None:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_focus_setting",
            personal_entry=PersonalEntrySignal(
                kind=PersonalEntryKind.FOCUS_SETTING_INTAKE,
                declared_focus=declared_focus,
                declared_direction=declared_direction,
            ),
            claim_capture=captures,
            relative_time_terms=relative_terms,
        )

    if personal_chat_intake:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_personal_chat_intake",
            personal_entry=PersonalEntrySignal(kind=PersonalEntryKind.PERSONAL_CHAT_INTAKE),
            relative_time_terms=relative_terms,
        )

    if concrete_help_intake:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_concrete_help_intake",
            personal_entry=PersonalEntrySignal(
                kind=PersonalEntryKind.CONCRETE_HELP_INTAKE,
                declared_direction="concrete_help",
            ),
            relative_time_terms=relative_terms,
        )

    if resume_intake:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_resume_intake",
            personal_entry=PersonalEntrySignal(kind=PersonalEntryKind.RESUME_INTAKE),
            relative_time_terms=relative_terms,
        )

    if return_entry:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_return",
            personal_entry=PersonalEntrySignal(kind=PersonalEntryKind.RETURN_ENTRY),
            relative_time_terms=relative_terms,
        )

    if greeting:
        return TurnInterpretation(
            kind=TurnInterpretationKind.PERSONAL_ENTRY,
            pattern_name="personal_entry_greeting",
            personal_entry=PersonalEntrySignal(kind=PersonalEntryKind.GREETING, owner_name=owner_name),
            relative_time_terms=relative_terms,
        )

    if (
        "elozo szalon mi volt" in normalized
        or normalized in {"az elozo szalon mi volt", "elozo szalon mi volt"}
        or ("elå" in raw_lower and "szã" in raw_lower and "mi volt" in raw_lower)
    ):
        return TurnInterpretation(
            kind=TurnInterpretationKind.RECALL_PREVIOUS,
            pattern_name="recall_previous_normalized",
            recall_request=RecallRequest(target=RecallTargetKind.PREVIOUS),
            relative_time_terms=relative_terms,
        )

    if (
        "hasonlitsd ossze a mostanit az elozo szallal" in normalized
        or ("hasonlã" in raw_lower and "ssze" in raw_lower and "elå" in raw_lower and "szã" in raw_lower)
    ):
        return TurnInterpretation(
            kind=TurnInterpretationKind.COMPARE_PREVIOUS,
            pattern_name="compare_previous_normalized",
            relative_time_terms=relative_terms,
        )

    for pattern_name, pattern, kind in _NAMED_PATTERNS:
        match = pattern.match(text)
        if match:
            return TurnInterpretation(
                kind=kind,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.NAMED, thread_key=match.group(1).strip().lower()),
                relative_time_terms=relative_terms,
            )

    for pattern_name, pattern in _PREVIOUS_RECALL_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.RECALL_PREVIOUS,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.PREVIOUS),
                relative_time_terms=relative_terms,
            )

    for pattern_name, pattern in _COMPARE_PREVIOUS_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.COMPARE_PREVIOUS,
                pattern_name=pattern_name,
                relative_time_terms=relative_terms,
            )

    for pattern_name, pattern in _PREVIOUS_RESUME_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.RESUME_PREVIOUS,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.PREVIOUS),
                relative_time_terms=relative_terms,
            )

    for pattern_name, pattern in _CURRENT_RECALL_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.RECALL_CURRENT,
                pattern_name=pattern_name,
                recall_request=RecallRequest(target=RecallTargetKind.CURRENT),
                relative_time_terms=relative_terms,
            )

    for pattern_name, pattern in _AMBIGUOUS_RESUME_PATTERNS:
        if pattern.match(text):
            return TurnInterpretation(
                kind=TurnInterpretationKind.CLARIFICATION_NEEDED,
                pattern_name=pattern_name,
                clarification_reason="resume_target_ambiguous",
                relative_time_terms=relative_terms,
            )

    if captures:
        return TurnInterpretation(
            kind=TurnInterpretationKind.ORDINARY,
            claim_capture=captures,
            relative_time_terms=relative_terms,
        )

    if memory_query is not None:
        return TurnInterpretation(
            kind=TurnInterpretationKind.ORDINARY,
            memory_query=memory_query,
            relative_time_terms=relative_terms,
        )

    return TurnInterpretation(kind=TurnInterpretationKind.ORDINARY, relative_time_terms=relative_terms)
