# Syntaris (Greenfield Rebuild)

Phase-0 runtime foundation with a minimal end-to-end talk vertical slice.

## Quick start

1. Copy environment template:
   - `cp .env.example .env`
2. Install in editable mode:
   - `python -m pip install -e .[dev]`
3. Initialize local DB:
   - `python -m syntaris.cli --config config/syntaris.example.toml init-db`
4. Run one talk turn:
   - `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia"`
5. Inspect latest persisted trace:
   - `python -m syntaris.cli --config config/syntaris.example.toml trace-last`

## Repository map

- `src/syntaris/contracts` — runtime/session/turn/trace contracts.
- `src/syntaris/config` — TOML + env precedence config loading.
- `src/syntaris/bootstrap` — side-effect-free runtime composition.
- `src/syntaris/persistence` — SQLite schema bootstrap and read/write API.
- `src/syntaris/reply` — reply adapter boundary and fallback backend.
- `src/syntaris/orchestration` — command orchestration (`doctor`, `init-db`, `talk`, `trace-last`).
- `src/syntaris/trace` — trace projection for boot + talk flows.
- `docs/` — architecture, bootstrap, operations, propagation reporting.
- `tests/` — modular tests for config, bootstrap, persistence, reply, and CLI flows.
