# Propagation report — REBUILD-022 personal cognitive baseline propagation

## Scope
Contracts, orchestration, persistence semantics, reply surface, trace semantics, CLI smoke paths, config comments, tests, and top-level docs were reviewed.

## Changed
- contracts: memory-query and claim-capture trace extensions.
- orchestration: Hungarian memory-query interpretation extensions and response-surface certainty split.
- turns+trace: explicit capture counters (`stable_count`, `temporary_count`, `strengthened_count`).
- tests: regression coverage for new memory queries and trace payload semantics.
- docs/changelog/config comments synchronized to post-022 semantics.

## Reviewed intentionally unchanged
- schema/storage shape stayed on v6 (`personal_claims` already supports stable + scoped-state semantics).
- routing/recall/snapshot/focus orchestration modules remained coherent with current semantics.
- CLI remained thin (no orchestration migration into CLI).

## Removed
- none.

## Deferred (explicit non-goals)
- executor/tool workflows,
- BioGraph/profile graph,
- architecture redesign.


## REBUILD-023 propagation note
Reviewed core contracts/orchestration/reply/trace/CLI/tests/docs for workframe, objective, blocker, and next-step alignment. Added deterministic workframe derivation and trace event; no schema migration required in this pass.

## REBUILD-024 propagation note
Reviewed and propagated contracts/orchestration/reply/trace/tests/docs/config for missing-info, open-question, assumption/evidence, and decision-needed semantics. No schema migration was required; persistence remains context-first while snapshot/focus keep aligned derived workframe state.


## REBUILD-024 follow-up correction note
Narrow semantic correction pass: explicit blocker declaration now stays on blocker-update path, meta state-queries are inspection-only (no open-question writeback from query text), evidence-gap question family includes `mihez nincs még elég bizonyíték?`, and decision-status questions no longer force `decision_made` without grounded resolution. Snapshot/focus/trace now retain grounded state without meta-query pollution.


## REBUILD-025 propagation note
Full-system propagation pass completed for deterministic thread-weave/conclusion/applicability baseline.
- contracts: added authoritative relation/conclusion/applicability enums + `ThreadWeaveState` + `ThreadWeaveTrace`.
- orchestration: added `thread_weave.py` derivation and query-family detection; integrated into turns/response planning/snapshot/focus.
- persistence/schema: schema v7, added `thread_weave_json` columns and migration/read-write support in store.
- trace: added `thread_weave_state_derived` event.
- CLI: thread-snapshot/thread-focus JSON surfaces now include thread-weave payload.
- tests: added deterministic regressions for relation/conclusion/applicability answers, trace integrity, and snapshot/focus alignment.
- docs/config/changelog: synchronized to post-025 semantics.


## REBUILD-025 follow-up correction note
Narrow semantic correction pass on the same PR: detour declaration and return-to-main declaration are now explicitly captured as thread-weave updates, and relation/conclusion/applicability answers are derived from retained weave state (not generic fallback). Direct answers are aligned with snapshot/focus/trace (`thread_weave_state_derived`) for the in-thread main-vs-detour scenario.


## REBUILD-026 propagation note
- follow-up correction: raw evidence turn now emits explicit ingest acknowledgement and evidence query family (`hiba/következtetés/fontos rész/blocker/recall`) no longer falls back to generic filler.
- CLI boundary: added explicit deterministic multiline ingest path (`talk --once-file`, `talk --once-stdin`) and tests.
- response surface: evidence-query family now emits explicit no-evidence guidance when ingest state is absent (no generic filler).
Full-system propagation pass completed for deterministic large-text evidence ingest + source-grounding baseline.
- contracts/config: new evidence ingest/chunk/grounding DTOs and config knobs
- orchestration: evidence ingest reducer + evidence-pack integration + follow-up evidence reuse
- response/reply: source-grounded vs inferred/unresolved separation in answer surface
- trace: ingest/chunk/key-line visibility in `evidence_pack_built`
- tests: deterministic regressions for ingest extraction and follow-up grounded reuse
- docs/config/changelog: synchronized to post-026 semantics

Schema migration: not required in this phase (v7 unchanged).
