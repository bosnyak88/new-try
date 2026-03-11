from __future__ import annotations

from dataclasses import dataclass

from syntaris.contracts.runtime import (
    ActiveConversationState,
    RouteDecision,
    RouteDecisionAction,
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


def execute_turn(context: RuntimeContext, request: TalkRequest, source: str = "talk_once") -> TalkRunResult:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)

    state = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )

    mode = request.mode or state.mode

    known_threads = store.list_threads_view(session_id=state.session_id, active_thread_id=state.thread_id).threads
    if request.thread_key:
        thread_key = request.thread_key
        route = RouteDecision(
            action=RouteDecisionAction.NO_ROUTE_CHANGE,
            reason="explicit_thread_override",
            thread_key=thread_key,
        )
    else:
        route = resolve_route_decision(request.message, state, known_threads)
        thread_key = route.thread_key or state.thread_key

    thread = store.open_or_create_thread(state.session_id, thread_key)
    store.set_active_state(session_id=state.session_id, thread_id=thread.thread_id, mode=mode)

    effective_state = ActiveConversationState(
        session_id=state.session_id,
        thread_id=thread.thread_id,
        thread_key=thread.thread_key,
        mode=mode,
        turn_count=state.turn_count,
        last_turn_id=state.last_turn_id,
    )

    reply_adapter = build_reply_adapter(context.config.reply)
    turn_input = TurnInput(
        message=request.message,
        session_id=state.session_id,
        thread_id=thread.thread_id,
        mode=mode,
    )
    reply: ReplyOutput = reply_adapter.generate(turn_input)

    turn = store.create_turn(
        session_id=state.session_id,
        thread_id=thread.thread_id,
        thread_key=thread.thread_key,
        mode=mode,
        user_message=request.message,
        assistant_reply=reply.text,
        reply_backend=reply.backend,
        degraded=reply.degraded,
    )

    trace_events = build_turn_trace_events(
        state=effective_state,
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

    updated_state = store.get_active_state() or effective_state
    return TalkRunResult(turn=turn, state=updated_state, route=route)
