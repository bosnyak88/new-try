# Changelog

## Unreleased

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
- Added deterministic REBUILD-023 workframe baseline (mode/objective/blocker/next-step derivation) with trace visibility via `workframe_state_derived`.
