# Architecture (post-REBUILD-022 authoritative baseline)

## Design doctrine
- Contract-first, layer-separated.
- One shared turn orchestration path for once/live/script.
- Hungarian-first deterministic behavior remains primary.
- Deterministic fallback must work without live LLM.

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
- orchestration derives state once (`workframe_state.py`),
- response plan surfaces it in Hungarian-first structured wording,
- snapshots/focus carry aligned workframe state,
- trace `workframe_state_derived` includes each status plus count fields.
- state-query prompts are inspection-only and do not self-materialize as persistent open-question content.

Schema impact: none in this phase (SQLite schema remains v6) because this layer is deterministic derivation from turn context, not a new persisted table.


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
