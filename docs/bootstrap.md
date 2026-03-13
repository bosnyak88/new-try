# Bootstrap and configuration (post-022)

- `build_runtime()` builds `RuntimeContext` from config.
- `init-db` applies schema + migrations and stores schema version.
- Deterministic mode requires no live LLM server.

## Relevant knobs
- `[conversation].scoped_state_short_stale_minutes`
- `[conversation].scoped_state_same_day_stale_minutes`
- `[time].timezone`

These control temporary-state lifecycle and continuity classification.


## Deterministic fallback and workframe
Bootstrap remains deterministic-first. Workframe derivation does not require a live LLM endpoint, and trace exposes `workframe_state_derived` in fallback mode as well.
