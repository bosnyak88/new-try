# Architecture (Phase-0)

## Design principles

- Contract-first: shared data contracts are declared under `contracts/` before orchestration logic.
- Structure-first: responsibilities are separated into config, bootstrap, orchestration, core, and trace layers.
- No central mega-pipeline: orchestration remains thin and delegates to explicit modules.

## Layer overview

1. `contracts/`
   - AppConfig, LLMConfig, RuntimeContext, DoctorResult.
2. `config/`
   - TOML + environment resolution.
3. `bootstrap/`
   - RuntimeContext assembly.
4. `core/`
   - Atomic domain checks.
5. `orchestration/`
   - Command-level flow (`run_doctor`).
6. `trace/`
   - Boot trace event projection.
7. `cli.py`
   - Command dispatch (`doctor`, `trace-boot`).
