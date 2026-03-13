# Propagation report — REBUILD-021 architecture sync / propagation audit

## Audit scope executed

Full review across:
- contracts
- orchestration
- persistence/schema/store
- reply/renderer boundary
- trace semantics
- CLI boundary
- config loader + example config
- docs/changelog
- regression tests

## Layers changed

- Documentation baseline synchronized to post-020 architecture:
  - `README.md`
  - `docs/architecture.md`
  - `docs/bootstrap.md`
  - `docs/operations.md`
  - `CHANGELOG.md`
- Regression hardening:
  - `tests/test_persistence.py` expanded schema assertions for post-020 memory model table presence.

## Layers reviewed and intentionally unchanged

- Contracts (`src/syntaris/contracts/runtime.py`): semantics already aligned with post-020 claims/scoped-state/time-context.
- Orchestration (`src/syntaris/orchestration/*.py`): shared turn path and post-020 behavior already coherent; no redesign required.
- Persistence implementation (`src/syntaris/persistence/store.py`): scoped-state lifecycle + stable claims behavior already aligned.
- Trace builder (`src/syntaris/trace/events.py`): event semantics already represent runtime decisions accurately.
- CLI boundary (`src/syntaris/cli.py`): remains thin and correctly delegates orchestration.
- Config loader/example (`src/syntaris/config/loader.py`, `config/syntaris.example.toml`): runtime options and defaults already aligned.

## Stale artifacts removed/updated

- Replaced stale stage-specific docs that still claimed pre-020 persistence semantics (`app_meta`-only owner memory, schema v2 framing, incomplete command surface).
- Removed drift from older architecture snapshots and normalized docs to one authoritative post-020 baseline.
- Cleaned changelog structure drift (duplicate/unordered unreleased sections) and added REBUILD-021 audit entry.

## Propagation gaps found and fixed

1. **Bootstrap docs drift**: schema version and table truth was stale -> fixed to schema v6 and actual table model.
2. **Memory persistence docs drift**: old `app_meta` owner-memory wording remained -> fixed to explicit `personal_claims` model.
3. **Operations/docs command drift**: docs incompletely reflected current snapshot/focus tools and post-020 smoke probes -> fixed.

## Authoritative post-020 baseline (confirmed)

- Stable explicit claims and temporary scoped-state are distinct concepts with deterministic lifecycle.
- Continuity-aware time shaping is deterministic and trace-visible.
- Snapshot/focus/recall/compare remain on shared orchestration with persistence-backed coherence.
- Deterministic offline fallback remains valid.
- No architecture redesign was introduced.

## Explicitly deferred non-goals

- Executor/tool workflows
- Reminder/task engine
- Broad profile graph / BioGraph
- Autonomous long-term inferred personal ontology

## REBUILD-021 follow-up (import-boundary cleanup)

- Root cause: `persistence.store` imported `syntaris.orchestration.text_normalize`, which triggers `syntaris.orchestration` package import first.
- Previous `orchestration/__init__.py` eagerly imported `talk` module, which imports modules that import `syntaris.persistence` package, causing `PersistenceStore` lookup from partially initialized package.
- Boundary fix: made `orchestration/__init__.py` side-effect free (no eager re-export chain).
- Added deterministic regression tests to verify isolated and cross-order imports for persistence/orchestration modules.
- No user-facing runtime behavior was intentionally changed.
