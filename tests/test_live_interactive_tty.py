from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop_interactive


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


def test_live_interactive_eof_exits_cleanly(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    result = run_live_loop_interactive(runtime, input_func=_raise_eof)
    assert result.outputs[-1].kind == "exit"
