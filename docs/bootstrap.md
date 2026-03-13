# Bootstrap and configuration

## Runtime bootstrap truth

`build_runtime()` constructs `RuntimeContext` from config only.  
`syntaris.cli` is the `.env` boundary via `load_repo_env()`.

## Config sections

- `[app]`: app name/environment
- `[llm]`: external llama path/host/port settings
- `[paths]`: `data_dir`, `db_path`
- `[conversation]`: context/snapshot/recall/focus/reasoning/scoped-state knobs
- `[reply]`: backend + timeout settings
- `[trace]`: enable + level
- `[time]`: timezone

## DB bootstrap flow

`init-db` and runtime entrypoints call `PersistenceStore.initialize()`:
1. create/open data dir and db
2. apply schema + migrations
3. persist `app_meta.schema_version=6`
4. keep active/pending pointers in `app_meta`

Authoritative persisted model (v6):
- conversation/runtime: `sessions`, `threads`, `turns`
- derived artifacts: `thread_snapshots`, `thread_focus`
- explicit claims + scoped state: `personal_claims`
- observability: `trace_events`
- lightweight runtime pointers: `app_meta`

## Environment/dependency truth

- Deterministic runtime does not require live llama server.
- `tzdata` is declared dependency for reproducible timezone behavior on platforms that need it.
- No manual rescue bootstrap step is required for REBUILD-018/020 baseline.
