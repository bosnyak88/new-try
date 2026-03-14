import json

from syntaris import cli


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


def test_cli_once_file_missing_is_controlled_and_traceable(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    missing = tmp_path / "missing.log"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once-file", str(missing)])
    assert cli.main() == 2
    err = json.loads(capsys.readouterr().out)
    assert err["error"] == "once_file_read_failed"
    assert "No such file" in err["reason"] or "cannot find" in err["reason"].lower()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztosan látszik ebből?"])
    assert cli.main() == 0
    answer = json.loads(capsys.readouterr().out)
    assert "nincs korábban ténylegesen ingesztált" in answer["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    assert cli.main() == 0
    trace = json.loads(capsys.readouterr().out)
    names = [item["event_name"] for item in trace["trace_events"]]
    assert "once_file_read_failed" in names
