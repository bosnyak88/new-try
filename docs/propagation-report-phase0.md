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
