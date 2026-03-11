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


def test_cli_talk_script_runs_multi_turn_with_controls(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    script = tmp_path / "loop.txt"
    _write_config(config, db_path, data_dir)
    script.write_text("\n".join([
        "elso",
        "/allapot",
        "/szal munka",
        "masodik",
        "/mod focus",
        "harmadik",
        "/kilep",
    ]), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv", ["syntaris", "--config", str(config), "talk", "--script", str(script)]
    )
    exit_code = cli.main()
    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]

    assert exit_code == 0
    assert [line["kind"] for line in lines] == ["turn", "status", "control", "turn", "control", "turn", "exit"]
    turn_lines = [line for line in lines if line["kind"] == "turn"]
    assert len(turn_lines) == 3
    assert turn_lines[0]["thread_key"] == "default"
    assert turn_lines[1]["thread_key"] == "munka"
    assert turn_lines[2]["mode"] == "focus"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "session-status"])
    cli.main()
    status = json.loads(capsys.readouterr().out)
    assert status["thread_key"] == "munka"
    assert status["mode"] == "focus"
    assert status["turn_count"] == 2

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace_output = json.loads(capsys.readouterr().out)
    event_names = [event["event_name"] for event in trace_output["trace_events"]]
    assert "turn_execution_source" in event_names
