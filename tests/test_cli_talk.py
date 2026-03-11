import json

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


def test_cli_talk_once_reuses_active_state_and_supports_thread_and_mode(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr(
        "sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"]
    )
    exit_code = cli.main()
    first = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert first["session_id"] > 0
    assert first["thread_key"] == "default"
    assert first["mode"] == "chat"

    monkeypatch.setattr(
        "sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk"]
    )
    cli.main()
    second = json.loads(capsys.readouterr().out)

    assert second["session_id"] == first["session_id"]
    assert second["thread_id"] == first["thread_id"]

    monkeypatch.setattr(
        "sys.argv",
        ["syntaris", "--config", str(config), "talk", "--once", "munka", "--thread", "work", "--mode", "chat"],
    )
    cli.main()
    third = json.loads(capsys.readouterr().out)

    assert third["session_id"] == first["session_id"]
    assert third["thread_key"] == "work"
    assert third["thread_id"] != first["thread_id"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "session-status"])
    cli.main()
    status = json.loads(capsys.readouterr().out)

    assert status["session_id"] == first["session_id"]
    assert status["thread_key"] == "work"
    assert status["mode"] == "chat"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    trace_exit_code = cli.main()
    trace_output = json.loads(capsys.readouterr().out)

    assert trace_exit_code == 0
    assert trace_output["turn"]["thread_key"] == "work"
    assert trace_output["turn"]["mode"] == "chat"
    assert trace_output["turn"]["backend"] == "deterministic"
    assert isinstance(trace_output["turn"]["degraded"], bool)
