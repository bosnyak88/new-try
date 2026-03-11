from syntaris.contracts.runtime import RuntimeContext, TurnResult


def build_boot_trace(context: RuntimeContext) -> dict[str, str | bool]:
    return {
        "event": "runtime_bootstrap",
        "environment": context.config.environment,
        "trace_enabled": context.config.trace_enabled,
    }


def build_turn_trace_events(turn: TurnResult, backend: str, degraded: bool) -> list[dict[str, object]]:
    return [
        {
            "event_name": "turn_received",
            "payload": {"session_id": turn.session_id, "turn_id": turn.turn_id},
        },
        {
            "event_name": "reply_generated",
            "payload": {"backend": backend, "degraded": degraded},
        },
        {
            "event_name": "turn_persisted",
            "payload": {"turn_id": turn.turn_id},
        },
    ]
