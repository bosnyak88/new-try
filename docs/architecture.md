## Architecture (REBUILD-009 deterministic thread recap/resume foundation)

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


## Thread recap layer

- `orchestration/recap.py` is a dedicated deterministic layer that maps `ThreadContextPack` => `ThreadRecapView`.
- Shared recap builder is reused by CLI (`thread-recap`) and talk turn execution (`talk --once`, `talk --live`, `talk --script`).
- Recap content is deterministic and bounded: thread metadata + recent turn lines from the context pack window.
- Recap queries are recognized by explicit Hungarian-first phrase families (current/previous/named), with conservative normalization (`strip`, case-insensitive regex).
- Recap is evaluated only after explicit overrides, live slash controls, pending resolution, and deterministic routing phrases.
- Recap turns bypass the reply adapter but still persist a normal turn + trace with recap metadata (`recap_query_recognized`, `thread_recap_built`).


## Thread snapshot / handoff foundation

Syntaris now persists deterministic thread snapshot packs via a shared snapshot module (`orchestration/thread_snapshot.py`).
Snapshots are compact handoff packs built from the thread context window, excluding recap/control/pending turns by default.

CLI inspection uses `thread-snapshot --current`, `thread-snapshot --previous`, or `thread-snapshot <thread_key>` with optional `--refresh` and `--limit`.
Snapshots are also refreshed automatically when routing switches away from a thread so handoff state remains stable for later resume/recall work.

## REBUILD-011 shared conversational cognition layer

Added three dedicated orchestration boundaries:

1. `orchestration/turn_interpret.py`
   - deterministic Hungarian-first interpretation (`ordinary`, recall current/previous/named, resume previous/named, clarification-needed).
2. `orchestration/thread_recall.py`
   - deterministic recall target resolution with precedence from interpretation request (`named > previous > current`) and snapshot-backed loading.
3. `orchestration/response_plan.py`
   - explicit plan building (`ordinary`, `recall`, `resume`, `clarification`) before final verbalization.

`execute_turn()` now uses one shared path for once/live/script:
route/pending -> interpretation -> recall resolution -> response plan -> rendering (`reply/plan_renderer.py`) -> persistence -> trace.

This keeps reply generation modular: plan construction is orchestration logic; textual rendering is a reply-boundary concern.

## REBUILD-012 active-focus foundation

A dedicated `orchestration.thread_focus` module builds/loads/updates compact `ThreadFocusPack` state, and `orchestration.followup_resolution` resolves shorthand follow-up phrases deterministically.
Response planning consumes focus state via contract fields (`focus_used`, follow-up target) instead of hidden prompt logic.
Persistence is explicit in `thread_focus` table, separate from snapshots.


## Deliberation layer

REBUILD-013 adds shared deterministic comparison-pack and answer-strategy orchestration between interpretation/recall/focus resolution and response-plan rendering. Once/live/script remain on the same execution path. Trace now records `comparison_pack_built` and `answer_strategy_selected` for inspectability without exposing chain-of-thought.
