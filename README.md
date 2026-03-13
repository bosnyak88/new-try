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
