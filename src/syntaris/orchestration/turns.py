from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

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
    ThreadFocusTrace,
    TurnInterpretTrace,
    RouteStateTransition,
    RuntimeContext,
    SnapshotTrace,
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
from syntaris.orchestration.thread_snapshot import refresh_snapshot_for_transition
from syntaris.orchestration.turn_interpret import interpret_turn
from syntaris.orchestration.thread_recall import resolve_recall_request
from syntaris.orchestration.response_plan import build_response_plan
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
    normalized = request.message.strip().lower()
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
            proposed_at=datetime.now(timezone.utc).isoformat(),
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
    interpretation = interpret_turn(execution_message)
    recall_resolution = resolve_recall_request(context, interpretation)
    focus_view = build_thread_focus_view(
        context,
        ThreadFocusRequest(target=FocusTarget.CURRENT, source=f"{source}:turn"),
    )
    followup_resolution = resolve_followup_reference(execution_message, focus_view.focus if focus_view.found else None) if context.config.conversation.followup_resolution_enabled else resolve_followup_reference("", None)

    deliberation_input = assemble_deliberation_input(
        message=execution_message,
        interpretation=interpretation,
        recall=recall_resolution,
        followup=followup_resolution,
        has_focus=focus_view.found and focus_view.focus is not None,
        has_previous_thread=resolved.state_after.previous_thread_id is not None,
    )
    comparison_pack = build_comparison_pack(context, deliberation_input)
    strategy_selection = select_answer_strategy(context, comparison_pack)
    response_plan = build_response_plan(
        context,
        interpretation,
        recall_resolution,
        strategy=strategy_selection,
        comparison_pack=comparison_pack,
        focus=focus_view.focus if focus_view.found else None,
        followup_target=followup_resolution.target_line,
    )

    recap_trace = RecapTrace(recognized=False)
    interpret_trace = TurnInterpretTrace(
        kind=interpretation.kind.value,
        pattern_name=interpretation.pattern_name,
        clarification_reason=interpretation.clarification_reason,
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
    plan_trace = ResponsePlanTrace(
        kind=response_plan.kind.value,
        section_count=len(response_plan.sections),
        clarification_emitted=response_plan.kind.value == "clarification",
        focus_used=response_plan.focus_used,
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
        return TalkRunResult(turn=turn, state=latest_state, route=resolved.route, output_kind=response_plan.kind.value)

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
