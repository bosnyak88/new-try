# Architecture (REBUILD-003 state foundation)

## Design principles

- Contract-first: session/thread/mode and state view entities are explicit dataclasses.
- Structure-first: config/bootstrap/persistence/reply/orchestration/trace/CLI remain separated.
- No monolithic pipeline: command orchestration composes leaf modules.

## Session / thread / mode model

- **session**: top-level conversation container.
- **thread**: named stream within one session (e.g. `default`, `work`).
- **mode**: explicit turn metadata (currently `chat`).
- **active state**: persisted pointers for active session, active thread, and active mode.

## Layer overview

1. `contracts/`
   - `ModeKind`, `ConversationConfig`, `ThreadRecord`, `ActiveConversationState`, `TalkRequest`.
2. `config/`
   - TOML/env loading, including `[conversation]` defaults.
3. `bootstrap/`
   - Side-effect-free `RuntimeContext` assembly.
4. `persistence/`
   - SQLite schema + migrations + store API for active state/session/thread/turn/trace.
5. `reply/`
   - Adapter boundary with deterministic fallback and optional llama-http path.
6. `orchestration/`
   - `init_db`, `resolve_active_state`, `talk_once`, `trace_last`.
7. `trace/`
   - state-aware turn event shaping (`active_state_resolved`, `thread_resolved_or_created`, `reply_generated`, `turn_persisted`).
8. `cli.py`
   - command routing only; no business logic dumping.

## Deferred intentionally

- advanced multi-mode routing
- memory graph / recall subsystems
- onboarding/reminders/planning systems
