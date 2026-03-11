from syntaris.config.loader import load_app_config
from syntaris.config.toml_strings import toml_basic_string, toml_path_string


def test_toml_path_string_escapes_windows_backslashes_for_parser(tmp_path, monkeypatch):
    windows_server_path = r"C:\Users\dev\AppData\Local\Programs\llama-server.exe"
    windows_model_path = r"D:\models\tiny\model.gguf"

    monkeypatch.delenv("SYNTARIS_LLM_SERVER_BIN", raising=False)
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)

    config = tmp_path / "syntaris.toml"
    config.write_text(
        f"""
[app]
name = "syntaris"
environment = "development"

[llm]
server_bin_path = {toml_path_string(windows_server_path)}
model_path = {toml_path_string(windows_model_path)}
host = "127.0.0.1"
port = 8080
""".strip(),
        encoding="utf-8",
    )

    loaded = load_app_config(str(config))

    assert loaded.llm.server_bin_path == windows_server_path
    assert loaded.llm.model_path == windows_model_path


def test_toml_basic_string_escapes_quotes_and_backslashes():
    value = 'C:\\path\\"quoted"\\bin'

    encoded = toml_basic_string(value)

    assert encoded == '"C:\\\\path\\\\\\"quoted\\"\\\\bin"'
