from __future__ import annotations

from syntaris.contracts.runtime import (
    AnswerStrategy,
    AnswerStrategySelection,
    ComparisonPack,
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
    strategy: AnswerStrategySelection,
    comparison_pack: ComparisonPack,
    focus: ThreadFocusPack | None = None,
    followup_target: str | None = None,
) -> ResponsePlan:
    if strategy.strategy == AnswerStrategy.CLARIFICATION:
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[
                ResponsePlanSection(
                    title="clarification",
                    lines=[strategy.clarification_question.question if strategy.clarification_question else (recall.clarification_message or "Pontosíts kérlek.")],
                )
            ],
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.RECALL_ANSWER, AnswerStrategy.RESUME_ANSWER} and recall.resolved and recall.snapshot is not None:
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

    if strategy.strategy == AnswerStrategy.STRUCTURED_ANSWER:
        lines = ["Lényeg röviden:"]
        if followup_target:
            lines.append(f"• Aktív téma: {followup_target}")
        elif focus and focus.focus_lines:
            lines.append(f"• Aktív téma: {focus.focus_lines[0].text}")
        lines.append("Következő lépés: haladjunk a kijelölt pont mentén, és pontosíts, ha másik szálat szeretnél.")
        return ResponsePlan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="structured", lines=lines)],
            focus_used=focus is not None,
        )

    if strategy.strategy == AnswerStrategy.CORRECTION_REDIRECT:
        lines = ["Rendben, korrigálok és átirányítom a választ a kért irányra."]
        if "előző" in interpretation.kind.value or comparison_pack.winner_kind.value in {"correction_redirect", "resume"}:
            lines.append("Az előző szálhoz igazodva folytatom.")
        return ResponsePlan(
            kind=ResponsePlanKind.CORRECTION_REDIRECT,
            sections=[ResponsePlanSection(title="correction_redirect", lines=lines)],
            focus_used=focus is not None,
        )

    if strategy.strategy == AnswerStrategy.UNCERTAINTY_LABELED_ANSWER:
        return ResponsePlan(
            kind=ResponsePlanKind.UNCERTAINTY_LABELED,
            sections=[ResponsePlanSection(title="uncertainty", lines=["Valószínűleg erre gondolsz, de jelezd kérlek, ha másik irányt szeretnél."])],
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
