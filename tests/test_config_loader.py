from syntaris.config.loader import load_app_config


def test_env_overrides_llm_paths(tmp_path, monkeypatch):
    server = tmp_path / "llama-server"
    model = tmp_path / "model.gguf"
    server.write_text("bin")
    model.write_text("model")

    monkeypatch.setenv("SYNTARIS_LLM_SERVER_BIN", str(server))
    monkeypatch.setenv("SYNTARIS_LLM_MODEL_PATH", str(model))

    config = load_app_config("config/syntaris.example.toml")

    assert config.llm.server_bin_path == str(server)
    assert config.llm.model_path == str(model)
    assert config.conversation.default_thread_key == "default"
    assert config.conversation.default_mode == "chat"
