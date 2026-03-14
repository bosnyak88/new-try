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


def test_old_evidence_requires_explicit_recall_wording(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    old_log = """Traceback (most recent call last):
  File "src/syntaris/orchestration/turns.py", line 1, in demo
    raise ValueError("HISTORICAL_LOG")
ValueError: HISTORICAL_LOG
WARNING: fallback path selected
exit code 1"""
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", old_log])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztosan látszik ebből?"])
    assert cli.main() == 0
    implicit = json.loads(capsys.readouterr().out)
    assert "nincs korábban ténylegesen ingesztált" in implicit["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "a korábbi konzolból mi derült ki?"])
    assert cli.main() == 0
    explicit = json.loads(capsys.readouterr().out)
    assert "HISTORICAL_LOG" in explicit["reply"] or "korábbi konzolból" in explicit["reply"].lower()
