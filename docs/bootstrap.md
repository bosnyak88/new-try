# Bootstrap and configuration (post-022)

- `build_runtime()` builds `RuntimeContext` from config.
- `init-db` applies schema + migrations and stores schema version.
- Deterministic mode requires no live LLM server.

## Relevant knobs
- `[conversation].scoped_state_short_stale_minutes`
- `[conversation].scoped_state_same_day_stale_minutes`
- `[time].timezone`

These control temporary-state lifecycle and continuity classification.
