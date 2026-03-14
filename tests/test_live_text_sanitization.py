from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop
from syntaris.orchestration.text_normalize import normalize_text
from syntaris.orchestration.talk import trace_last


def _write_config(path, db_path, data_dir):
    path.write_text(
        f"""
[app]
name = "syntaris"
environment = "test"

[llm]
server_bin_path = ""
model_path = ""
host = "127.0.0.1"
port = 8080

[paths]
data_dir = "{data_dir.as_posix()}"
db_path = "{db_path.as_posix()}"

[conversation]
default_thread_key = "default"
default_mode = "chat"

[reply]
backend = "deterministic"
live_url = ""
live_model = ""
timeout_seconds = 1.0

[trace]
enabled = true
level = "info"
""".strip(),
        encoding="utf-8",
    )


def test_normalize_text_replaces_unpaired_surrogate():
    normalized = normalize_text("ár\udc81pi")

    assert "\udc81" not in normalized.canonical_text
    assert "�" in normalized.canonical_text


def test_live_loop_surrogate_input_is_persistence_safe(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["szia syntaris én Ár\udc81pi vagyok", "/kilep"])
    turns = [item for item in result.outputs if item.kind in {"turn", "recall", "resume", "structured", "clarification"}]

    assert turns
    assert turns[0].message.strip() != ""

    last = trace_last(runtime)
    assert last.turn is not None
    assert "\udc81" not in last.turn.user_message
