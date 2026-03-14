# Architecture (post-REBUILD-022 authoritative baseline)

## Design doctrine
- Contract-first, layer-separated.
- One shared turn orchestration path for once/live/script.
- Hungarian-first deterministic behavior remains primary.
- Deterministic fallback must work without live LLM.
- Live response surface must be visibility-safe: processed turns cannot silently render as blank output.

## Layer map
1. `contracts/runtime.py`: DTOs for interpretation, memory semantics, continuity, focus/snapshot/recall, trace.
2. `orchestration/`: shared deterministic execution path (`turns.py`).
3. `persistence/`: SQLite schema v7 and store logic.
4. `reply/`: plan rendering + adapter boundary.
5. `trace/events.py`: persisted event stream.
6. `cli.py`: thin boundary.

## Memory semantics model
- **Stable explicit claim**: explicit user declaration persisted in `personal_claims` with `stable` scope.
- **Temporary scoped state**: `day`/`session`/`thread` scope with deterministic status (`active`, `stale`, `expired`).
- **Candidate / inferred / unknown**: surfaced conservatively in response semantics; system does not pretend inferred profile certainty.
- **Strengthened claim**: trace marks repeated stable captures as strengthened when same value re-confirmed.

## Trace semantics
- `turn_interpreted`: includes personal-entry kind, memory query, relative-time terms.
- `explicit_claims_captured`: includes items plus stable/temporary/strengthened counters.
- `response_plan_built`: includes response kind and continuity metadata.


## Post-023 workframe model
The authoritative model is `WorkframeState` with:
- workframe kind
- objective status/text
- blocker status/text
- next-step status/lines

This model is derived in orchestration and propagated to response planning and trace.

- Workframe update signals now distinguish explicit blocker declaration vs hedged blocker/objective/next-step proposals to keep state-write certainty discipline consistent with response and trace layers.

## Post-024 decision-readiness model
`WorkframeState` is extended (no new central orchestrator file) with explicit deterministic statuses:
- missing info: `missing_info_explicit` / `missing_info_implied` / `no_missing_info_established` / `missing_info_resolved`
- open question: `explicit_open_question` / `implied_open_question` / `answered_question` / `no_open_question_established`
- assumption support level: `assumption` / `inferred_possibility` / `supported_claim` / `unknown_or_not_established`
- decision state: `decision_needed` / `decision_blocked_by_missing_info` / `decision_proposed` / `decision_made` / `no_decision_established`
- evidence gap: `evidence_gap_explicit` / `evidence_gap_implied` / `evidence_sufficient` / `evidence_unknown`

Propagation shape:
- CLI boundary provides deterministic multiline evidence ingress (`--once-file` / `--once-stdin`) so ingest semantics are testable without shell-quoting ambiguity
- orchestration derives state once (`workframe_state.py`),
- response plan surfaces it in Hungarian-first structured wording,
- snapshots/focus carry aligned workframe state,
- trace `workframe_state_derived` includes each status plus count fields.
- state-query prompts are inspection-only and do not self-materialize as persistent open-question content.

Schema impact: none in that phase (SQLite schema remained v6 at REBUILD-024).


## Post-025 thread-weave + conclusion applicability model
Authoritative deterministic model (`ThreadWeaveState`) now propagates across contracts/orchestration/persistence/reply/trace:
- thread relation: `main_thread`, `side_thread`, `detour`, `return_to_main`, `unrelated_thread`, `relation_unknown`
- conclusion status: `explicit_conclusion`, `derived_conclusion`, `tentative_conclusion`, `superseded_conclusion`, `no_conclusion_established`
- applicability status: `applicable_now`, `partially_applicable`, `not_applicable_now`, `applicability_uncertain`, `superseded_by_new_context`

Propagation shape:
- orchestration derives once from semantic context (`thread_weave.py`),
- response surface answers Hungarian thread/conclusion/applicability queries from the same state,
- snapshot/focus persist aligned `thread_weave_state`,
- trace emits `thread_weave_state_derived` for auditability.

Schema impact: minimal, SQLite schema moved to v7 with `thread_weave_json` columns on `thread_snapshots` and `thread_focus` for persisted derived-state alignment.


## Post-026 evidence-ingest baseline
Authoritative deterministic model is now explicit and shared across contracts/orchestration/reply/trace:
- ingest status: `raw_text_evidence` | `no_evidence_ingested`
- chunking semantics: `kept_chunk` vs `dropped_noise`
- extracted key lines + summary + source references + unresolved evidence
- grounding labels on evidence items (`directly_supported_by_source`..`source_not_available`)

Propagation shape:
- `orchestration/evidence_ingest.py` performs chunk/reduction/extraction from large raw text
- `orchestration/turns.py` wires ingest into evidence pack and reuses prior large evidence for follow-up turns
- `answer_synthesis` and response planning keep direct source lines separated from inferred/unresolved lines
- trace `evidence_pack_built` includes ingest/chunk/key-line counters

Schema impact: **none** for REBUILD-026 (schema remains v7).


## Post-027 maintenance/applicability baseline
Authoritative deterministic maintenance model extends `ThreadWeaveState` with lifecycle semantics:
- temporary-state lifecycle: `currently_active_temporary_state`, `aging_or_stale_temporary_state`, `resolved_temporary_state`, `superseded_temporary_state`, `archived_inactive_state`
- thread lifecycle: `active`, `parked`, `abandoned`, `closed`, `reopenable`
- conclusion validity: `still_valid`, `partially_valid`, `no_longer_valid_in_current_context`, `superseded_by_newer_context`, `historical_reminder_value_only`

Propagation shape:
- orchestration derives lifecycle/applicability once (`thread_weave.py`)
- response layer surfaces active vs historical vs superseded distinctions
- persistence serializes/deserializes the additional `ThreadWeaveState` fields
- trace `thread_weave_state_derived` carries lifecycle/validity payloads for honest auditability

Schema impact: none for REBUILD-027 (v7 unchanged).


## REBUILD-029 live visibility note
- Live-loop output remains a thin boundary above shared turn execution, but applies a visibility guard for empty replies and records `live_surface_degraded` trace when guardrails are used.
- No cognition logic moved into `cli.py`; routing/state/trace boundaries remain unchanged.


## REBUILD-030 live boundary doctrine
- CLI remains a thin boundary, but it now enforces a console-safe rendering boundary for live output and records `live_output_sanitized` trace when codepage degradation is applied.
- Persistence boundary now enforces surrogate-safe normalization before turn writes.
- Live loop now emits bounded `live_turn_failed` trace on pre-persist failures, instead of silent crash-only behavior.


## REBUILD-031 live ingress doctrine
- Live stdin ingress may decode from bytes using deterministic encoding candidates with bounded mojibake repair before turn execution.
- Input repair/degradation is trace-visible (`live_input_repaired`) to preserve audit honesty for semantic parity claims.
