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

`init-db` and talk/status flows call `PersistenceStore.initialize()`:

1. create `data_dir` (if missing)
2. create/open `db_path`
3. apply explicit SQLite schema
4. migrate legacy REBUILD-002 schema when needed
5. write schema metadata (`app_meta.schema_version=2`)

## Active state resolution

On talk/status:

1. resolve active state from `app_meta` pointers
2. if missing, create new session + default thread and set default mode
3. optional `--thread` resolves/creates that thread and marks it active
4. optional `--mode` persists explicit mode metadata on turn and active pointers

This keeps active-state logic in orchestration + persistence, not in CLI parsing.
