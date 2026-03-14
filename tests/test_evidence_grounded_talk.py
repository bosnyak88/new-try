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
context_turn_window = 5
evidence_chunk_line_limit = 8
evidence_max_chunks = 4
evidence_summary_line_limit = 4

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


def test_talk_reuses_ingested_evidence_for_grounded_question(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    log_text = """Traceback (most recent call last):
  File \"src/syntaris/orchestration/turns.py\", line 351, in execute_turn
    raise ValueError('bad config')
ValueError: bad config
WARNING: fallback path selected
exit code 1"""

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", log_text])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztosan látszik ebből?"])
    assert cli.main() == 0
    answer = json.loads(capsys.readouterr().out)
    assert "Közvetlenül látszik" in answer["reply"]
    assert "Traceback" in answer["reply"] or "ValueError" in answer["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi benne a valódi hiba?"])
    assert cli.main() == 0
    second = json.loads(capsys.readouterr().out)
    assert "Közvetlenül látszik" in second["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "a korábbi konzolból mi derült ki?"])
    assert cli.main() == 0
    recalled = json.loads(capsys.readouterr().out)
    assert "forrás" in recalled["reply"].lower() or "Traceback" in recalled["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    assert cli.main() == 0
    trace = json.loads(capsys.readouterr().out)
    event = next(evt for evt in trace["trace_events"] if evt["event_name"] == "evidence_pack_built")
    assert '"ingest_status": "raw_text_evidence"' in event["payload"]


def test_evidence_query_without_ingest_is_honest_not_filler(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi benne a valódi hiba?"])
    assert cli.main() == 0
    answer = json.loads(capsys.readouterr().out)
    assert "nincs korábban ténylegesen ingesztált" in answer["reply"]
    assert answer["reply"].strip() != "Rendben."


def test_ingest_intent_message_is_acknowledged(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "bemásolok egy hosszabb konzolkimenetet"])
    assert cli.main() == 0
    answer = json.loads(capsys.readouterr().out)
    assert "várom a nyers forrásblokkot" in answer["reply"].lower()
