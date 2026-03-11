# Syntaris (Greenfield Rebuild)

Phase-0 foundation for a modular, contract-first local runtime.

## Quick start

1. Copy environment template:
   - `cp .env.example .env`
2. Set external runtime paths:
   - `SYNTARIS_LLM_SERVER_BIN`
   - `SYNTARIS_LLM_MODEL_PATH`
3. Install in editable mode:
   - `python -m pip install -e .[dev]`
4. Run checks:
   - `syntaris --config config/syntaris.example.toml doctor`
   - `syntaris --config config/syntaris.example.toml trace-boot`

## Repository map

- `src/syntaris/contracts` — shared runtime contracts and data structures.
- `src/syntaris/config` — config loading with env override support.
- `src/syntaris/bootstrap` — runtime composition and bootstrapping.
- `src/syntaris/core` — leaf-level reusable domain utilities.
- `src/syntaris/orchestration` — command orchestration flow.
- `src/syntaris/trace` — trace event shaping.
- `docs/` — architecture, operations, and propagation reporting.
- `tests/` — baseline tests for config and doctor flows.
