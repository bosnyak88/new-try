# Changelog

## 0.5.0 - REBUILD-005 deterministic natural thread routing

- Added first-class routing contracts and thread list view contracts.
- Added deterministic Hungarian-first natural route resolver for return/switch and create/switch thread phrases.
- Unified routing path in shared turn execution for once/live/script message execution.
- Added `thread-list` CLI command for known-thread inspection and active marker visibility.
- Extended turn trace events with route decision metadata.
- Added deterministic tests for route matching, route precedence, thread listing, and trace alignment.
- Updated architecture/operations/bootstrap/README propagation docs for route behavior and precedence.

## 0.4.0 - REBUILD-004 multi-turn conversational loop

- Added live-loop contracts: `LoopAction`, `LoopCommand`, `LiveConversationState`, and `LiveTurnOutput`.
- Introduced shared single-turn orchestration (`execute_turn`) and made `talk --once` a thin wrapper around it.
- Added multi-turn loop orchestration with in-loop control commands (`/allapot`, `/szal`, `/mod`, `/kilep` plus aliases).
- Expanded CLI with `talk --live` and deterministic scripted loop mode `talk --script <path>`.
- Extended trace events with turn execution source and loop lifecycle/control audit events.
- Added deterministic tests for scripted multi-turn flow, control behavior, state reuse, and trace alignment.
- Updated docs and propagation report to describe live-loop architecture and command surface.

## 0.3.0 - REBUILD-003 session/thread/mode foundation

- Added first-class contracts for mode/thread/active conversation state and talk request metadata.
- Added `[conversation]` config defaults (`default_thread_key`, `default_mode`).
- Extended persistence schema with `threads` and active-state pointers, and persisted thread/mode fields on turns and trace events.
- Added migration behavior to keep REBUILD-002 databases readable while moving to schema version 2.
- Updated orchestration to resolve/reuse active session/thread state and support `talk --once` thread/mode overrides.
- Added `session-status` CLI command and expanded `trace-last` output with session/thread/mode context.
- Extended deterministic tests for migration, active-state reuse, thread switching, mode persistence, and trace projection.

## 0.2.0 - REBUILD-002 vertical slice

- Added persistence package with SQLite bootstrap schema (`app_meta`, `sessions`, `turns`, `trace_events`).
- Extended runtime contracts with app paths, reply config, session/turn/trace entities, and persistence bootstrap result.
- Added reply adapter boundary with deterministic degraded fallback and optional llama-http integration.
- Added orchestration + CLI commands: `init-db`, `talk --once`, `trace-last`.
- Added turn-level trace persistence and inspection path.
- Updated docs, config templates, and tests for the modular talk slice.

## 0.1.0 - Phase-0 foundation

- Established modular package skeleton and contract-first runtime definitions.
- Added config and env templates with external llama server/model path support.
- Added CLI with `doctor` and `trace-boot` commands.
- Added baseline docs and tests for bootstrap behavior.
