from __future__ import annotations

from syntaris.contracts.runtime import (
    RecallResolution,
    ResponsePlan,
    ResponsePlanKind,
    ResponsePlanSection,
    RuntimeContext,
    ThreadFocusPack,
    TurnInterpretation,
    TurnInterpretationKind,
)


def build_response_plan(
    context: RuntimeContext,
    interpretation: TurnInterpretation,
    recall: RecallResolution,
    focus: ThreadFocusPack | None = None,
    followup_target: str | None = None,
) -> ResponsePlan:
    if interpretation.kind == TurnInterpretationKind.CLARIFICATION_NEEDED or recall.clarification_message is not None:
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=[recall.clarification_message or "Pontosíts kérlek."])],
            focus_used=focus is not None,
        )

    if recall.resolved and recall.snapshot is not None:
        limit = max(1, context.config.conversation.recall_line_limit)
        selected = recall.snapshot.snapshot_lines[-limit:]
        lead = "Röviden itt tartottunk:" if interpretation.kind.value.startswith("recall") else f"Visszahoztam a(z) {recall.snapshot.thread_key} szálat."
        lines = [lead]
        for line in selected:
            lines.append(f"• #{line.turn_index}: {line.user_message} → {line.assistant_reply}")
        followup = "Innen menjünk tovább?" if context.config.conversation.response_followup_enabled else None
        return ResponsePlan(
            kind=ResponsePlanKind.RECALL if interpretation.kind.value.startswith("recall") else ResponsePlanKind.RESUME,
            sections=[ResponsePlanSection(title="recall_summary", lines=lines)],
            followup_prompt=followup,
            focus_used=focus is not None,
        )

    ordinary_lines: list[str] = []
    if followup_target:
        ordinary_lines.append(f"Rendben, innen folytatjuk: {followup_target}")
    return ResponsePlan(
        kind=ResponsePlanKind.ORDINARY,
        sections=[ResponsePlanSection(title="ordinary", lines=ordinary_lines)],
        focus_used=focus is not None,
    )
