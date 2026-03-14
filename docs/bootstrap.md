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
- Supported CLI ingest entrypoints for multiline raw evidence: `talk --once-file` and `talk --once-stdin`.
No new external service is required. Deterministic ingest/reduction is local and controlled by conversation config:
- `evidence_chunk_line_limit`
- `evidence_max_chunks`
- `evidence_summary_line_limit`

Fallback behavior remains valid without live LLM.


## REBUILD-027 bootstrap note
No new bootstrap command is required. Maintenance/applicability semantics are deterministic defaults in orchestration and require no additional runtime services. Existing scoped-state staleness knobs still apply; schema remains v7.


## REBUILD-029 live runtime note
- Bootstrap assumptions are unchanged: no extra service is required.
- Live-mode visibility now degrades explicitly when a processed turn yields empty text, while deterministic fallback remains valid without live LLM.


## REBUILD-030 live text boundary note
- Bootstrap services are unchanged.
- Runtime now includes deterministic surrogate-safe text normalization and console-safe live rendering fallback for constrained terminals.


## REBUILD-031 live ingress note
- Bootstrap services remain unchanged. Runtime now includes deterministic live stdin decode/repair boundary for Windows pipeline fidelity (HU-first).

## REBUILD-032 follow-up (manual live output visibility)
- Live loop now supports streaming output callbacks so manual interactive mode can emit each turn result immediately instead of end-of-loop batch printing.
- CLI live path now records output-stage honesty events (`reply_emit_attempted`, `reply_emitted_successfully`, `reply_emit_failed`) and keeps degraded sanitization audit (`live_output_sanitized`).
- No cognition relocation to CLI, no schema change, no maintenance/evidence architecture expansion in this follow-up.
