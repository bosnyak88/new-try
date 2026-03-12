from __future__ import annotations

from syntaris.orchestration.text_normalize import clean_display_text
from syntaris.contracts.runtime import (
    AnswerStrategy,
    AnswerStrategySelection,
    ComparisonPack,
    DecompositionPlan,
    EvidencePack,
    ObjectiveFrame,
    RecallResolution,
    ResponsePlan,
    ResponsePlanKind,
    ResponsePlanSection,
    RuntimeContext,
    SynthesisPlan,
    ThreadFocusPack,
    TurnInterpretation,
)


def _synthesis_sections(synthesis: SynthesisPlan) -> list[ResponsePlanSection]:
    return [
        ResponsePlanSection(title=section.key, lines=section.lines)
        for section in synthesis.sections
        if section.lines
    ]


def _direct_should_use_synthesis(objective: ObjectiveFrame, decomposition: DecompositionPlan, synthesis: SynthesisPlan) -> bool:
    _ = synthesis
    if objective.kind.value in {"mixed_multi_part", "status_check", "diagnose", "compare", "next_step"}:
        return True
    if decomposition.multi_part:
        return True
    target_kinds = {"status_check", "diagnose", "compare", "next_step"}
    return any(unit.objective_kind.value in target_kinds for unit in decomposition.units)


def build_response_plan(
    context: RuntimeContext,
    interpretation: TurnInterpretation,
    recall: RecallResolution,
    strategy: AnswerStrategySelection,
    comparison_pack: ComparisonPack,
    objective: ObjectiveFrame,
    decomposition: DecompositionPlan,
    evidence_pack: EvidencePack,
    synthesis: SynthesisPlan,
    focus: ThreadFocusPack | None = None,
    followup_target: str | None = None,
) -> ResponsePlan:
    if strategy.strategy == AnswerStrategy.CLARIFICATION:
        question = strategy.clarification_question.question if strategy.clarification_question else (recall.clarification_message or "Pontosíts kérlek.")
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=[question])],
            focus_used=focus is not None,
        )

    if objective.kind.value == "clarify":
        return ResponsePlan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=["Pontosíts kérlek röviden, mit hasonlítsak vagy melyik szálra gondolsz."])],
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.RECALL_ANSWER, AnswerStrategy.RESUME_ANSWER} and recall.resolved and recall.snapshot is not None:
        limit = max(1, context.config.conversation.recall_line_limit)
        selected = recall.snapshot.snapshot_lines[-limit:]
        lead = "Röviden itt tartottunk:" if interpretation.kind.value.startswith("recall") else f"Visszahoztam a(z) {recall.snapshot.thread_key} szálat."
        lines = [lead]
        for line in selected:
            lines.append(f"• #{line.turn_index}: {clean_display_text(line.user_message)} → {clean_display_text(line.assistant_reply)}")
        followup = "Innen menjünk tovább?" if context.config.conversation.response_followup_enabled else None
        return ResponsePlan(
            kind=ResponsePlanKind.RECALL if interpretation.kind.value.startswith("recall") else ResponsePlanKind.RESUME,
            sections=[ResponsePlanSection(title="recall_summary", lines=lines)],
            followup_prompt=followup,
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.STRUCTURED_ANSWER, AnswerStrategy.UNCERTAINTY_LABELED_ANSWER}:
        sections = _synthesis_sections(synthesis)
        if not sections:
            sections = [ResponsePlanSection(title="ordinary", lines=["Rendben."])]
        kind = ResponsePlanKind.STRUCTURED if strategy.strategy != AnswerStrategy.UNCERTAINTY_LABELED_ANSWER else ResponsePlanKind.UNCERTAINTY_LABELED
        return ResponsePlan(kind=kind, sections=sections, focus_used=focus is not None)

    if strategy.strategy == AnswerStrategy.DIRECT_ANSWER:
        if _direct_should_use_synthesis(objective, decomposition, synthesis):
            sections = _synthesis_sections(synthesis)
            if sections:
                return ResponsePlan(
                    kind=ResponsePlanKind.STRUCTURED,
                    sections=sections,
                    focus_used=focus is not None,
                )
        lines = [f"Rendben, innen folytatjuk: {clean_display_text(followup_target)}"] if followup_target else ["Rendben."]
        return ResponsePlan(
            kind=ResponsePlanKind.ORDINARY,
            sections=[ResponsePlanSection(title="ordinary", lines=lines)],
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

    ordinary_lines: list[str] = []
    if followup_target:
        ordinary_lines.append(f"Rendben, innen folytatjuk: {clean_display_text(followup_target)}")
    return ResponsePlan(
        kind=ResponsePlanKind.ORDINARY,
        sections=[ResponsePlanSection(title="ordinary", lines=ordinary_lines)],
        focus_used=focus is not None,
    )
