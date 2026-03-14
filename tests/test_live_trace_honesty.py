from syntaris.bootstrap.init_app import build_runtime
from syntaris.contracts.runtime import LiveConversationState, LiveTurnOutput
from syntaris.orchestration.live_loop import run_live_loop
from syntaris.orchestration.talk import trace_last
from syntaris import cli


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


def test_live_turn_failure_persists_bounded_failure_trace(tmp_path, monkeypatch):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    from syntaris.orchestration import live_loop as module

    def _boom(*_args, **_kwargs):
        raise UnicodeEncodeError("utf-8", "x", 0, 1, "surrogates not allowed")

    monkeypatch.setattr(module, "execute_turn", _boom)

    out = run_live_loop(runtime, ["szia", "/kilep"])
    errors = [item for item in out.outputs if item.kind == "error"]
    assert errors
    assert errors[0].message.startswith("[degraded-live]")

    last = trace_last(runtime)
    names = [event.event_name for event in last.trace_events]
    assert "live_turn_failed" in names


def test_live_output_sanitized_trace_is_recorded(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    output = LiveTurnOutput(
        kind="turn",
        message="teszt",
        state=LiveConversationState(
            session_id=1,
            thread_id=1,
            thread_key="default",
            mode="chat",
            turn_count=0,
            last_turn_id=None,
        ),
        turn_id=0,
        backend="deterministic",
        degraded=True,
    )
    cli._record_live_output_degraded(runtime, output, "console_encoding_replace:cp1250")

    last = trace_last(runtime)
    names = [event.event_name for event in last.trace_events]
    assert "live_output_sanitized" in names
