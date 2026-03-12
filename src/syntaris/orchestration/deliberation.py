from __future__ import annotations

from syntaris.contracts.runtime import (
    ComparisonReason,
    DeliberationInput,
    FollowupResolution,
    RecallResolution,
    TurnInterpretation,
)

_CORRECTION_CUES = (
    "nem erre gondoltam",
    "nem ezt kérdeztem",
    "nem ezt",
)

_REDIRECT_CUES = (
    "várj",
    "térjünk vissza",
    "a másik",
)


def _contains_any(message: str, phrases: tuple[str, ...]) -> bool:
    normalized = message.strip().lower()
    return any(phrase in normalized for phrase in phrases)


def assemble_deliberation_input(
    message: str,
    interpretation: TurnInterpretation,
    recall: RecallResolution,
    followup: FollowupResolution,
    has_focus: bool,
    has_previous_thread: bool,
) -> DeliberationInput:
    normalized = message.strip().lower()
    references_previous = "előző szál" in normalized or "előzőre" in normalized
    references_other = "másik" in normalized
    structured_request = (
        (("lényeg" in normalized and "következő" in normalized)
         or ("biztos" in normalized and "feltételezés" in normalized)
         or ("fő probléma" in normalized and "mit kell" in normalized)
         or ("hasonlítsd össze" in normalized)
         or "mi a lényeg" in normalized
         or "mi legyen a következő" in normalized)
    )

    return DeliberationInput(
        message=message,
        interpretation_kind=interpretation.kind.value,
        recall_resolved=recall.resolved,
        recall_target=recall.target.value,
        recall_clarification=recall.clarification_message,
        has_focus=has_focus,
        followup_detected=followup.detected,
        followup_resolved=followup.resolved,
        followup_ambiguous=followup.ambiguous,
        followup_target=followup.target_line,
        followup_clarification=followup.clarification_message,
        has_previous_thread=has_previous_thread,
        correction_cue=_contains_any(normalized, _CORRECTION_CUES),
        redirect_cue=_contains_any(normalized, _REDIRECT_CUES),
        references_previous_thread=references_previous,
        references_other_target=references_other,
        structured_request=structured_request,
    )
