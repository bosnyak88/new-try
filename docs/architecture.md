# Architecture (Phase-0 talk slice)

## Design principles

- Contract-first: runtime/session/turn/trace structures are explicit dataclasses.
- Structure-first: config/bootstrap/persistence/reply/orchestration/trace are separate layers.
- No monolithic pipeline: CLI dispatches, orchestration composes, leaf modules execute.

## Layer overview

1. `contracts/`
   - `AppConfig`, `AppPaths`, `ReplyConfig`, `SessionRecord`, `TurnInput`, `TurnResult`, `TraceEventRecord`, `LastTurnTraceView`.
2. `config/`
   - TOML + env loading into contracts.
3. `bootstrap/`
   - Side-effect-free `RuntimeContext` assembly.
4. `persistence/`
   - SQLite schema and explicit store API (`initialize`, `create_session`, `create_turn`, `create_trace_events`, `read_last_turn_trace`).
5. `reply/`
   - Adapter boundary (`build_reply_adapter`) with deterministic fallback and optional llama-http path.
6. `orchestration/`
   - `doctor`, `init_db`, `talk_once`, `trace_last` flows.
7. `trace/`
   - Boot and turn-level trace event shaping.
8. `cli.py`
   - CLI boundary + command routing.

## Scope intentionally deferred

- multi-turn thread routing
- memory graphs
- onboarding/intent systems
- advanced planning prompts
