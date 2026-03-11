# Bootstrap and configuration

## Runtime boundary

`build_runtime()` only constructs `RuntimeContext` from config sources.
It does not load `.env` implicitly.

`syntaris.cli` is the CLI boundary that calls `load_repo_env()` before runtime construction.

## Config keys

- `app`: name/environment
- `llm`: external llama runtime paths and host/port
- `paths`: `data_dir`, `db_path`
- `reply`: backend config (`deterministic` or `llama-http`)
- `trace`: trace flags

## Precedence

Config file selection:

1. CLI `--config`
2. `SYNTARIS_CONFIG_PATH`
3. `config/syntaris.example.toml`

Runtime value precedence:

1. existing shell env
2. `.env` loaded by CLI boundary
3. TOML defaults

This preserves the Phase-0.1a rule: no hidden global `.env` side effects in generic runtime builders.

## DB bootstrap flow

`init-db` and talk flow call `PersistenceStore.initialize()`:

1. create `data_dir` (if missing)
2. create/open `db_path`
3. apply explicit SQLite schema
4. write schema metadata (`app_meta.schema_version=1`)
