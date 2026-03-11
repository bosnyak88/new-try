from pathlib import Path

from syntaris.config.toml_strings import toml_basic_string, toml_path_string


def write_runtime_toml_config(
    config_path: Path,
    *,
    server_bin_path: str,
    model_path: str,
    host: str = "127.0.0.1",
    port: int = 8080,
    app_name: str = "syntaris",
    environment: str = "development",
) -> None:
    """Write runtime config TOML with path fields serialized safely for Windows."""
    config_path.write_text(
        f"""
[app]
name = {toml_basic_string(app_name)}
environment = {toml_basic_string(environment)}

[llm]
server_bin_path = {toml_path_string(server_bin_path)}
model_path = {toml_path_string(model_path)}
host = {toml_basic_string(host)}
port = {port}
""".strip(),
        encoding="utf-8",
    )
