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
    assert config.conversation.context_turn_window == 5
    assert config.conversation.snapshot_turn_window == 8
    assert config.conversation.snapshot_include_recap_turns is False
    assert config.conversation.snapshot_include_pending_turns is False

    assert config.conversation.recall_line_limit == 3
    assert config.conversation.recall_prefer_snapshot is True
    assert config.conversation.response_followup_enabled is True
    assert config.conversation.focus_turn_window == 8
    assert config.conversation.focus_line_limit == 4
    assert config.conversation.followup_resolution_enabled is True



def test_env_overrides_deliberation_flags(monkeypatch):
    monkeypatch.setenv("SYNTARIS_MAX_COMPARISON_CANDIDATES", "4")
    monkeypatch.setenv("SYNTARIS_CLARIFICATION_PREFER_WHEN_CLOSE", "false")
    monkeypatch.setenv("SYNTARIS_UNCERTAINTY_LABELING_ENABLED", "true")

    config = load_app_config("config/syntaris.example.toml")

    assert config.conversation.max_comparison_candidates == 4
    assert config.conversation.clarification_prefer_when_close is False
    assert config.conversation.uncertainty_labeling_enabled is True


def test_timezone_config_loaded_and_overridable(monkeypatch):
    config = load_app_config("config/syntaris.example.toml")
    assert config.time.timezone == "Europe/Budapest"

    monkeypatch.setenv("SYNTARIS_TIMEZONE", "Europe/Berlin")
    overridden = load_app_config("config/syntaris.example.toml")
    assert overridden.time.timezone == "Europe/Berlin"


def test_compat_aliases_do_not_override_explicit_temp_config(tmp_path, monkeypatch):
    cfg = tmp_path / "syntaris.temp.toml"
    cfg.write_text(
        f'''
[app]
name = "syntaris"
environment = "test"

[llm]
server_bin_path = ""
model_path = ""

[paths]
data_dir = "{(tmp_path / 'data').as_posix()}"
db_path = "{(tmp_path / 'expected.db').as_posix()}"

[conversation]
default_thread_key = "default"
default_mode = "chat"
artifact_allowed_roots = "{(tmp_path / 'sandbox').as_posix()}"

[reply]
backend = "deterministic"

[trace]
enabled = true
level = "info"
'''.strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("SYNTARIS_DB", str(tmp_path / "ambient.db"))
    monkeypatch.setenv("SYNTARIS_SANDBOX_ROOTS", str(tmp_path / "ambient_root"))

    config = load_app_config(str(cfg))

    assert config.paths.db_path == (tmp_path / "expected.db").as_posix()
    assert config.conversation.artifact_allowed_roots == ((tmp_path / "sandbox").as_posix(),)
