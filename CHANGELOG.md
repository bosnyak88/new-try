# Changelog

## Unreleased
- REBUILD-031: fixed Windows/PowerShell live stdin mojibake boundary with deterministic byte-decoding + reversible repair so Hungarian prompts preserve semantic fidelity in `talk --live`.
- REBUILD-031: added `live_input_repaired` trace accounting for repaired/degraded ingress and restored once/live self-intro parity on repaired live input flows.
- REBUILD-030: fixed Windows live output boundary with console-safe rendering fallback so `talk --live` no longer crashes on unencodable Unicode in constrained codepages.
- REBUILD-030: fixed live input/persistence boundary by replacing invalid surrogate code points before turn persistence; prevents `surrogates not allowed` crashes.
- REBUILD-030: added bounded live failure accounting via `live_turn_failed` and output-sanitization audit via `live_output_sanitized`; updated `trace-last` to surface loop-level (`turn_id=0`) events when needed.
- REBUILD-029: stabilized `talk --live` response visibility so processed turns cannot silently render as blank output; added explicit degraded live-surface fallback + `live_surface_degraded` trace event.
- REBUILD-029: hardened llama-http reply extraction for structured/malformed payload variants and deterministic fallback on empty content.
- REBUILD-029: added deterministic regressions for live visibility, degraded handling, greeting first-turn stability, and once/live parity spot-check.
- REBUILD-028: fixed maintenance-route hijack where explicit maintenance/blocker turns containing time references ("most/ma") could fall back to generic clarification.
- REBUILD-028: added blocker replacement parsing (old blocker resolved + new blocker remains), and completed applicability/conclusion query handling for the Scenario-A maintenance flow.
- REBUILD-028: added focused regressions for maintenance update routing, blocker persistence/replacement, and state/trace/snapshot alignment.
- REBUILD-027: deterministic maintenance baseline for memory/thread/conclusion lifecycle with explicit applicability gate propagation.
- Added lifecycle semantics to `ThreadWeaveState` (temporary-state lifecycle, thread lifecycle, conclusion validity) and aligned response/persistence/trace behavior.
- Added deterministic regressions for memory maintenance, thread lifecycle cues (park/return/close), and applicability gate behavior.
- REBUILD-026 follow-up: raw multiline evidence turn now acknowledges ingest explicitly, and evidence query family returns grounded non-filler answers (error/inference/important-part/blocker/recall).
- REBUILD-026 follow-up: added deterministic CLI multiline ingress path (`talk --once-file`, `talk --once-stdin`) and removed evidence-query filler fallback when no evidence is ingested.

- REBUILD-025: deterministic thread-weave baseline (main/side/detour/return/unrelated/unknown) with conclusion + applicability semantics.
- Added persisted `thread_weave_state` propagation to snapshot/focus (schema v7 migration).
- Added `thread_weave_state_derived` trace event and Hungarian response-surface handling for relation/conclusion/applicability queries.
- Added regression tests and docs synchronization for post-025 baseline.
- REBUILD-025 follow-up: fixed in-thread detour/return-to-main capture and removed `unrelated_thread` mismatch for main/side relation answers in the canonical rebuild-025 scenario.

- REBUILD-022: full-system personal cognitive baseline propagation pass.
- Added explicit memory-query semantics for inferred/temporary-vs-certain answers.
- Extended trace capture payload with stable/temporary/strengthened counters.
- Updated docs and propagation report to post-022 authoritative semantics.

- REBUILD-021: full-system post-020 architecture sync/propagation audit.
- Synchronized architecture/bootstrap/operations/README docs to the authoritative post-020 runtime model.
- Removed stale doc semantics (schema-v2 framing, app_meta-only owner-memory claim, partial command/trace framing).
- Added explicit propagation report for REBUILD-021 with changed vs intentionally unchanged layer accounting.
- Hardened regression expectations for persistence schema truth by asserting `personal_claims` table presence in bootstrap test.
- REBUILD-021 follow-up: removed orchestration package eager re-exports to break persistence/orchestration import cycle during isolated persistence test loading.
- Added import-boundary regressions for persistence-first and orchestration-first import orders (`tests/test_import_boundaries.py`).

## 0.9.0 - REBUILD-020 deterministic scoped-state baseline

- Separated stable claims from temporary scoped state semantics.
- Added deterministic scoped-state lifecycle (`active`/`stale`/`expired`) behavior.
- Kept continuity/time shaping deterministic and trace-visible.

## 0.8.0 - REBUILD-019 controlled explicit personal memory

- Added explicit claim capture/query substrate with grounded answer behavior.

## 0.7.0 - REBUILD-018 deterministic time awareness

- Added clock/timezone-aware greeting and continuity shaping.

## 0.6.0 - REBUILD-017 owner-aware intake bridge

- Added deterministic intake-kind handling and personal-entry response shaping.

## 0.5.0 - REBUILD-016 personal-entry/owner-intro foundation

- Added deterministic greeting/self-intro/owner framing interpretation path.


## Unreleased
- REBUILD-031: fixed Windows/PowerShell live stdin mojibake boundary with deterministic byte-decoding + reversible repair so Hungarian prompts preserve semantic fidelity in `talk --live`.
- REBUILD-031: added `live_input_repaired` trace accounting for repaired/degraded ingress and restored once/live self-intro parity on repaired live input flows.
- REBUILD-030: fixed Windows live output boundary with console-safe rendering fallback so `talk --live` no longer crashes on unencodable Unicode in constrained codepages.
- REBUILD-030: fixed live input/persistence boundary by replacing invalid surrogate code points before turn persistence; prevents `surrogates not allowed` crashes.
- REBUILD-030: added bounded live failure accounting via `live_turn_failed` and output-sanitization audit via `live_output_sanitized`; updated `trace-last` to surface loop-level (`turn_id=0`) events when needed.
- REBUILD-029: stabilized `talk --live` response visibility so processed turns cannot silently render as blank output; added explicit degraded live-surface fallback + `live_surface_degraded` trace event.
- REBUILD-029: hardened llama-http reply extraction for structured/malformed payload variants and deterministic fallback on empty content.
- REBUILD-029: added deterministic regressions for live visibility, degraded handling, greeting first-turn stability, and once/live parity spot-check.
- REBUILD-028: fixed maintenance-route hijack where explicit maintenance/blocker turns containing time references ("most/ma") could fall back to generic clarification.
- REBUILD-028: added blocker replacement parsing (old blocker resolved + new blocker remains), and completed applicability/conclusion query handling for the Scenario-A maintenance flow.
- REBUILD-028: added focused regressions for maintenance update routing, blocker persistence/replacement, and state/trace/snapshot alignment.
- REBUILD-027: deterministic maintenance baseline for memory/thread/conclusion lifecycle with explicit applicability gate propagation.
- Added lifecycle semantics to `ThreadWeaveState` (temporary-state lifecycle, thread lifecycle, conclusion validity) and aligned response/persistence/trace behavior.
- Added deterministic regressions for memory maintenance, thread lifecycle cues (park/return/close), and applicability gate behavior.
- REBUILD-026 follow-up: raw multiline evidence turn now acknowledges ingest explicitly, and evidence query family returns grounded non-filler answers (error/inference/important-part/blocker/recall).
- Added deterministic REBUILD-023 workframe baseline (mode/objective/blocker/next-step derivation) with trace visibility via `workframe_state_derived`.

- REBUILD-023 follow-up: separated explicit blocker declaration from hedged blocker/next-step/objective proposal semantics; certainty-split responses now keep tentative inputs out of certain facts, with aligned trace uncertainty flags.
- Added REBUILD-024 deterministic decision-readiness baseline: missing-info/open-question/assumption/decision/evidence-gap statuses in `WorkframeState`, response planning, and trace payloads.
- Added regression tests for Hungarian missing-info/open-question/decision/evidence queries and trace payload integrity.
- Updated README/architecture/bootstrap/operations/propagation docs for post-024 semantics and confirmed schema stays at v6 for this pass.

- REBUILD-024 follow-up: fixed explicit blocker declaration routing, prevented meta state-queries from self-materializing into open-question state, added explicit evidence-gap query matching (`mihez nincs még elég bizonyíték?`), and stopped premature `decision_made` promotion for decision-status questions.

- REBUILD-026: deterministic large-text evidence-ingest baseline with chunking, key-line extraction, source-grounded response sections, and unresolved-evidence separation.
- Added evidence-ingest config knobs (`evidence_chunk_line_limit`, `evidence_max_chunks`, `evidence_summary_line_limit`) and trace payload enrichment (`ingest_status`, `chunk_count`, `key_line_count`).
- Added regressions for large-text ingest extraction and follow-up source-grounded recall without repasting full logs.
