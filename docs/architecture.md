# Architecture (post-REBUILD-020 authoritative baseline)

## Design doctrine

- Contract-first and layer-separated.
- One shared turn orchestration path for once/live/script.
- Hungarian-first deterministic behavior remains primary.
- Deterministic fallback must work without live LLM.
- No monolithic central brain file and no CLI orchestration smearing.

## Layer map

1. **Contracts** (`src/syntaris/contracts/runtime.py`)
   - Runtime DTOs for routing, interpretation, memory queries, claim capture, scoped-state status, time context, response planning, and trace views.
2. **Orchestration** (`src/syntaris/orchestration/`)
   - `turns.py` executes the shared pipeline: route -> context/focus/snapshot/recall -> interpretation -> strategy/reasoning scaffold -> response plan -> render/persist/trace.
3. **Persistence** (`src/syntaris/persistence/`)
   - Schema v6 with `sessions`, `threads`, `turns`, `thread_snapshots`, `thread_focus`, `personal_claims`, `trace_events`, `app_meta`.
4. **Reply** (`src/syntaris/reply/`)
   - Adapter boundary plus deterministic plan renderer.
5. **Trace** (`src/syntaris/trace/events.py`)
   - Event stream reflecting route decision, interpretation, strategy, continuity, and capture actions.
6. **CLI** (`src/syntaris/cli.py`)
   - Thin command boundary; no business logic.

## Personal-memory semantics

- Stable claims are persisted as explicit captures only.
- Scoped state is persisted in the same `personal_claims` table with scope tags (`day`, `session`, `thread`).
- Read path classifies scoped entries into `active/stale/expired` deterministically from timestamps/day boundary.
- Corrections supersede older active values by claim kind + scope domain.

## Time and continuity semantics

- `RuntimeContext.clock` and `[time].timezone` are authoritative.
- Continuity metadata (`gap_kind`, `continuity_class`, relative grounding) is computed in orchestration and surfaced in `response_plan_built` trace payloads.

## Trace contract intent

Trace events are operationally honest and mapped to runtime decisions:
- `route_decision_computed`: routing + state transition + pending resolution metadata.
- `turn_interpreted`: interpretation kind, personal-entry/intake markers, memory query, claim-capture count, relative terms.
- `response_plan_built`: final response kind plus time/continuity shaping metadata.
- `explicit_claims_captured`: only emitted when actual captures persisted.
- `thread_snapshot_refreshed` / `thread_focus_loaded`: artifact coherence visibility.

## Explicit non-goals

- executor/tool orchestration,
- routine learning,
- broad inferred profile graph,
- hidden CoT exposure.
