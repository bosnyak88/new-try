## Architecture (REBUILD-008 deterministic thread context pack foundation)

## Design principles

- Contract-first: loop/state/turn outputs are explicit dataclasses.
- Structure-first: config/bootstrap/persistence/reply/orchestration/trace/CLI remain separated.
- No monolithic pipeline: one reusable single-turn path is called by both CLI wrappers.
- Routing is a dedicated orchestration layer, reused by once/live/script message execution.

## Conversation model

- **session**: top-level conversation container.
- **thread**: named stream within one session (e.g. `default`, `work`).
- **mode**: explicit turn metadata (currently free-form, default `chat`).
- **active state**: persisted pointers for active session, active thread, active mode, and previous active thread.
- **live loop state**: projected from active state every loop step.

## Layer overview

1. `contracts/`
   - `LoopAction`, `LoopCommand`, `LiveConversationState`, `LiveTurnOutput`, plus existing talk/session contracts.
2. `orchestration/turns.py`
   - single reusable `execute_turn()` orchestration path.
3. `orchestration/talk.py`
   - thin wrappers (`talk_once`, state helpers, trace-last).
4. `orchestration/live_loop.py`
   - loop command parsing, control routing, and repeated calls into `execute_turn()`.
5. `persistence/`
   - active state/session/thread/turn/trace persistence unchanged in shape.
6. `trace/`
   - turn trace enriched with execution source (`talk_once` vs `talk_live`) plus loop-level events.
7. `cli.py`
   - boundary routing only (`--once`, `--live`, `--script`).

## Live controls

- `/kilep` (alias `/exit`) - exit loop
- `/allapot` (alias `/status`) - compact status output
- `/szal <thread_key>` (alias `/thread ...`) - switch active thread
- `/mod <mode>` (alias `/mode ...`) - switch active mode

Control commands are not persisted as normal turns.


## Routing layer

- `orchestration/routing.py` resolves deterministic route decisions before turn execution.
- Actions: `CONTINUE_ACTIVE`, `SWITCH_EXISTING`, `CREATE_AND_SWITCH`, `SWITCH_PREVIOUS`, `NO_ROUTE_CHANGE`.
- `execute_turn()` applies precedence: explicit request overrides first, then deterministic named routing, then deterministic previous-thread/topic-shift phrases, then continue active.
- live slash commands stay explicit controls and are handled before natural routing phrases.


## Pending-route clarification layer

- Suggestive Hungarian-first phrases create persisted `pending_route` state instead of immediate switch.
- The next turn resolves pending state deterministically: affirmative = switch and execute held message on proposed thread; negative = stay and execute held message on current thread; other input = cancel pending and process new input normally.
- `talk --once`, `talk --live`, and `talk --script` share the same pre-turn route/pending resolution path in orchestration (`execute_turn`).


## Thread context projection layer

- Added a dedicated orchestration module (`orchestration/context_pack.py`) to build deterministic `ThreadContextPack` views.
- The same projection path serves CLI inspection (`thread-view`) and turn-time context loading (`execute_turn`).
- Projection remains bounded (`conversation.context_turn_window`, overrideable via `thread-view --limit`).
- Context packs are raw-but-shaped: session/thread metadata + bounded recent persisted turns; no summarization, embeddings, or semantic recall.
