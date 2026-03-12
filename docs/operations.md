# Operations baseline

## Commands

### `doctor`

Validates external llama binary/model path presence and port sanity.

### `init-db`

Initializes runtime data directory and SQLite schema/migrations.

### `talk --once "..." [--thread <thread_key>] [--mode <mode>]`

Runs one turn through shared `execute_turn()` orchestration.

### `talk --live`

Runs interactive multi-turn loop:

- normal text => persisted talk turn (via shared deterministic route resolver)
- `/allapot` => compact status
- `/szal <thread_key>` => switch active thread
- `/mod <mode>` => switch active mode
- `/kilep` => exit cleanly

### `talk --script <path>`

Runs deterministic non-interactive loop from newline-delimited input file.
Each output row is emitted as compact JSON for tests.

### `session-status`

Prints compact JSON view of active conversation state, including `previous_thread_id` and `previous_thread_key`.

### `trace-last`

Prints latest persisted turn and its trace events including session/thread/mode/backend/degraded context, plus thread context-load metadata.


### `thread-list`

Prints known threads for the active session with active/previous markers, turn counts, and last turn ids.

### `thread-view --current | --previous | <thread_key> [--limit <N>]`

Prints compact deterministic context-pack JSON for active, previous, or named thread target.
Includes session/thread metadata, bounded recent turns, and previous-thread pointers when present.

## Route precedence

1. explicit CLI flags (`--thread`, `--mode`)
2. live slash control commands (`/szal`, `/mod`, etc.)
3. deterministic named thread-routing phrases
4. deterministic previous-thread/topic-shift phrases
5. active-thread continuation fallback


## Pending-route operations

- `session-status` now surfaces `pending_route` metadata when clarification is waiting.
- `trace-last` includes proposal/resolution metadata (`pending_route_proposed`, `pending_route_confirmed`, `pending_route_rejected`, `pending_route_cancelled`).


### `thread-recap [--current|--previous|<thread_key>] [--limit <N>]`

Builds and prints a compact deterministic recap view for the selected thread target.

- `--current`: active thread recap
- `--previous`: previous-thread recap (returns `found=false` when missing)
- `<thread_key>`: named-thread recap

### Recap queries in talk flows

The same recap builder is used in once/live/script execution when deterministic recap phrases are matched:

- current: `hol tartunk?`, `hol tartunk most?`, `mutasd a mostani szálat`, `foglald össze ezt a szálat`
- previous: `mutasd az előző szálat`, `foglald össze az előző szálat`, `hol tartunk az előző szálon?`
- named: `mutasd a <thread_key> szálat`, `foglald össze a <thread_key> szálat`, `hol tartunk a <thread_key> szálon?`

Recap queries do not implicitly switch active thread and produce trace metadata for recap handling.


## Thread snapshot / handoff foundation

Syntaris now persists deterministic thread snapshot packs via a shared snapshot module (`orchestration/thread_snapshot.py`).
Snapshots are compact handoff packs built from the thread context window, excluding recap/control/pending turns by default.

CLI inspection uses `thread-snapshot --current`, `thread-snapshot --previous`, or `thread-snapshot <thread_key>` with optional `--refresh` and `--limit`.
Snapshots are also refreshed automatically when routing switches away from a thread so handoff state remains stable for later resume/recall work.
