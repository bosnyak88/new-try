from syntaris.contracts.runtime import ActiveConversationState, ContextLoadResult, FollowupTrace, RecapTrace, RecallTrace, ResponsePlanTrace, RouteDecision, RuntimeContext, SnapshotTrace, ThreadFocusTrace, TurnInterpretTrace, TurnResult


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
    context_load: ContextLoadResult,
    recap_trace: RecapTrace | None = None,
    snapshot_trace: SnapshotTrace | None = None,
    interpret_trace: TurnInterpretTrace | None = None,
    recall_trace: RecallTrace | None = None,
    response_plan_trace: ResponsePlanTrace | None = None,
    focus_trace: ThreadFocusTrace | None = None,
    followup_trace: FollowupTrace | None = None,
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
            "event_name": "thread_context_loaded",
            "payload": {
                "source": context_load.source.value,
                "thread_id": context_load.pack.thread_id,
                "thread_key": context_load.pack.thread_key,
                "recent_turn_count": len(context_load.pack.recent_turns),
                "turn_count": context_load.pack.turn_count,
                "last_turn_id": context_load.pack.last_turn_id,
            },
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




    if interpret_trace is not None:
        events.append(
            {
                "event_name": "turn_interpreted",
                "payload": {
                    "kind": interpret_trace.kind,
                    "pattern_name": interpret_trace.pattern_name,
                    "clarification_reason": interpret_trace.clarification_reason,
                },
            }
        )

    if recall_trace is not None:
        events.append(
            {
                "event_name": "recall_resolved",
                "payload": {
                    "requested": recall_trace.requested,
                    "request_target": recall_trace.request_target,
                    "resolved_target": recall_trace.resolved_target,
                    "thread_id": recall_trace.thread_id,
                    "thread_key": recall_trace.thread_key,
                    "used_snapshot": recall_trace.used_snapshot,
                    "loaded_from_persistence": recall_trace.loaded_from_persistence,
                    "refreshed_snapshot": recall_trace.refreshed_snapshot,
                    "clarification_emitted": recall_trace.clarification_emitted,
                },
            }
        )

    if response_plan_trace is not None:
        events.append(
            {
                "event_name": "response_plan_built",
                "payload": {
                    "kind": response_plan_trace.kind,
                    "section_count": response_plan_trace.section_count,
                    "clarification_emitted": response_plan_trace.clarification_emitted,
                    "focus_used": response_plan_trace.focus_used,
                },
            }
        )

    if focus_trace is not None:
        events.append(
            {
                "event_name": "thread_focus_loaded",
                "payload": {
                    "loaded": focus_trace.loaded,
                    "loaded_from_persistence": focus_trace.loaded_from_persistence,
                    "thread_id": focus_trace.thread_id,
                    "thread_key": focus_trace.thread_key,
                    "source_turn_count": focus_trace.source_turn_count,
                    "included_turn_count": focus_trace.included_turn_count,
                    "filtered_recap_turn_count": focus_trace.filtered_recap_turn_count,
                    "filtered_pending_turn_count": focus_trace.filtered_pending_turn_count,
                    "filtered_control_turn_count": focus_trace.filtered_control_turn_count,
                    "updated": focus_trace.updated,
                    "update_reason": focus_trace.update_reason,
                },
            }
        )

    if followup_trace is not None and followup_trace.detected:
        events.append(
            {
                "event_name": "followup_reference_resolved",
                "payload": {
                    "detected": followup_trace.detected,
                    "resolved": followup_trace.resolved,
                    "ambiguous": followup_trace.ambiguous,
                    "phrase": followup_trace.phrase,
                    "target_line": followup_trace.target_line,
                    "clarification_emitted": followup_trace.clarification_emitted,
                },
            }
        )

    if snapshot_trace is not None and snapshot_trace.built:
        events.append(
            {
                "event_name": "thread_snapshot_refreshed",
                "payload": {
                    "refreshed": snapshot_trace.refreshed,
                    "source": snapshot_trace.source,
                    "thread_id": snapshot_trace.thread_id,
                    "thread_key": snapshot_trace.thread_key,
                    "source_turn_count": snapshot_trace.source_turn_count,
                    "included_turn_count": snapshot_trace.included_turn_count,
                    "filtered_recap_turn_count": snapshot_trace.filtered_recap_turn_count,
                    "filtered_pending_turn_count": snapshot_trace.filtered_pending_turn_count,
                    "filtered_control_turn_count": snapshot_trace.filtered_control_turn_count,
                },
            }
        )

    if recap_trace is not None and recap_trace.recognized:
        events.append(
            {
                "event_name": "recap_query_recognized",
                "payload": {
                    "source": recap_trace.source,
                    "target_thread_key": recap_trace.target_thread_key,
                },
            }
        )
        events.append(
            {
                "event_name": "thread_recap_built",
                "payload": {
                    "context_turn_count": recap_trace.context_turn_count,
                    "bypassed_reply_adapter": recap_trace.bypassed_reply_adapter,
                },
            }
        )

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
