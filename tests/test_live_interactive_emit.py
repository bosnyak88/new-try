from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop, run_live_loop_interactive
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


def test_run_live_loop_interactive_emits_outputs_via_callback(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    lines = iter(["szia", "/kilep"])
    emitted: list[tuple[str, str]] = []

    result = run_live_loop_interactive(
        runtime,
        input_func=lambda _prompt: next(lines),
        on_output=lambda output: emitted.append((output.kind, output.message)),
    )

    assert emitted
    assert emitted[0][0] in {"turn", "recall", "resume", "structured", "clarification"}
    assert emitted[0][1].strip() != ""
    assert emitted == [(item.kind, item.message) for item in result.outputs]


def test_live_loop_on_output_callback_order_matches_outputs(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    observed: list[str] = []
    result = run_live_loop(runtime, ["szia", "/allapot", "/kilep"], on_output=lambda output: observed.append(output.kind))

    assert observed == [item.kind for item in result.outputs]


def test_emit_live_output_records_attempt_and_success_trace(tmp_path, monkeypatch):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["szia", "/kilep"])
    output = next(item for item in result.outputs if item.kind in {"turn", "recall", "resume", "structured", "clarification"})

    monkeypatch.setattr(cli, "_emit_console_text", lambda _text: (False, None))
    assert cli._emit_live_output(runtime, output) is True

    last = trace_last(runtime)
    names = [event.event_name for event in last.trace_events]
    assert "reply_emit_attempted" in names
    assert "reply_emitted_successfully" in names
    assert "reply_emit_failed" not in names


def test_emit_live_output_records_failure_trace_and_stderr(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["szia", "/kilep"])
    output = next(item for item in result.outputs if item.kind in {"turn", "recall", "resume", "structured", "clarification"})

    def _boom(_text: str):
        raise OSError("tty_write_failed")

    monkeypatch.setattr(cli, "_emit_console_text", _boom)
    assert cli._emit_live_output(runtime, output) is False
    err = capsys.readouterr().err
    assert "live-output-error" in err

    last = trace_last(runtime)
    names = [event.event_name for event in last.trace_events]
    assert "reply_emit_attempted" in names
    assert "reply_emit_failed" in names
