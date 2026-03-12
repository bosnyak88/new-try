from __future__ import annotations

from syntaris.contracts.runtime import (
    AnswerStrategy,
    AnswerStrategySelection,
    CandidateKind,
    ClarificationNeed,
    ClarificationQuestionSpec,
    ComparisonPack,
    ComparisonReason,
    ConfidenceBand,
    DeliberationCandidate,
    DeliberationInput,
    RuntimeContext,
)


def _score_to_band(score: int) -> ConfidenceBand:
    if score >= 7:
        return ConfidenceBand.HIGH
    if score >= 4:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW


def _clarification_for_input(item: DeliberationInput, cause: str) -> ClarificationQuestionSpec:
    if cause == "other_target_ambiguous":
        return ClarificationQuestionSpec(
            question="A jelenlegi szálra gondolsz, vagy az előzőre térjünk vissza?",
            cause=cause,
        )
    return ClarificationQuestionSpec(
        question=item.followup_clarification or item.recall_clarification or "Pontosíts kérlek röviden, mire gondolsz.",
        cause=cause,
    )


def build_comparison_pack(context: RuntimeContext, item: DeliberationInput) -> ComparisonPack:
    candidates: list[DeliberationCandidate] = []

    candidates.append(
        DeliberationCandidate(
            kind=CandidateKind.DIRECT,
            strategy=AnswerStrategy.DIRECT_ANSWER,
            score=2,
            confidence=ConfidenceBand.LOW,
            reasons=[ComparisonReason.DEFAULT_FALLBACK],
        )
    )

    if item.structured_request:
        candidates.append(
            DeliberationCandidate(
                kind=CandidateKind.STRUCTURED,
                strategy=AnswerStrategy.STRUCTURED_ANSWER,
                score=7,
                confidence=ConfidenceBand.HIGH,
                reasons=[ComparisonReason.STRUCTURED_REQUEST],
            )
        )

    if item.recall_resolved and item.recall_target in {"current", "previous", "named"}:
        strategy = AnswerStrategy.RECALL_ANSWER if item.interpretation_kind.startswith("recall") else AnswerStrategy.RESUME_ANSWER
        kind = CandidateKind.RECALL if strategy == AnswerStrategy.RECALL_ANSWER else CandidateKind.RESUME
        reason = ComparisonReason.INTERPRETATION_RECALL if strategy == AnswerStrategy.RECALL_ANSWER else ComparisonReason.INTERPRETATION_RESUME
        candidates.append(
            DeliberationCandidate(
                kind=kind,
                strategy=strategy,
                score=8,
                confidence=ConfidenceBand.HIGH,
                reasons=[reason],
            )
        )

    if item.followup_detected and item.followup_resolved:
        candidates.append(
            DeliberationCandidate(
                kind=CandidateKind.FOCUS_FOLLOWUP,
                strategy=AnswerStrategy.DIRECT_ANSWER,
                score=6,
                confidence=ConfidenceBand.MEDIUM,
                reasons=[ComparisonReason.FOLLOWUP_TARGET_RESOLVED],
            )
        )

    if item.correction_cue or item.redirect_cue:
        reasons = []
        if item.correction_cue:
            reasons.append(ComparisonReason.CORRECTION_CUE)
        if item.redirect_cue:
            reasons.append(ComparisonReason.REDIRECT_CUE)
        if item.references_previous_thread and item.has_previous_thread:
            reasons.append(ComparisonReason.PREVIOUS_THREAD_AVAILABLE)
        candidates.append(
            DeliberationCandidate(
                kind=CandidateKind.CORRECTION_REDIRECT,
                strategy=AnswerStrategy.CORRECTION_REDIRECT,
                score=6 if item.has_previous_thread else 4,
                confidence=ConfidenceBand.MEDIUM,
                reasons=reasons or [ComparisonReason.REDIRECT_CUE],
            )
        )

    if item.followup_ambiguous or item.recall_clarification is not None or (item.references_other_target and not item.references_previous_thread):
        cause = "followup_ambiguous" if item.followup_ambiguous else "other_target_ambiguous" if item.references_other_target else "recall_ambiguous"
        reasons = [ComparisonReason.FOLLOWUP_AMBIGUOUS if item.followup_ambiguous else ComparisonReason.RECALL_CLARIFICATION]
        candidates.append(
            DeliberationCandidate(
                kind=CandidateKind.CLARIFICATION,
                strategy=AnswerStrategy.CLARIFICATION,
                score=7,
                confidence=ConfidenceBand.HIGH,
                reasons=reasons,
                clarification=_clarification_for_input(item, cause),
            )
        )

    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)[: max(1, context.config.conversation.max_comparison_candidates)]
    winner = ranked[0]
    return ComparisonPack(built=True, candidates=ranked, winner_kind=winner.kind, winner_score=winner.score)


def select_answer_strategy(context: RuntimeContext, pack: ComparisonPack) -> AnswerStrategySelection:
    ranked = pack.candidates
    winner = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    if (
        context.config.conversation.clarification_prefer_when_close
        and runner_up is not None
        and winner.strategy != AnswerStrategy.CLARIFICATION
        and winner.score - runner_up.score <= 1
    ):
        clarification = ClarificationQuestionSpec(
            question="Pontosíts kérlek egy rövid mondatban, melyik irányra menjünk tovább.",
            cause="close_candidates",
        )
        return AnswerStrategySelection(
            strategy=AnswerStrategy.CLARIFICATION,
            selected_candidate_kind=CandidateKind.CLARIFICATION,
            confidence=ConfidenceBand.MEDIUM,
            reasons=[ComparisonReason.CLOSE_CANDIDATES],
            clarification_need=ClarificationNeed(needed=True, cause="close_candidates"),
            clarification_question=clarification,
        )

    clarification = winner.clarification if winner.strategy == AnswerStrategy.CLARIFICATION else None
    return AnswerStrategySelection(
        strategy=winner.strategy,
        selected_candidate_kind=winner.kind,
        confidence=winner.confidence,
        reasons=winner.reasons,
        clarification_need=ClarificationNeed(needed=winner.strategy == AnswerStrategy.CLARIFICATION, cause=clarification.cause if clarification else None),
        clarification_question=clarification,
    )
