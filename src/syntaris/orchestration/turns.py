from __future__ import annotations

from dataclasses import dataclass

from syntaris.contracts.runtime import (
    ActiveConversationState,
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


def _resolve_route_and_state(
    store: PersistenceStore,
    context: RuntimeContext,
    request: TalkRequest,
) -> tuple[ActiveConversationState, ActiveConversationState, RouteDecision]:
    state = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )

    mode = request.mode or state.mode
    known_threads = store.list_threads_view(session_id=state.session_id, active_thread_id=state.thread_id).threads
    if request.thread_key:
        route = RouteDecision(
            action=RouteDecisionAction.NO_ROUTE_CHANGE,
            reason="explicit_thread_override",
            thread_key=request.thread_key,
        )
    else:
        route = resolve_route_decision(request.message, state, known_threads)

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
    route = RouteDecision(
        action=route.action,
        reason=route.reason,
        thread_key=route.thread_key,
        match=route.match,
        created_thread=route.created_thread,
        transition=transition,
    )
    return state, updated_state, route


def execute_turn(context: RuntimeContext, request: TalkRequest, source: str = "talk_once") -> TalkRunResult:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)

    state, updated_state, route = _resolve_route_and_state(store, context, request)

    reply_adapter = build_reply_adapter(context.config.reply)
    turn_input = TurnInput(
        message=request.message,
        session_id=state.session_id,
        thread_id=updated_state.thread_id,
        mode=updated_state.mode,
    )
    reply: ReplyOutput = reply_adapter.generate(turn_input)

    turn = store.create_turn(
        session_id=state.session_id,
        thread_id=updated_state.thread_id,
        thread_key=updated_state.thread_key,
        mode=updated_state.mode,
        user_message=request.message,
        assistant_reply=reply.text,
        reply_backend=reply.backend,
        degraded=reply.degraded,
    )

    trace_events = build_turn_trace_events(
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
        events=trace_events,
    )

    latest_state = store.get_active_state() or updated_state
    return TalkRunResult(turn=turn, state=latest_state, route=route)
