from syntaris.bootstrap.init_app import build_runtime


def test_dotenv_is_autoloaded_for_runtime(tmp_path, monkeypatch):
    server = tmp_path / "llama-server"
    model = tmp_path / "model.gguf"
    server.write_text("bin")
    model.write_text("model")

    config = tmp_path / "syntaris.toml"
    config.write_text(
        """
[app]
name = "syntaris"
environment = "development"

[llm]
server_bin_path = ""
model_path = ""
host = "127.0.0.1"
port = 8080
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / ".env").write_text(
        f"SYNTARIS_LLM_SERVER_BIN={server}\nSYNTARIS_LLM_MODEL_PATH={model}\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SYNTARIS_LLM_SERVER_BIN", raising=False)
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)

    runtime = build_runtime(str(config))

    assert runtime.config.llm.server_bin_path == str(server)
    assert runtime.config.llm.model_path == str(model)


def test_shell_env_overrides_dotenv(tmp_path, monkeypatch):
    dotenv_server = tmp_path / "dotenv-llama-server"
    shell_server = tmp_path / "shell-llama-server"
    model = tmp_path / "model.gguf"
    dotenv_server.write_text("bin")
    shell_server.write_text("bin")
    model.write_text("model")

    config = tmp_path / "syntaris.toml"
    config.write_text(
        """
[app]
name = "syntaris"
environment = "development"

[llm]
server_bin_path = "toml-default"
model_path = ""
host = "127.0.0.1"
port = 8080
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / ".env").write_text(
        f"SYNTARIS_LLM_SERVER_BIN={dotenv_server}\nSYNTARIS_LLM_MODEL_PATH={model}\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SYNTARIS_LLM_SERVER_BIN", str(shell_server))
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)

    runtime = build_runtime(str(config))

    assert runtime.config.llm.server_bin_path == str(shell_server)
    assert runtime.config.llm.model_path == str(model)

