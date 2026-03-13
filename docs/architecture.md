# Architecture (post-REBUILD-022 authoritative baseline)

## Design doctrine
- Contract-first, layer-separated.
- One shared turn orchestration path for once/live/script.
- Hungarian-first deterministic behavior remains primary.
- Deterministic fallback must work without live LLM.

## Layer map
1. `contracts/runtime.py`: DTOs for interpretation, memory semantics, continuity, focus/snapshot/recall, trace.
2. `orchestration/`: shared deterministic execution path (`turns.py`).
3. `persistence/`: SQLite schema v6 and store logic.
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
