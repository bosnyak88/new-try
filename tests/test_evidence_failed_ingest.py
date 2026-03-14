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


def test_failed_once_file_does_not_silently_substitute_old_evidence(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    old_log = """Traceback\nValueError: OLD_EVIDENCE\nexit code 1"""

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", old_log])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "bemásolok egy hosszabb konzolkimenetet"])
    assert cli.main() == 0
    capsys.readouterr()

    missing = tmp_path / "new_missing.log"
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once-file", str(missing)])
    assert cli.main() == 2
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztosan látszik ebből?"])
    assert cli.main() == 0
    support = json.loads(capsys.readouterr().out)
    assert "nincs korábban ténylegesen ingesztált" in support["reply"]
    assert "OLD_EVIDENCE" not in support["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi csak következtetés?"])
    assert cli.main() == 0
    inference = json.loads(capsys.readouterr().out)
    assert "nincs korábban ténylegesen ingesztált" in inference["reply"]
    assert "OLD_EVIDENCE" not in inference["reply"]
