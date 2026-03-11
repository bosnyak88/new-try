# Bootstrap and configuration

## External runtime paths

Syntaris intentionally keeps LLM server binary and model files outside this repository.

Set either in `.env` or process environment:

- `SYNTARIS_LLM_SERVER_BIN`
- `SYNTARIS_LLM_MODEL_PATH`
- optional host/port: `SYNTARIS_LLM_HOST`, `SYNTARIS_LLM_PORT`

## Config precedence

1. CLI `--config`
2. `SYNTARIS_CONFIG_PATH`
3. default `config/syntaris.example.toml`

Environment values override TOML values for runtime-sensitive settings.
