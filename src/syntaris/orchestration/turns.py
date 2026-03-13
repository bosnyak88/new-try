from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from syntaris.contracts.runtime import (
    ActiveConversationState,
    PendingResolutionAction,
    PendingRouteProposal,
    RouteDecision,
    RouteDecisionAction,
    FollowupTrace,
    RecapTrace,
    RecallTrace,
    ResponsePlanTrace,
    ComparisonPackTrace,
    AnswerStrategyTrace,
    ObjectiveFrameTrace,
    DecompositionTrace,
    EvidencePackTrace,
    SynthesisTrace,
    ThreadFocusTrace,
    TurnInterpretTrace,
    ClaimCaptureTrace,
    RouteStateTransition,
    RuntimeContext,
    SnapshotTrace,
    SnapshotTarget,
    ThreadSnapshotRequest,
    FocusTarget,
    ThreadFocusRequest,
    TalkRequest,
    TurnInput,
    TurnResult,
)
from syntaris.orchestration.context_pack import load_execution_context_pack
from syntaris.orchestration.followup_resolution import resolve_followup_reference
from syntaris.orchestration.thread_focus import build_thread_focus_view, refresh_thread_focus
from syntaris.orchestration.deliberation import assemble_deliberation_input
from syntaris.orchestration.answer_strategy import build_comparison_pack, select_answer_strategy
from syntaris.orchestration.thread_snapshot import build_thread_snapshot_view, refresh_snapshot_for_transition
from syntaris.orchestration.turn_interpret import interpret_turn
from syntaris.orchestration.thread_recall import resolve_recall_request
from syntaris.orchestration.objective_frame import frame_objective
from syntaris.orchestration.question_decompose import build_decomposition_plan
from syntaris.orchestration.evidence_pack import build_evidence_pack
from syntaris.orchestration.answer_synthesis import build_synthesis_plan
from syntaris.orchestration.text_normalize import preprocess_turn_message
from syntaris.orchestration.response_plan import build_response_plan
from syntaris.orchestration.time_context import build_time_context
from syntaris.orchestration.routing import resolve_route_decision
from syntaris.persistence import PersistenceStore
from syntaris.reply.adapters import ReplyOutput
from syntaris.reply.plan_renderer import render_response_plan
from syntaris.reply.factory import build_reply_adapter
from syntaris.trace.events import build_turn_trace_events


@dataclass(frozen=True)
class TalkRunResult:
    turn: TurnResult
    state: ActiveConversationState
    route: RouteDecision
    output_kind: str = "turn"


_AFFIRMATIVE = {"igen", "oké", "mehet", "arra", "igen arra"}
_NEGATIVE = {"nem", "mégse", "maradjon", "ne", "nem arra"}


@dataclass(frozen=True)
class _RouteResolution:
    state_before: ActiveConversationState
    state_after: ActiveConversationState
    route: RouteDecision
    execution_message: str | None


def _apply_state_transition(
    store: PersistenceStore,
    state: ActiveConversationState,
    mode: str,
    route: RouteDecision,
) -> tuple[ActiveConversationState, RouteDecision]:
    thread_key = route.thread_key or state.thread_key
    thread = store.open_or_create_thread(state.session_id, thread_key)
    store.set_active_state(session_id=state.session_id, thread_id=thread.thread_id, mode=mode)
    updated_state = store.get_active_state()
    assert updated_state is not None

    transition = RouteStateTransition(
        before_thread_id=state.thread_id,
        before_thread_key=state.thread_key,
        before_previous_thread_id=state.previous_thread_id,
        before_previous_thread_key=state.previous_thread_key,
        after_thread_id=updated_state.thread_id,
        after_thread_key=updated_state.thread_key,
        after_previous_thread_id=updated_state.previous_thread_id,
        after_previous_thread_key=updated_state.previous_thread_key,
    )
    return updated_state, RouteDecision(
        action=route.action,
        reason=route.reason,
        thread_key=route.thread_key,
        match=route.match,
        created_thread=route.created_thread,
        transition=transition,
        pending_proposal=route.pending_proposal,
        pending_resolution=route.pending_resolution,
        execution_message=route.execution_message,
    )


def _resolve_route_and_state(
    store: PersistenceStore,
    context: RuntimeContext,
    request: TalkRequest,
    source: str,
) -> _RouteResolution:
    state = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )
    mode = request.mode or state.mode

    if request.thread_key:
        route = RouteDecision(
            action=RouteDecisionAction.NO_ROUTE_CHANGE,
            reason="explicit_thread_override",
            thread_key=request.thread_key,
            execution_message=request.message,
        )
        updated, routed = _apply_state_transition(store, state, mode, route)
        return _RouteResolution(state_before=state, state_after=updated, route=routed, execution_message=request.message)

    pending_resolution = PendingResolutionAction.NONE
    pending = state.pending_route
    normalized = preprocess_turn_message(request.message).strip().lower()
    if pending is not None:
        if normalized in _AFFIRMATIVE:
            route = RouteDecision(
                action=RouteDecisionAction.SWITCH_EXISTING,
                reason="pending_route_confirmed",
                thread_key=pending.pending_thread_key,
                pending_resolution=PendingResolutionAction.CONFIRMED,
                execution_message=pending.pending_original_message,
            )
            store.clear_pending_route()
            updated, routed = _apply_state_transition(store, state, mode, route)
            return _RouteResolution(
                state_before=state,
                state_after=updated,
                route=routed,
                execution_message=pending.pending_original_message,
            )
        if normalized in _NEGATIVE:
            route = RouteDecision(
                action=RouteDecisionAction.CONTINUE_ACTIVE,
                reason="pending_route_rejected",
                thread_key=state.thread_key,
                pending_resolution=PendingResolutionAction.REJECTED,
                execution_message=pending.pending_original_message,
            )
            store.clear_pending_route()
            updated, routed = _apply_state_transition(store, state, mode, route)
            return _RouteResolution(
                state_before=state,
                state_after=updated,
                route=routed,
                execution_message=pending.pending_original_message,
            )
        store.clear_pending_route()
        pending_resolution = PendingResolutionAction.CANCELLED
        state = store.get_active_state() or state

    known_threads = store.list_threads_view(session_id=state.session_id, active_thread_id=state.thread_id).threads
    route = resolve_route_decision(request.message, state, known_threads, source=source)

    if route.pending_proposal is not None and route.action in {
        RouteDecisionAction.PROPOSE_SWITCH_EXISTING,
        RouteDecisionAction.PROPOSE_SWITCH_PREVIOUS,
    }:
        proposal = PendingRouteProposal(
            held_user_message=route.pending_proposal.held_user_message,
            proposed_thread_key=route.pending_proposal.proposed_thread_key,
            current_thread_key=route.pending_proposal.current_thread_key,
            reason=route.pending_proposal.reason,
            match_pattern=route.pending_proposal.match_pattern,
            source=source,
            proposed_at=context.clock.now().isoformat(),
        )
        store.set_pending_route(proposal)
        state_after = store.get_active_state() or state
        proposal_route = RouteDecision(
            action=route.action,
            reason="pending_route_proposed",
            thread_key=state_after.thread_key,
            match=route.match,
            pending_proposal=proposal,
            execution_message=request.message,
        )
        return _RouteResolution(state_before=state, state_after=state_after, route=proposal_route, execution_message=None)

    route = RouteDecision(
        action=route.action,
        reason=route.reason,
        thread_key=route.thread_key,
        match=route.match,
        created_thread=route.created_thread,
        pending_resolution=pending_resolution,
        execution_message=request.message,
    )
    updated_state, routed = _apply_state_transition(store, state, mode, route)
    return _RouteResolution(state_before=state, state_after=updated_state, route=routed, execution_message=request.message)


def execute_turn(context: RuntimeContext, request: TalkRequest, source: str = "talk_once") -> TalkRunResult:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)

    resolved = _resolve_route_and_state(store, context, request, source)
    snapshot_trace: SnapshotTrace | None = None

    transition_snapshot = refresh_snapshot_for_transition(
        context=context,
        from_thread_id=resolved.state_before.thread_id,
        from_mode=resolved.state_before.mode,
        switched=resolved.state_before.thread_id != resolved.state_after.thread_id,
        source=source,
    )
    if transition_snapshot is not None:
        meta = transition_snapshot.snapshot.source_metadata
        snapshot_trace = SnapshotTrace(
            built=True,
            refreshed=transition_snapshot.refreshed,
            source=transition_snapshot.reason,
            thread_id=transition_snapshot.snapshot.thread_id,
            thread_key=transition_snapshot.snapshot.thread_key,
            source_turn_count=meta.source_turn_count,
            included_turn_count=meta.included_turn_count,
            filtered_recap_turn_count=meta.filtered_recap_turn_count,
            filtered_pending_turn_count=meta.filtered_pending_turn_count,
            filtered_control_turn_count=meta.filtered_control_turn_count,
        )

    turn_created_at = context.clock.now()

    if resolved.execution_message is None:
        pending = resolved.state_after.pending_route
        assert pending is not None
        assistant = f"A(z) {pending.pending_thread_key} szálra váltsak? (igen/nem)"
        turn = store.create_turn(
            session_id=resolved.state_after.session_id,
            thread_id=resolved.state_after.thread_id,
            thread_key=resolved.state_after.thread_key,
            mode=resolved.state_after.mode,
            user_message=request.message,
            assistant_reply=assistant,
            reply_backend="deterministic",
            degraded=True,
            created_at=turn_created_at,
        )
        context_load = load_execution_context_pack(
            context=context,
            session_id=resolved.state_after.session_id,
            thread_id=resolved.state_after.thread_id,
            mode=resolved.state_after.mode,
        )
        events = build_turn_trace_events(
            state=resolved.state_after,
            turn=turn,
            backend="deterministic",
            degraded=True,
            source=source,
            route=resolved.route,
            context_load=context_load,
            snapshot_trace=snapshot_trace,
            claim_capture_trace=None,
        )
        store.create_trace_events(
            session_id=turn.session_id,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            mode=turn.mode,
            backend="deterministic",
            degraded=True,
            events=events,
        )
        return TalkRunResult(turn=turn, state=resolved.state_after, route=resolved.route)

    context_load = load_execution_context_pack(
        context=context,
        session_id=resolved.state_after.session_id,
        thread_id=resolved.state_after.thread_id,
        mode=resolved.state_after.mode,
    )

    execution_message = resolved.execution_message
    normalized_message = preprocess_turn_message(execution_message)
    interpretation = interpret_turn(normalized_message)
    last_turn_at = store.read_last_turn_at(resolved.state_after.thread_id)
    time_context = build_time_context(context, last_turn_at=last_turn_at, relative_terms=interpretation.relative_time_terms)
    personal_memory = store.get_personal_memory(session_id=resolved.state_after.session_id, thread_id=resolved.state_after.thread_id)
    owner_identity = store.get_owner_identity()
    recall_resolution = resolve_recall_request(context, interpretation)
    focus_view = build_thread_focus_view(
        context,
        ThreadFocusRequest(target=FocusTarget.CURRENT, source=f"{source}:turn"),
    )
    if context.config.conversation.followup_resolution_enabled:
        lower_message = normalized_message.strip().lower()
        followup_only_cue = any(phrase in lower_message for phrase in {"erről", "ebből", "abból"})
        structured_cue = any(phrase in lower_message for phrase in {"lényeg", "következő", "biztos", "feltételezés", "fő probléma", "hasonlítsd össze"})
        if focus_view.found and focus_view.focus is not None and bool(focus_view.focus.focus_lines):
            followup_resolution = resolve_followup_reference(normalized_message, focus_view.focus)
        elif followup_only_cue and not structured_cue:
            followup_resolution = resolve_followup_reference(normalized_message, None)
        else:
            followup_resolution = resolve_followup_reference("", None)
    else:
        followup_resolution = resolve_followup_reference("", None)

    deliberation_input = assemble_deliberation_input(
        message=normalized_message,
        interpretation=interpretation,
        recall=recall_resolution,
        followup=followup_resolution,
        has_focus=focus_view.found and focus_view.focus is not None,
        has_previous_thread=resolved.state_after.previous_thread_id is not None,
    )
    comparison_pack = build_comparison_pack(context, deliberation_input)
    strategy_selection = select_answer_strategy(context, comparison_pack)
    objective = frame_objective(normalized_message, strategy_selection)
    decomposition = build_decomposition_plan(normalized_message, objective)
    max_units = max(1, context.config.conversation.max_reasoning_units)
    decomposition = type(decomposition)(units=decomposition.units[:max_units], multi_part=decomposition.multi_part)
    current_summary: str | None = None
    if context_load.pack.recent_turns:
        last = context_load.pack.recent_turns[-1]
        current_summary = f"#{last.turn_index}: {preprocess_turn_message(last.user_message)}"

    previous_view = build_thread_snapshot_view(
        context,
        ThreadSnapshotRequest(target=SnapshotTarget.PREVIOUS, source=f"{source}:evidence_compare"),
    )
    previous_summary: str | None = None
    if previous_view.found and previous_view.snapshot is not None and previous_view.snapshot.snapshot_lines:
        prev_last = previous_view.snapshot.snapshot_lines[-1]
        previous_summary = f"#{prev_last.turn_index}: {preprocess_turn_message(prev_last.user_message)}"
    if previous_summary is None and resolved.state_after.previous_thread_id is not None:
        previous_context = store.build_thread_context_pack(
            thread_id=resolved.state_after.previous_thread_id,
            mode=resolved.state_after.mode,
            turn_window=1,
        )
        if previous_context is not None and previous_context.recent_turns:
            prev_last = previous_context.recent_turns[-1]
            previous_summary = f"#{prev_last.turn_index}: {preprocess_turn_message(prev_last.user_message)}"

    evidence_pack = build_evidence_pack(
        message=normalized_message,
        decomposition=decomposition,
        recall=recall_resolution,
        focus=focus_view.focus if focus_view.found else None,
        followup=followup_resolution,
        current_thread_summary=current_summary,
        previous_thread_summary=previous_summary,
    )
    max_items = max(1, context.config.conversation.max_evidence_items_per_unit) * max(1, len(decomposition.units))
    has_compare_unit = any(unit.objective_kind.value == "compare" for unit in decomposition.units)
    if has_compare_unit:
        compare_priority = {"current_message": 0, "current_thread": 1, "previous_thread": 2, "support_gap": 3}
        prioritized = sorted(
            evidence_pack.items,
            key=lambda item: (compare_priority.get(item.source, 10), item.unit_id, item.source),
        )
        evidence_pack = type(evidence_pack)(items=prioritized[:max_items])
    else:
        evidence_pack = type(evidence_pack)(items=evidence_pack.items[:max_items])
    synthesis_plan = build_synthesis_plan(objective, decomposition, evidence_pack)
    response_plan = build_response_plan(
        context,
        interpretation,
        recall_resolution,
        strategy=strategy_selection,
        comparison_pack=comparison_pack,
        objective=objective,
        decomposition=decomposition,
        evidence_pack=evidence_pack,
        synthesis=synthesis_plan,
        focus=focus_view.focus if focus_view.found else None,
        followup_target=followup_resolution.target_line,
        owner_identity=owner_identity,
        personal_memory=personal_memory,
        time_context=time_context,
    )

    recap_trace = RecapTrace(recognized=False)
    interpret_trace = TurnInterpretTrace(
        kind=interpretation.kind.value,
        pattern_name=interpretation.pattern_name,
        clarification_reason=interpretation.clarification_reason,
        personal_entry_kind=interpretation.personal_entry.kind.value if interpretation.personal_entry is not None else None,
        owner_name=interpretation.personal_entry.owner_name if interpretation.personal_entry is not None else None,
        owner_relation=interpretation.personal_entry.owner_relation if interpretation.personal_entry is not None else None,
        declared_focus=interpretation.personal_entry.declared_focus if interpretation.personal_entry is not None else None,
        declared_direction=interpretation.personal_entry.declared_direction if interpretation.personal_entry is not None else None,
        memory_query=interpretation.memory_query.value if interpretation.memory_query is not None else None,
        claim_capture_count=len(interpretation.claim_capture),
        relative_time_terms=interpretation.relative_time_terms,
    )
    recall_trace = RecallTrace(
        requested=interpretation.recall_request is not None,
        request_target=interpretation.recall_request.target.value if interpretation.recall_request is not None else None,
        resolved_target=recall_resolution.target.value,
        thread_id=recall_resolution.thread_id,
        thread_key=recall_resolution.thread_key,
        used_snapshot=recall_resolution.used_snapshot,
        loaded_from_persistence=recall_resolution.loaded_from_persistence,
        refreshed_snapshot=recall_resolution.refreshed_snapshot,
        clarification_emitted=response_plan.kind.value == "clarification",
    )
    claim_trace = ClaimCaptureTrace(
        captured=bool(interpretation.claim_capture),
        items=[f"{item.scope.value}:{item.kind.value}={item.value}" for item in interpretation.claim_capture],
    )

    plan_trace = ResponsePlanTrace(
        kind=response_plan.kind.value,
        section_count=len(response_plan.sections),
        clarification_emitted=response_plan.kind.value == "clarification",
        focus_used=response_plan.focus_used,
        daypart=time_context.daypart.value,
        gap_kind=time_context.gap_kind.value,
        relative_grounding=[f"{item.term}:{item.resolved_label}" for item in time_context.relative_grounding],
    )
    focus_trace = ThreadFocusTrace(
        loaded=focus_view.found and focus_view.focus is not None,
        loaded_from_persistence=focus_view.loaded_from_persistence,
        thread_id=focus_view.focus.thread_id if focus_view.focus is not None else None,
        thread_key=focus_view.focus.thread_key if focus_view.focus is not None else None,
        source_turn_count=focus_view.focus.source_metadata.source_turn_count if focus_view.focus is not None else 0,
        included_turn_count=focus_view.focus.source_metadata.included_turn_count if focus_view.focus is not None else 0,
        filtered_recap_turn_count=focus_view.focus.source_metadata.filtered_recap_turn_count if focus_view.focus is not None else 0,
        filtered_pending_turn_count=focus_view.focus.source_metadata.filtered_pending_turn_count if focus_view.focus is not None else 0,
        filtered_control_turn_count=focus_view.focus.source_metadata.filtered_control_turn_count if focus_view.focus is not None else 0,
    )
    followup_trace = FollowupTrace(
        detected=followup_resolution.detected,
        resolved=followup_resolution.resolved,
        ambiguous=followup_resolution.ambiguous,
        phrase=followup_resolution.phrase,
        target_line=followup_resolution.target_line,
        clarification_emitted=followup_resolution.ambiguous,
    )
    comparison_trace = ComparisonPackTrace(
        built=comparison_pack.built,
        candidate_count=len(comparison_pack.candidates),
        candidate_kinds=[candidate.kind.value for candidate in comparison_pack.candidates],
        winner_kind=comparison_pack.winner_kind.value,
        winner_score=comparison_pack.winner_score,
    )
    answer_strategy_trace = AnswerStrategyTrace(
        selected_strategy=strategy_selection.strategy.value,
        selected_candidate_kind=strategy_selection.selected_candidate_kind.value,
        confidence=strategy_selection.confidence.value,
        clarification_planned=strategy_selection.clarification_need.needed,
        clarification_cause=strategy_selection.clarification_need.cause,
    )

    objective_trace = ObjectiveFrameTrace(
        kind=objective.kind.value,
        is_multi_part=objective.is_multi_part,
        secondary_kinds=[item.value for item in objective.secondary_kinds],
    )
    decomposition_trace = DecompositionTrace(
        unit_count=len(decomposition.units),
        unit_kinds=[unit.objective_kind.value for unit in decomposition.units],
    )
    support_distribution: dict[str, int] = {}
    for item in evidence_pack.items:
        support_distribution[item.support.value] = support_distribution.get(item.support.value, 0) + 1
    evidence_trace = EvidencePackTrace(
        item_count=len(evidence_pack.items),
        support_distribution=support_distribution,
    )
    synthesis_trace = SynthesisTrace(
        section_count=len(synthesis_plan.sections),
        section_keys=[section.key for section in synthesis_plan.sections],
        partial=synthesis_plan.partial,
    )

    if response_plan.kind.value in {"recall", "resume", "clarification"} or any(section.lines for section in response_plan.sections):
        planned_text = render_response_plan(response_plan)
        turn = store.create_turn(
            session_id=resolved.state_before.session_id,
            thread_id=resolved.state_after.thread_id,
            thread_key=resolved.state_after.thread_key,
            mode=resolved.state_after.mode,
            user_message=execution_message,
            assistant_reply=planned_text,
            reply_backend="deterministic",
            degraded=False,
            created_at=turn_created_at,
        )
        store.capture_claims(
            session_id=resolved.state_after.session_id,
            thread_id=resolved.state_after.thread_id,
            source_turn_id=turn.turn_id,
            captures=interpretation.claim_capture,
        )
        events = build_turn_trace_events(
            state=resolved.state_after,
            turn=turn,
            backend="deterministic",
            degraded=False,
            source=source,
            route=resolved.route,
            context_load=context_load,
            recap_trace=recap_trace,
            snapshot_trace=snapshot_trace,
            interpret_trace=interpret_trace,
            recall_trace=recall_trace,
            response_plan_trace=plan_trace,
            focus_trace=focus_trace,
            followup_trace=followup_trace,
            comparison_trace=comparison_trace,
            answer_strategy_trace=answer_strategy_trace,
            objective_trace=objective_trace,
            decomposition_trace=decomposition_trace,
            evidence_trace=evidence_trace,
            synthesis_trace=synthesis_trace,
            claim_capture_trace=claim_trace,
        )
        store.create_trace_events(
            session_id=turn.session_id,
            thread_id=turn.thread_id,
            turn_id=turn.turn_id,
            mode=turn.mode,
            backend="deterministic",
            degraded=False,
            events=events,
        )
        updated_focus = refresh_thread_focus(context, thread_id=turn.thread_id, mode=turn.mode, reason=f"{source}:post_turn")
        if updated_focus is not None:
            focus_trace = ThreadFocusTrace(
                loaded=focus_trace.loaded,
                loaded_from_persistence=focus_trace.loaded_from_persistence,
                thread_id=focus_trace.thread_id,
                thread_key=focus_trace.thread_key,
                source_turn_count=focus_trace.source_turn_count,
                included_turn_count=focus_trace.included_turn_count,
                filtered_recap_turn_count=focus_trace.filtered_recap_turn_count,
                filtered_pending_turn_count=focus_trace.filtered_pending_turn_count,
                filtered_control_turn_count=focus_trace.filtered_control_turn_count,
                updated=True,
                update_reason=updated_focus.reason,
            )
        latest_state = store.get_active_state() or resolved.state_after
        output_kind = response_plan.kind.value if response_plan.kind.value in {"recall", "resume", "clarification", "correction_redirect", "structured"} else "turn"
        return TalkRunResult(turn=turn, state=latest_state, route=resolved.route, output_kind=output_kind)

    reply_adapter = build_reply_adapter(context.config.reply)
    reply: ReplyOutput = reply_adapter.generate(
        TurnInput(
            message=execution_message,
            session_id=resolved.state_before.session_id,
            thread_id=resolved.state_after.thread_id,
            mode=resolved.state_after.mode,
        )
    )

    turn = store.create_turn(
        session_id=resolved.state_before.session_id,
        thread_id=resolved.state_after.thread_id,
        thread_key=resolved.state_after.thread_key,
        mode=resolved.state_after.mode,
        user_message=execution_message,
        assistant_reply=reply.text,
        reply_backend=reply.backend,
        degraded=reply.degraded,
        created_at=turn_created_at,
    )
    events = build_turn_trace_events(
        state=resolved.state_after,
        turn=turn,
        backend=reply.backend,
        degraded=reply.degraded,
        source=source,
        route=resolved.route,
        context_load=context_load,
        recap_trace=recap_trace,
        snapshot_trace=snapshot_trace,
        interpret_trace=interpret_trace,
        recall_trace=recall_trace,
        response_plan_trace=plan_trace,
        focus_trace=focus_trace,
        followup_trace=followup_trace,
        comparison_trace=comparison_trace,
        answer_strategy_trace=answer_strategy_trace,
    )
    store.create_trace_events(
        session_id=turn.session_id,
        thread_id=turn.thread_id,
        turn_id=turn.turn_id,
        mode=turn.mode,
        backend=reply.backend,
        degraded=reply.degraded,
        events=events,
    )
    refresh_thread_focus(context, thread_id=turn.thread_id, mode=turn.mode, reason=f"{source}:post_turn")
    latest_state = store.get_active_state() or resolved.state_after
    return TalkRunResult(turn=turn, state=latest_state, route=resolved.route)
