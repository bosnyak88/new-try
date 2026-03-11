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

This also means shell env always wins over `.env`, and `.env` fills values when TOML is empty or lower-priority.

## TOML path safety (Windows)

When writing filesystem paths directly into TOML config files, ensure backslashes are escaped (for example `C:\\Users\\you\\llama-server.exe`) or use forward slashes (`C:/Users/you/llama-server.exe`).

Programmatic config generation should use `syntaris.config.toml_strings.toml_path_string()` to safely serialize path values in TOML basic strings.

## DB bootstrap flow

`init-db` and talk flow call `PersistenceStore.initialize()`:

1. create `data_dir` (if missing)
2. create/open `db_path`
3. apply explicit SQLite schema
4. write schema metadata (`app_meta.schema_version=1`)

## Talk flow bootstrap

For `talk --once`, the bootstrap path is:

1. CLI parses arguments
2. CLI autoloads repo-root `.env`
3. `build_runtime()` constructs `RuntimeContext`
4. persistence layer initializes/opens SQLite storage
5. reply adapter is selected from config
6. session/turn/trace records are written
7. assistant reply is printed

## Operational notes

- Programmatic runtime construction must remain side-effect free unless explicitly requested otherwise.
- Live backend support is optional and must remain behind the reply adapter boundary.
- SQLite/bootstrap logic must not be moved into CLI argument parsing or config loader code.
- If no live backend is available, the system must return a deterministic degraded fallback reply instead of crashing.