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


def test_cli_talk_once_persists_turn_and_trace(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr(
        "sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"]
    )

    exit_code = cli.main()
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["reply"].startswith("[fallback] Deterministic reply")
    assert output["session_id"] > 0
    assert output["turn_id"] > 0

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    trace_exit_code = cli.main()
    trace_output = json.loads(capsys.readouterr().out)

    assert trace_exit_code == 0
    assert trace_output["turn"]["user_message"] == "szia"
    assert len(trace_output["trace_events"]) >= 1