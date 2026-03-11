# Bootstrap and configuration

## Runtime boundary

`build_runtime()` constructs `RuntimeContext` from config sources only.
It does not load `.env` implicitly.

`syntaris.cli` remains the CLI boundary that calls `load_repo_env()` before runtime construction.

## Config keys

- `app`: name/environment
- `llm`: external llama runtime paths and host/port
- `paths`: `data_dir`, `db_path`
- `conversation`: `default_thread_key`, `default_mode`
- `reply`: backend config (`deterministic` or `llama-http`)
- `trace`: trace flags

## DB bootstrap flow

`init-db`, talk, and loop flows call `PersistenceStore.initialize()`:

1. create `data_dir` (if missing)
2. create/open `db_path`
3. apply explicit SQLite schema
4. migrate legacy REBUILD-002 schema when needed
5. write schema metadata (`app_meta.schema_version=2`) and preserve active/previous thread pointers in `app_meta`

## Active state resolution

On one-shot talk, live loop entry, and status:

1. resolve active state from `app_meta` pointers
2. if missing, create new session + default thread and set default mode
3. apply thread/mode switches as requested and maintain previous-thread pointer whenever active thread changes
4. persist resulting active pointers for subsequent turns


## Routing bootstrap note

No additional boot-time providers are required for REBUILD-005 routing. The deterministic phrase matcher runs inside orchestration using persisted active state plus known thread list from storage.


- `app_meta.pending_route` stores deterministic pending-route proposals (held message + proposed thread + reason + metadata) until confirmation, rejection, or cancellation.
