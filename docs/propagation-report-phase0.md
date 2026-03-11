# Propagation report — REBUILD-003 session/thread/mode foundation

## Direct changes

- Added explicit contracts for mode/thread/active-state/talk-request.
- Extended SQLite schema with `threads`, active-state pointers in `app_meta`, and mode/thread fields on turns and trace events.
- Added migration path for REBUILD-002 databases (schema v1 -> v2).
- Extended talk orchestration to resolve/reuse active state and to support explicit thread/mode overrides.
- Expanded CLI with `session-status` and new `talk` flags (`--thread`, `--mode`).
- Extended trace shaping and persisted trace payloads with session/thread/mode context.

## Propagated layers

- **Contracts:** no loose session/thread/mode dict passing in orchestration.
- **Config/bootstrap:** conversation defaults added without reintroducing hidden `.env` side effects.
- **Persistence:** active-state/session/thread/turn/trace logic centralized in store module.
- **Orchestration:** runtime composition handles state resolution; CLI stays thin.
- **Trace:** events now explain which conversation context handled the turn.
- **Docs/config/tests/changelog:** synchronized with new behavior and schema version.

## Structural self-check

- No giant central pipeline file introduced.
- Business logic not moved into `cli.py`.
- Session/thread/mode resolution is not duplicated across layers.
- SQLite logic remains outside config loading and CLI parsing.

## Deferred intentionally

- intelligent mode switching
- memory graph/recall systems
- advanced routing and planning workflows
