# Operations baseline

## Commands

### `doctor`

Validates external llama binary/model path presence and port sanity.

### `init-db`

Initializes runtime data directory and SQLite schema.

### `talk --once "..."`

Runs one turn:

1. open/create DB
2. create session
3. generate reply through adapter boundary
4. persist turn
5. persist trace events

If no live backend is configured/available, deterministic fallback returns a stable degraded reply.

### `trace-last`

Prints the latest persisted turn plus its trace events from SQLite.

## Runtime artifacts

All runtime artifacts are in configured local data dir / DB path and are intentionally outside git-tracked binaries/models.
