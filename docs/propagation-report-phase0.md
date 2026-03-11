# Propagation report — REBUILD-002 talk vertical slice

## Direct changes

- Added persistence layer (`src/syntaris/persistence`) with explicit SQLite schema for `app_meta`, `sessions`, `turns`, `trace_events`.
- Extended contracts with app path/reply/session/turn/trace structures.
- Added reply adapter boundary (`src/syntaris/reply`) with deterministic fallback and optional llama-http adapter.
- Added orchestration flows for `init-db`, `talk --once`, and `trace-last`.
- Expanded CLI surface without moving business logic into `cli.py`.

## Propagated layers

- Contracts: new dataclasses ensure runtime/session/turn/trace are not ad-hoc dicts.
- Config: added `paths` and `reply` sections with env override support.
- Bootstrap: remains side-effect-free (`.env` loading still CLI boundary only).
- Persistence: schema bootstrap + read/write APIs are isolated in store module.
- Reply: backend selection and degraded behavior centralized behind adapter factory.
- Orchestration: command-level flows composed from contracts + persistence + reply + trace.
- Trace: turn-level events persisted and queryable via `trace-last`.
- Docs/config/examples: updated to match runtime/CLI behavior.
- Tests: added deterministic persistence/reply/CLI talk coverage.

## Structural self-check

- No giant central pipeline file introduced.
- SQLite logic is not in config loader or CLI.
- Reply HTTP logic is not scattered; it exists only inside reply adapter module.
- `.env` behavior boundary from previous phase is preserved.

## Deferred intentionally

- multi-turn session continuation UX
- memory/recall graph tables
- advanced routing and prompt systems
