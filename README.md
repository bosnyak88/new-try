# Syntaris (Greenfield Rebuild)

Phase-0 runtime foundation with a minimal end-to-end talk vertical slice.

## Current scope

The current repository contains:

- a modular runtime foundation
- CLI-boundary `.env` autoload
- `doctor` and `trace-boot`
- SQLite bootstrap and persistence for sessions, turns, and trace events
- a reply adapter boundary with deterministic fallback behavior
- a minimal one-turn talk flow
- latest-trace inspection from CLI

## Quick start

1. Copy environment template:
   - `cp .env.example .env`
2. Install in editable mode:
   - `python -m pip install -e .`
3. Initialize local DB:
   - `python -m syntaris.cli --config config/syntaris.example.toml init-db`
4. Run one talk turn:
   - `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia"`
5. Inspect latest persisted trace:
   - `python -m syntaris.cli --config config/syntaris.example.toml trace-last`

## Repository map

- `src/syntaris/contracts` — runtime/session/turn/trace contracts and shared data structures.
- `src/syntaris/config` — TOML + env precedence config loading and TOML-safe string/path serialization helpers for generated config.
- `src/syntaris/bootstrap` — side-effect-free runtime composition and CLI-boundary bootstrapping.
- `src/syntaris/core` — leaf-level reusable domain utilities.
- `src/syntaris/persistence` — SQLite schema bootstrap and read/write API.
- `src/syntaris/reply` — reply adapter boundary and fallback/live backend selection.
- `src/syntaris/orchestration` — command orchestration (`doctor`, `init-db`, `talk`, `trace-last`).
- `src/syntaris/trace` — trace projection and event shaping for boot + talk flows.
- `docs/` — architecture, bootstrap, operations, and propagation reporting.
- `tests/` — modular tests for config, bootstrap, persistence, reply, and CLI flows.

## Config and runtime notes

- External llama server binary and model remain outside the repo.
- `.env` is autoloaded only by the CLI boundary.
- `build_runtime()` does not implicitly read repo-root `.env`.
- Runtime precedence is:
  1. existing shell env
  2. `.env` loaded by CLI boundary
  3. TOML defaults
- On Windows, use forward slashes or escaped backslashes in TOML path values.

## Commands currently available

- `doctor`
- `trace-boot`
- `init-db`
- `talk --once "..."`
- `trace-last`

## Deferred on purpose

These are intentionally not part of this vertical slice yet:

- multi-turn live chat orchestration
- advanced thread/mode routing
- recall/memory graph
- onboarding flows
- reminders/tasks
- deep prompt systems
- long-form conversation planning