# Bootstrap and configuration

## External runtime paths

Syntaris intentionally keeps LLM server binary and model files outside this repository.

Set either in `.env` or process environment:

- `SYNTARIS_LLM_SERVER_BIN`
- `SYNTARIS_LLM_MODEL_PATH`
- optional host/port: `SYNTARIS_LLM_HOST`, `SYNTARIS_LLM_PORT`

The CLI bootstrap automatically loads `.env` from the current working directory (repo root in normal usage) before config resolution.

## Config precedence

1. CLI `--config`
2. `SYNTARIS_CONFIG_PATH`
3. default `config/syntaris.example.toml`

For runtime values, precedence is explicit:

1. Shell environment variables (already present in process environment)
2. `.env` values autoloaded at CLI/bootstrap startup
3. TOML defaults from selected config file

This means shell env always wins over `.env`, and `.env` fills values when TOML is empty or lower-priority.
