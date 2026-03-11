from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from syntaris.contracts.runtime import (
    ActiveConversationState,
    PendingResolutionAction,
    PendingRouteProposal,
    RouteDecision,
    RouteDecisionAction,
    RouteStateTransition,
    RuntimeContext,
    TalkRequest,
    TurnInput,
    TurnResult,
)
from syntaris.orchestration.routing import resolve_route_decision
from syntaris.persistence import PersistenceStore
from syntaris.reply.adapters import ReplyOutput
from syntaris.reply.factory import build_reply_adapter
from syntaris.trace.events import build_turn_trace_events


@dataclass(frozen=True)
class TalkRunResult:
    turn: TurnResult
    state: ActiveConversationState
    route: RouteDecision


_AFFIRMATIVE = {"igen", "oké", "mehet", "arra", "igen arra"}
_NEGATIVE = {"nem", "mégse", "maradjon", "ne", "nem arra"}


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
) -> tuple[ActiveConversationState, ActiveConversationState, RouteDecision, str] | None:
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
        return state, updated, routed, request.message

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
            return state, updated, routed, pending.pending_original_message
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
            return state, updated, routed, pending.pending_original_message
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
        return None

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
    return state, updated_state, routed, request.message


def execute_turn(context: RuntimeContext, request: TalkRequest, source: str = "talk_once") -> TalkRunResult:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)

    resolved = _resolve_route_and_state(store, context, request, source)
    if resolved is None:
        active = store.get_active_state()
        assert active is not None and active.pending_route is not None
        pending = active.pending_route
        assistant = f"A(z) {pending.pending_thread_key} szálra váltsak? (igen/nem)"
        turn = store.create_turn(
            session_id=active.session_id,
            thread_id=active.thread_id,
            thread_key=active.thread_key,
            mode=active.mode,
            user_message=request.message,
            assistant_reply=assistant,
            reply_backend="deterministic",
            degraded=True,
        )
        route = RouteDecision(
            action=RouteDecisionAction.PROPOSE_SWITCH_EXISTING,
            reason="pending_route_proposed",
            thread_key=active.thread_key,
            pending_proposal=PendingRouteProposal(
                held_user_message=pending.pending_original_message,
                proposed_thread_key=pending.pending_thread_key,
                current_thread_key=active.thread_key,
                reason=pending.pending_reason,
                match_pattern=pending.match_pattern,
                source=pending.source,
                proposed_at=pending.proposed_at,
            ),
            pending_resolution=PendingResolutionAction.NONE,
            execution_message=request.message,
        )
        events = build_turn_trace_events(
            state=active,
            turn=turn,
            backend="deterministic",
            degraded=True,
            source=source,
            route=route,
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
        return TalkRunResult(turn=turn, state=active, route=route)

    state, updated_state, route, execution_message = resolved
    reply_adapter = build_reply_adapter(context.config.reply)
    reply: ReplyOutput = reply_adapter.generate(
        TurnInput(
            message=execution_message,
            session_id=state.session_id,
            thread_id=updated_state.thread_id,
            mode=updated_state.mode,
        )
    )

    turn = store.create_turn(
        session_id=state.session_id,
        thread_id=updated_state.thread_id,
        thread_key=updated_state.thread_key,
        mode=updated_state.mode,
        user_message=execution_message,
        assistant_reply=reply.text,
        reply_backend=reply.backend,
        degraded=reply.degraded,
    )
    events = build_turn_trace_events(
        state=updated_state,
        turn=turn,
        backend=reply.backend,
        degraded=reply.degraded,
        source=source,
        route=route,
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
    latest_state = store.get_active_state() or updated_state
    return TalkRunResult(turn=turn, state=latest_state, route=route)
