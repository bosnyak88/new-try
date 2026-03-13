# Operations baseline (post-020)

## Core checks

- `doctor`: validates external llama path/port assumptions.
- `init-db`: initializes schema/migrations.
- `trace-last`: inspect latest persisted turn + event trail.

## Shared talk execution modes

- `talk --once "..."`
- `talk --live`
- `talk --script <path>`

All three use the same orchestration path (`execute_turn`).

## Thread/context tools

- `session-status`
- `thread-list`
- `thread-view`
- `thread-recap`
- `thread-snapshot`
- `thread-focus`

## Routing and pending precedence

1. explicit flags (`--thread`, `--mode`)
2. live slash commands
3. pending-route resolution
4. deterministic routing phrases
5. recap/recall interpretation and strategy path
6. active-thread continuation

## Post-020 smoke probes

- Personal entry: `szia syntaris én Árpi vagyok`
- Owner-aware intake: `a mai fókusz a syntaris`
- Scoped-state query: `mi a mostani fókusz?`
- Stable-memory query: `ki vagyok?`, `mit tudsz rólam biztosan?`
- Continuity/recall: `hol tartottunk?`, `az előző szálon mi volt?`
- Compare/structured: `hasonlítsd össze a mostanit az előző szállal`

## Observability expectations

Use `trace-last` to confirm coherent event chain:
- `route_decision_computed`
- `turn_interpreted`
- `thread_focus_loaded`
- `comparison_pack_built`
- `answer_strategy_selected`
- `response_plan_built`
- `explicit_claims_captured` (only on capture turns)
