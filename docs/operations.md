# Operations baseline

## Commands

### `doctor`

Validates external llama binary/model path presence and port sanity.

### `init-db`

Initializes runtime data directory and SQLite schema/migrations.

### `talk --once "..." [--thread <thread_key>] [--mode <mode>]`

Runs one turn:

1. open/create DB and apply migrations
2. resolve or create active session/thread/mode state
3. apply thread/mode overrides if provided
4. generate reply through adapter boundary
5. persist turn with session/thread/mode metadata
6. persist trace events with conversation context

If no live backend is available, deterministic fallback returns a stable degraded reply.

### `session-status`

Prints compact JSON view of active conversation state:

- `session_id`
- `thread_id`
- `thread_key`
- `mode`
- `turn_count`
- `last_turn_id`

### `trace-last`

Prints latest persisted turn and its trace events including session/thread/mode/backend/degraded context.
