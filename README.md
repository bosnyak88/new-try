# Syntaris (post-REBUILD-020 baseline)

Syntaris is an offline, Hungarian-first personal cognitive companion for a **single owner**.  
The runtime is deterministic by default and remains usable without a live LLM server.

## Authoritative architecture shape

- **Contracts-first runtime** (`contracts/runtime.py`): explicit turn interpretation, routing, memory, scoped-state, time-context, and trace DTOs.
- **Shared orchestration path** (`orchestration/turns.py`): once/live/script all execute the same deterministic turn flow.
- **Persistence** (`persistence/store.py`, `persistence/schema.py`): SQLite for sessions, threads, turns, snapshots, focus packs, explicit claims, and trace events.
- **Reply boundary** (`reply/`): deterministic renderer + optional `llama-http` adapter.
- **Trace boundary** (`trace/events.py`): persisted inspectable events for route/interpretation/strategy/response-plan/time continuity.
- **CLI boundary** (`cli.py`): command routing only; no orchestration logic leakage.

## Stable behavior baseline

### 1) Identity and memory model
- Stable explicit claims: `owner_name`, `owner_relation`, `system_role`.
- Temporary scoped state:
  - day scope (`current_focus`)
  - session scope (`current_direction` from day-intent)
  - thread scope (`current_direction` from topic-intent)
- Scoped state lifecycle is deterministic: `active`, `stale`, `expired`.

### 2) Time awareness and continuity
- Runtime uses explicit clock + timezone.
- Greeting/daypart and continuity wording are deterministic from persisted timestamps.
- No fake surveillance or unstored-memory claims.

### 3) Owner-aware intake and personal-entry
- Deterministic Hungarian-first recognition for greeting/self-intro/owner framing/return-entry/intake patterns.
- Capture applies only to explicit user-provided facts.

### 4) Recall/snapshot/focus coherence
- Snapshot and focus are persisted deterministic artifacts.
- Retrieval paths enforce freshness + hygiene rebuild/writeback.
- Recall/compare/structured planning uses these artifacts through shared orchestration.

## Quick start

1. `python -m pip install -e .`
2. `python -m syntaris.cli --config config/syntaris.example.toml init-db`
3. `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia syntaris én Árpi vagyok"`
4. `python -m syntaris.cli --config config/syntaris.example.toml trace-last`

## Commands

- `doctor`
- `trace-boot`
- `init-db`
- `talk --once "..." [--thread <thread_key>] [--mode <mode>]`
- `talk --live`
- `talk --script <path>`
- `session-status`
- `thread-list`
- `thread-view [--current|--previous|<thread_key>] [--limit N]`
- `thread-recap [--current|--previous|<thread_key>] [--limit N]`
- `thread-snapshot [--current|--previous|<thread_key>] [--refresh] [--limit N]`
- `thread-focus [--current|--previous|<thread_key>] [--refresh] [--limit N]`
- `trace-last`

## Scope guardrails

Current baseline intentionally does **not** include:
- autonomous executor/tool-calling workflows,
- reminder/task engine,
- broad profile graph (BioGraph),
- inferred long-term personal ontology from implicit signals.
