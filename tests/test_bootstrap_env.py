import json

from syntaris import cli
from syntaris.bootstrap.env import load_repo_env
from syntaris.bootstrap.init_app import build_runtime
from syntaris.config.toml_strings import toml_basic_string


def _write_runtime_config(config_path, server_bin_path: str, model_path: str) -> None:
    config_path.write_text(
        f"""
[app]
name = "syntaris"
environment = "development"

[llm]
server_bin_path = {toml_basic_string(server_bin_path)}
model_path = {toml_basic_string(model_path)}
host = "127.0.0.1"
port = 8080
""".strip(),
        encoding="utf-8",
    )


def test_cli_doctor_autoloads_repo_dotenv_and_reports_healthy(tmp_path, monkeypatch, capsys):
    server = tmp_path / "llama-server"
    model = tmp_path / "model.gguf"
    server.write_text("bin")
    model.write_text("model")

    config = tmp_path / "syntaris.toml"
    _write_runtime_config(config, server_bin_path="", model_path="")

    (tmp_path / ".env").write_text(
        f"SYNTARIS_LLM_SERVER_BIN={server}\nSYNTARIS_LLM_MODEL_PATH={model}\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SYNTARIS_LLM_SERVER_BIN", raising=False)
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "doctor"])

    exit_code = cli.main()
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["healthy"] is True


def test_programmatic_runtime_build_does_not_implicitly_load_dotenv(tmp_path, monkeypatch):
    server = tmp_path / "llama-server"
    model = tmp_path / "model.gguf"
    server.write_text("bin")
    model.write_text("model")

    config = tmp_path / "syntaris.toml"
    _write_runtime_config(config, server_bin_path="", model_path="")

    (tmp_path / ".env").write_text(
        f"SYNTARIS_LLM_SERVER_BIN={server}\nSYNTARIS_LLM_MODEL_PATH={model}\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SYNTARIS_LLM_SERVER_BIN", raising=False)
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)

    runtime = build_runtime(str(config))

    assert runtime.config.llm.server_bin_path == ""
    assert runtime.config.llm.model_path == ""


def test_shell_env_overrides_dotenv(tmp_path, monkeypatch):
    dotenv_server = tmp_path / "dotenv-llama-server"
    shell_server = tmp_path / "shell-llama-server"
    model = tmp_path / "model.gguf"
    dotenv_server.write_text("bin")
    shell_server.write_text("bin")
    model.write_text("model")

    config = tmp_path / "syntaris.toml"
    _write_runtime_config(config, server_bin_path="toml-default", model_path="")

    (tmp_path / ".env").write_text(
        f"SYNTARIS_LLM_SERVER_BIN={dotenv_server}\nSYNTARIS_LLM_MODEL_PATH={model}\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SYNTARIS_LLM_SERVER_BIN", str(shell_server))
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)

    load_repo_env()
    runtime = build_runtime(str(config))

    assert runtime.config.llm.server_bin_path == str(shell_server)
    assert runtime.config.llm.model_path == str(model)
