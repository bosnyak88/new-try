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

- normal text => persisted talk turn
- `/allapot` => compact status
- `/szal <thread_key>` => switch active thread
- `/mod <mode>` => switch active mode
- `/kilep` => exit cleanly

### `talk --script <path>`

Runs deterministic non-interactive loop from newline-delimited input file.
Each output row is emitted as compact JSON for tests.

### `session-status`

Prints compact JSON view of active conversation state.

### `trace-last`

Prints latest persisted turn and its trace events including session/thread/mode/backend/degraded context.
