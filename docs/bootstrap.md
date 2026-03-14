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

## REBUILD-024 deterministic readiness bootstrap
No additional bootstrap service is required. Decision-readiness semantics are produced inside deterministic orchestration from turn context and remain available without live LLM.


## REBUILD-025 deterministic thread-weave bootstrap
No external bootstrap service was added. Thread-weave/conclusion/applicability semantics are deterministic and available without live LLM, including persisted snapshot/focus state and trace visibility.


## REBUILD-026 evidence-ingest bootstrap
No new external service is required. Deterministic ingest/reduction is local and controlled by conversation config:
- `evidence_chunk_line_limit`
- `evidence_max_chunks`
- `evidence_summary_line_limit`

Fallback behavior remains valid without live LLM.
