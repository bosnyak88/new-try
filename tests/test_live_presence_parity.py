from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop


def _write_config(path, db_path, data_dir):
    path.write_text(
        f'''
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
'''.strip(),
        encoding="utf-8",
    )


def test_live_presence_sequence_keeps_non_filler_replies(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    live = run_live_loop(runtime, [
        "szia syntaris én Árpi vagyok",
        "a te neved syntaris",
        "én tervezlek és fejlesztelek",
        "a személyes kognitív rendszerem leszel",
        "miben segítesz nekem?",
        "folytassuk innen",
        "/kilep",
    ])
    turns = [o.message for o in live.outputs if o.kind in {"turn", "structured", "recall", "resume", "clarification"}]
    assert turns
    assert all(t.strip() != "Rendben." for t in turns[-2:])
    assert "determinisztikus" in turns[-2].lower()
