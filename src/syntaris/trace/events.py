from syntaris.orchestration.text_normalize import clean_display_text
from syntaris.contracts.runtime import ActiveConversationState, AnswerStrategyTrace, ClaimCaptureTrace, ComparisonPackTrace, ContextLoadResult, DecompositionTrace, EvidencePackTrace, FollowupTrace, ObjectiveFrameTrace, RecapTrace, RecallTrace, ResponsePlanTrace, RouteDecision, RuntimeContext, SnapshotTrace, SynthesisTrace, ThreadFocusTrace, ThreadWeaveTrace, TurnInterpretTrace, TurnResult, WorkframeTrace


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
    comparison_trace: ComparisonPackTrace | None = None,
    answer_strategy_trace: AnswerStrategyTrace | None = None,
    objective_trace: ObjectiveFrameTrace | None = None,
    decomposition_trace: DecompositionTrace | None = None,
    evidence_trace: EvidencePackTrace | None = None,
    synthesis_trace: SynthesisTrace | None = None,
    claim_capture_trace: ClaimCaptureTrace | None = None,
    workframe_trace: WorkframeTrace | None = None,
    thread_weave_trace: ThreadWeaveTrace | None = None,
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
                "execution_message": clean_display_text(route.execution_message) if route.execution_message is not None else None,
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
                    "personal_entry_kind": interpret_trace.personal_entry_kind,
                    "owner_name": interpret_trace.owner_name,
                    "owner_relation": interpret_trace.owner_relation,
                    "declared_focus": interpret_trace.declared_focus,
                    "declared_direction": interpret_trace.declared_direction,
                    "memory_query": interpret_trace.memory_query,
                    "claim_capture_count": interpret_trace.claim_capture_count,
                    "relative_time_terms": interpret_trace.relative_time_terms,
                    "unit_count": interpret_trace.unit_count,
                    "selected_intent": interpret_trace.selected_intent,
                    "workframe_candidate_summary": interpret_trace.workframe_candidate_summary,
                    "thread_candidate_summary": interpret_trace.thread_candidate_summary,
                    "style_constraints_effective": interpret_trace.style_constraints_effective,
                    "uncertainty_flags": interpret_trace.uncertainty_flags,
                    "selected_reason": interpret_trace.selected_reason,
                    "rejected_reason": interpret_trace.rejected_reason,
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
                    "daypart": response_plan_trace.daypart,
                    "gap_kind": response_plan_trace.gap_kind,
                    "continuity_class": response_plan_trace.continuity_class,
                    "relative_grounding": response_plan_trace.relative_grounding,
                    "style_constraints": response_plan_trace.style_constraints,
                    "chat_lock_active": response_plan_trace.chat_lock_active,
                    "chat_lock_strength": response_plan_trace.chat_lock_strength,
                    "direct_answer_required": response_plan_trace.direct_answer_required,
                    "direct_answer_present": response_plan_trace.direct_answer_present,
                    "clarification_needed": response_plan_trace.clarification_needed,
                    "clarification_reason": response_plan_trace.clarification_reason,
                    "anti_hijack_guarded": response_plan_trace.anti_hijack_guarded,
                    "ack_collapse_risk": response_plan_trace.ack_collapse_risk,
                    "final_workframe": response_plan_trace.final_workframe,
                    "final_thread_arbitration": response_plan_trace.final_thread_arbitration,
                    "reply_shape": response_plan_trace.reply_shape,
                    "recap_source_turn_count": response_plan_trace.recap_source_turn_count,
                    "recap_included_turn_count": response_plan_trace.recap_included_turn_count,
                    "composition_recap_used": response_plan_trace.composition_recap_used,
                    "composition_next_step_used": response_plan_trace.composition_next_step_used,
                    "composition_reflective_lead_used": response_plan_trace.composition_reflective_lead_used,
                    "surface_hijack_guarded": response_plan_trace.surface_hijack_guarded,
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
                    "target_line": clean_display_text(followup_trace.target_line) if followup_trace.target_line is not None else None,
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



    if workframe_trace is not None:
        events.append(
            {
                "event_name": "workframe_state_derived",
                "payload": {
                    "workframe": workframe_trace.workframe,
                    "objective_status": workframe_trace.objective_status,
                    "objective_text": clean_display_text(workframe_trace.objective_text) if workframe_trace.objective_text else None,
                    "blocker_status": workframe_trace.blocker_status,
                    "blocker_text": clean_display_text(workframe_trace.blocker_text) if workframe_trace.blocker_text else None,
                    "next_step_status": workframe_trace.next_step_status,
                    "next_step_line_count": workframe_trace.next_step_line_count,
                    "missing_info_status": workframe_trace.missing_info_status,
                    "missing_info_count": workframe_trace.missing_info_count,
                    "open_question_status": workframe_trace.open_question_status,
                    "open_question_count": workframe_trace.open_question_count,
                    "assumption_status": workframe_trace.assumption_status,
                    "assumption_count": workframe_trace.assumption_count,
                    "decision_state": workframe_trace.decision_state,
                    "decision_count": workframe_trace.decision_count,
                    "evidence_gap_status": workframe_trace.evidence_gap_status,
                    "evidence_gap_count": workframe_trace.evidence_gap_count,
                    "query_family": workframe_trace.query_family,
                    "uncertainty_marked": workframe_trace.uncertainty_marked,
                },
            }
        )

    if thread_weave_trace is not None:
        events.append(
            {
                "event_name": "thread_weave_state_derived",
                "payload": {
                    "relation": thread_weave_trace.relation,
                    "main_thread_key": thread_weave_trace.main_thread_key,
                    "related_thread_key": thread_weave_trace.related_thread_key,
                    "detour_thread_key": thread_weave_trace.detour_thread_key,
                    "conclusion_status": thread_weave_trace.conclusion_status,
                    "conclusion_validity": thread_weave_trace.conclusion_validity,
                    "applicability_status": thread_weave_trace.applicability_status,
                    "temporary_state_lifecycle": thread_weave_trace.temporary_state_lifecycle,
                    "thread_lifecycle": thread_weave_trace.thread_lifecycle,
                    "query_family": thread_weave_trace.query_family,
                },
            }
        )

    if claim_capture_trace is not None and claim_capture_trace.captured:
        events.append(
            {
                "event_name": "explicit_claims_captured",
                "payload": {
                    "captured": claim_capture_trace.captured,
                    "items": claim_capture_trace.items,
                    "stable_count": claim_capture_trace.stable_count,
                    "temporary_count": claim_capture_trace.temporary_count,
                    "strengthened_count": claim_capture_trace.strengthened_count,
                },
            }
        )

    if comparison_trace is not None and comparison_trace.built:
        events.append(
            {
                "event_name": "comparison_pack_built",
                "payload": {
                    "candidate_count": comparison_trace.candidate_count,
                    "candidate_kinds": comparison_trace.candidate_kinds,
                    "winner_kind": comparison_trace.winner_kind,
                    "winner_score": comparison_trace.winner_score,
                },
            }
        )

    if answer_strategy_trace is not None:
        events.append(
            {
                "event_name": "answer_strategy_selected",
                "payload": {
                    "selected_strategy": answer_strategy_trace.selected_strategy,
                    "selected_candidate_kind": answer_strategy_trace.selected_candidate_kind,
                    "confidence": answer_strategy_trace.confidence,
                    "clarification_planned": answer_strategy_trace.clarification_planned,
                    "clarification_cause": answer_strategy_trace.clarification_cause,
                },
            }
        )

    if objective_trace is not None:
        events.append(
            {
                "event_name": "objective_framed",
                "payload": {
                    "kind": objective_trace.kind,
                    "is_multi_part": objective_trace.is_multi_part,
                    "secondary_kinds": objective_trace.secondary_kinds,
                },
            }
        )

    if decomposition_trace is not None:
        events.append(
            {
                "event_name": "decomposition_built",
                "payload": {
                    "unit_count": decomposition_trace.unit_count,
                    "unit_kinds": decomposition_trace.unit_kinds,
                },
            }
        )

    if evidence_trace is not None:
        events.append(
            {
                "event_name": "evidence_pack_built",
                "payload": {
                    "item_count": evidence_trace.item_count,
                    "support_distribution": evidence_trace.support_distribution,
                    "ingest_status": evidence_trace.ingest_status,
                    "chunk_count": evidence_trace.chunk_count,
                    "key_line_count": evidence_trace.key_line_count,
                    "artifact_ids": evidence_trace.artifact_ids,
                },
            }
        )

    if synthesis_trace is not None:
        events.append(
            {
                "event_name": "synthesis_plan_built",
                "payload": {
                    "section_count": synthesis_trace.section_count,
                    "section_keys": synthesis_trace.section_keys,
                    "partial": synthesis_trace.partial,
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
        events.append({"event_name": "pending_route_confirmed", "payload": {"executed_message": clean_display_text(route.execution_message) if route.execution_message is not None else None}})
    elif route.pending_resolution.value == "rejected":
        events.append({"event_name": "pending_route_rejected", "payload": {"executed_message": route.execution_message}})
    elif route.pending_resolution.value == "cancelled":
        events.append({"event_name": "pending_route_cancelled", "payload": {"new_message": turn.user_message}})

    return events
