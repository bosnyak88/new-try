# Propagation report — REBUILD-004 multi-turn conversational loop

## Direct changes

- Added explicit live-loop contracts (`LoopAction`, `LoopCommand`, `LiveConversationState`, `LiveTurnOutput`).
- Introduced `orchestration/turns.py` with single reusable `execute_turn()` path.
- Refactored `talk_once` to delegate to shared turn execution.
- Added `orchestration/live_loop.py` for multi-turn orchestration and control command routing.
- Expanded CLI talk surface with `--live` and deterministic `--script` loop mode.
- Added loop-aware trace metadata (`turn_execution_source`) and loop lifecycle/control events.

## Propagated layers

- **Contracts:** loop flow is typed and explicit; no loose command strings across layers.
- **Orchestration:** loop, one-shot, and turn execution have distinct module boundaries.
- **Persistence:** existing session/thread/mode/turn persistence is reused without schema sprawl.
- **Trace:** live/once execution source is visible and loop command handling is auditable.
- **Docs/tests/changelog:** synchronized to new CLI and loop behavior.

## Structural self-check

- No giant central pipeline file introduced.
- `talk --once` and live loop share one turn path (`execute_turn`).
- CLI remains thin and does not duplicate business orchestration.
- Loop control parsing is centralized in `live_loop.py`.

## Deferred intentionally

- advanced routing
- memory/recall graph
- proactive autonomy
- TUI/GUI interaction
