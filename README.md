# Syntaris (post-REBUILD-022 baseline)

Syntaris is an offline, Hungarian-first personal cognitive companion for a **single owner**.
The runtime is deterministic by default and remains usable without a live LLM server.

## Authoritative baseline

- Owner identity and relationship are explicit (`owner_name`, `owner_relation`, `system_role`).
- Memory semantics are explicit and conservative:
  - stable explicit claims,
  - temporary scoped state (`day`/`session`/`thread`) with `active/stale/expired`,
  - no hidden long-term profile inference.
- Natural Hungarian teaching phrases work without command syntax.
- Continuity (`hol tartottunk?`), recall, compare, snapshot, and focus all run through the same deterministic orchestration.
- Trace remains honest: interpretation, memory capture, uncertainty-oriented planning, and continuity metadata are persisted.

## Quick start

1. `python -m pip install -e .`
2. `python -m syntaris.cli --config config/syntaris.example.toml init-db`
3. `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia syntaris én Árpi vagyok"`
4. `python -m syntaris.cli --config config/syntaris.example.toml trace-last`

## Scope guardrails

Current baseline intentionally does **not** include:
- autonomous executor/tool-calling workflows,
- reminder/task engine,
- broad profile graph (BioGraph),
- overcapturing implicit personal ontology from one casual sentence.


## REBUILD-023 baseline
- Runtime derives a deterministic **workframe state** (chat/work/planning/recall/capture) from natural Hungarian turns.
- Answers about blocker/next-step/plan now surface objective state, blocker state, and next-step uncertainty explicitly.
- Trace now includes `workframe_state_derived` for honest post-turn audit.

## REBUILD-024 baseline
- Workframe now carries an explicit decision-readiness layer: `missing_info`, `open_question`, `assumption`, `decision_state`, `evidence_gap`.
- Natural Hungarian queries like `mi hiányzik még?`, `milyen nyitott kérdések vannak?`, `milyen döntést kell meghozni?` map to deterministic structured answers.
- `workframe_state_derived` trace payload includes all decision-readiness statuses and counts, so uncertainty and readiness are auditable instead of hidden in wording.


## REBUILD-025 baseline
- Added an explicit deterministic thread-weave model: `main_thread`, `side_thread`, `detour`, `return_to_main`, `unrelated_thread`, `relation_unknown`.
- Added deterministic conclusion semantics: `explicit_conclusion`, `derived_conclusion`, `tentative_conclusion`, `superseded_conclusion`, `no_conclusion_established`.
- Added deterministic carry-forward applicability semantics: `applicable_now`, `partially_applicable`, `not_applicable_now`, `applicability_uncertain`, `superseded_by_new_context`.
- Snapshot/focus/trace now carry aligned thread-weave state, and `trace-last` includes `thread_weave_state_derived`.
- Detour (`kitértünk ...`) and return-to-main (`a főszál továbbra is ...`) declarations are captured as retained thread-weave updates, and direct relation answers align with snapshot/focus/trace state.
