from syntaris.contracts.runtime import ActiveConversationState, RuntimeContext, TurnResult


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
) -> list[dict[str, object]]:
    return [
        {
            "event_name": "active_state_resolved",
            "payload": {
                "session_id": state.session_id,
                "thread_id": state.thread_id,
                "thread_key": state.thread_key,
                "mode": state.mode,
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
