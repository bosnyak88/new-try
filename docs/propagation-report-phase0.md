# Propagation report — REBUILD-005 natural topic/thread routing foundation

## Direct changes

- Added first-class routing contracts (`RouteDecisionAction`, `RouteMatch`, `RouteDecision`, `ThreadSummaryView`, `ThreadListView`).
- Added `orchestration/routing.py` with deterministic Hungarian-first phrase routing.
- Reused one shared turn path so `talk --once`, `talk --live`, and `talk --script` all route through the same decision flow.
- Added `thread-list` CLI command for thread observability.
- Extended trace events with `route_decision_computed` metadata.

## Supported deterministic phrases

- Return/switch existing thread: `vissza a <thread_key> szálra`, `menjünk vissza a <thread_key> szálra`, `váltsunk a <thread_key> szálra`
- Create/switch thread: `új szál: <thread_key>`, `legyen új szál: <thread_key>`, `nyiss új szálat: <thread_key>`

## Precedence

1. explicit CLI overrides
2. explicit live slash commands
3. deterministic natural routing phrases
4. continue active thread

## Structural self-check

- No central monolithic pipeline was introduced.
- Routing, live control parsing, turn execution, persistence, and CLI boundary remain modular.
- Routing logic is not duplicated across once/live/script flows.

## Deferred intentionally

- semantic/LLM routing
- embeddings or fuzzy intent classification
- thread summarization or memory graph
