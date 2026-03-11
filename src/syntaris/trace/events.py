from syntaris.contracts.runtime import ActiveConversationState, RouteDecision, RuntimeContext, TurnResult


def build_boot_trace(context: RuntimeContext) -> dict[str, str | bool]:
    return {
        "event": "runtime_bootstrap",
        "environment": context.config.environment,
        "trace_enabled": context.config.trace_enabled,
    }


def build_turn_trace_events(
    state: ActiveConversationState,
    turn: TurnResult,
    backend: str,
    degraded: bool,
    source: str,
    route: RouteDecision,
) -> list[dict[str, object]]:
    events = [
        {
            "event_name": "route_decision_computed",
            "payload": {
                "action": route.action.value,
                "reason": route.reason,
                "thread_key": route.thread_key,
                "created_thread": route.created_thread,
                "match_pattern": route.match.pattern_name if route.match else None,
                "before_thread_id": route.transition.before_thread_id if route.transition else None,
                "before_thread_key": route.transition.before_thread_key if route.transition else None,
                "before_previous_thread_id": route.transition.before_previous_thread_id if route.transition else None,
                "before_previous_thread_key": route.transition.before_previous_thread_key if route.transition else None,
                "after_thread_id": route.transition.after_thread_id if route.transition else None,
                "after_thread_key": route.transition.after_thread_key if route.transition else None,
                "after_previous_thread_id": route.transition.after_previous_thread_id if route.transition else None,
                "after_previous_thread_key": route.transition.after_previous_thread_key if route.transition else None,
                "pending_resolution": route.pending_resolution.value,
                "execution_message": route.execution_message,
            },
        },
        {
            "event_name": "active_state_resolved",
            "payload": {
                "session_id": state.session_id,
                "thread_id": state.thread_id,
                "thread_key": state.thread_key,
                "mode": state.mode,
                "previous_thread_id": state.previous_thread_id,
                "previous_thread_key": state.previous_thread_key,
            },
        },
        {
            "event_name": "thread_resolved_or_created",
            "payload": {"thread_id": turn.thread_id, "thread_key": turn.thread_key},
        },
        {
            "event_name": "reply_generated",
            "payload": {"backend": backend, "degraded": degraded, "mode": turn.mode},
        },
        {
            "event_name": "turn_persisted",
            "payload": {"turn_id": turn.turn_id, "turn_index": turn.turn_index},
        },
        {
            "event_name": "turn_execution_source",
            "payload": {"source": source},
        },
    ]

    if route.action.value.startswith("propose_switch"):
        events.append(
            {
                "event_name": "pending_route_proposed",
                "payload": {
                    "target_thread_key": route.pending_proposal.proposed_thread_key if route.pending_proposal else route.thread_key,
                    "reason": route.reason,
                },
            }
        )

    if route.pending_resolution.value == "confirmed":
        events.append({"event_name": "pending_route_confirmed", "payload": {"executed_message": route.execution_message}})
    elif route.pending_resolution.value == "rejected":
        events.append({"event_name": "pending_route_rejected", "payload": {"executed_message": route.execution_message}})
    elif route.pending_resolution.value == "cancelled":
        events.append({"event_name": "pending_route_cancelled", "payload": {"new_message": turn.user_message}})

    return events
