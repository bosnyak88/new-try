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
context_turn_window = 3

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
    assert status["previous_thread_key"] == "default"

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


def test_cli_natural_routing_thread_list_and_trace_metadata(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    first = json.loads(capsys.readouterr().out)
    assert first["thread_key"] == "work"
    assert first["route"]["action"] == "create_and_switch"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia ott"])
    cli.main()
    second = json.loads(capsys.readouterr().out)
    assert second["thread_key"] == "work"
    assert second["route"]["action"] == "continue_active"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    third = json.loads(capsys.readouterr().out)
    assert third["thread_key"] == "default"
    assert third["route"]["action"] == "switch_existing"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-list"])
    cli.main()
    listing = json.loads(capsys.readouterr().out)
    keys = [item["thread_key"] for item in listing["threads"]]
    assert keys == ["default", "work"]
    assert listing["active_thread_key"] == "default"
    assert listing["previous_thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace_output = json.loads(capsys.readouterr().out)
    route_event = next(event for event in trace_output["trace_events"] if event["event_name"] == "route_decision_computed")
    assert '"action": "switch_existing"' in route_event["payload"]


def test_explicit_thread_override_beats_inferred_routing(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work", "--thread", "manual"])
    cli.main()
    out = json.loads(capsys.readouterr().out)

    assert out["thread_key"] == "manual"
    assert out["route"]["reason"] == "explicit_thread_override"


def test_previous_thread_and_topic_shift_phrases(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új téma: admin"])
    cli.main()
    first = json.loads(capsys.readouterr().out)
    assert first["thread_key"] == "admin"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza az előző szálra"])
    cli.main()
    second = json.loads(capsys.readouterr().out)
    assert second["thread_key"] == "default"
    assert second["route"]["action"] == "switch_previous"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "térjünk vissza az előző témára"])
    cli.main()
    third = json.loads(capsys.readouterr().out)
    assert third["thread_key"] == "admin"
    assert third["route"]["action"] == "switch_previous"


def test_cli_pending_route_confirm_and_reject(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk a worköt"])
    cli.main()
    proposed = json.loads(capsys.readouterr().out)
    assert proposed["route"]["action"] == "propose_switch_existing"
    assert "váltsak" in proposed["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "session-status"])
    cli.main()
    status = json.loads(capsys.readouterr().out)
    assert status["pending_route"]["pending_thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "igen"])
    cli.main()
    confirmed = json.loads(capsys.readouterr().out)
    assert confirmed["thread_key"] == "work"
    assert confirmed["route"]["pending_resolution"] == "confirmed"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk a worköt"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "nem"])
    cli.main()
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["thread_key"] == "default"
    assert rejected["route"]["pending_resolution"] == "rejected"


def test_cli_pending_cancel_and_trace(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk a worköt"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "valami más"])
    cli.main()
    out = json.loads(capsys.readouterr().out)
    assert out["route"]["pending_resolution"] == "cancelled"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in trace["trace_events"]]
    assert "pending_route_cancelled" in names


def test_cli_previous_suggestive_pending_confirm_reject(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk az előzőt"])
    cli.main()
    proposed = json.loads(capsys.readouterr().out)
    assert proposed["route"]["action"] == "propose_switch_previous"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "session-status"])
    cli.main()
    status = json.loads(capsys.readouterr().out)
    assert status["pending_route"] is not None
    assert status["pending_route"]["pending_thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "igen"])
    cli.main()
    confirmed = json.loads(capsys.readouterr().out)
    assert confirmed["thread_key"] == "work"
    assert confirmed["route"]["pending_resolution"] == "confirmed"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk az előzőt"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "nem"])
    cli.main()
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["thread_key"] == "default"
    assert rejected["route"]["pending_resolution"] == "rejected"


def test_cli_script_bom_safe_pending(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    script = tmp_path / "bom-script.txt"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    script.write_text("﻿folytassuk az előzőt\nigen\n/kilep\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--script", str(script)])
    assert cli.main() == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    turns = [line for line in lines if line["kind"] == "turn"]
    assert turns[0]["message"].startswith("A(z) work")
    assert turns[1]["thread_key"] == "work"


def test_cli_thread_view_current_previous_named_and_missing(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "elso"]) 
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "masodik"]) 
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "harmadik"]) 
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"]) 
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-view", "--current"])
    cli.main()
    current = json.loads(capsys.readouterr().out)
    assert current["found"] is True
    assert current["pack"]["thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-view", "--previous"])
    cli.main()
    previous = json.loads(capsys.readouterr().out)
    assert previous["found"] is True
    assert previous["pack"]["thread_key"] == "default"
    assert len(previous["pack"]["recent_turns"]) == 3

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-view", "default", "--limit", "2"])
    cli.main()
    named = json.loads(capsys.readouterr().out)
    assert named["found"] is True
    assert named["pack"]["thread_key"] == "default"
    assert len(named["pack"]["recent_turns"]) == 2

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-view", "missing"])
    cli.main()
    missing = json.loads(capsys.readouterr().out)
    assert missing["found"] is False
    assert missing["pack"] is None


def test_thread_context_loaded_trace_for_once_and_script(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    script = tmp_path / "loop.txt"
    _write_config(config, db_path, data_dir)
    script.write_text("elso\n/kilep\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    once_trace = json.loads(capsys.readouterr().out)
    once_context = next(event for event in once_trace["trace_events"] if event["event_name"] == "thread_context_loaded")
    assert '"source": "execution_target"' in once_context["payload"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--script", str(script)])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    script_trace = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in script_trace["trace_events"]]
    assert "thread_context_loaded" in names
    source_event = next(event for event in script_trace["trace_events"] if event["event_name"] == "turn_execution_source")
    assert '"source": "talk_live"' in source_event["payload"]


def test_cli_thread_view_previous_missing(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-view", "--previous"])
    exit_code = cli.main()
    out = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert out["found"] is False


def test_cli_thread_recap_current_previous_named(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-recap", "--current"])
    cli.main()
    current = json.loads(capsys.readouterr().out)
    assert current["found"] is True
    assert current["thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-recap", "--previous"])
    cli.main()
    previous = json.loads(capsys.readouterr().out)
    assert previous["found"] is True
    assert previous["thread_key"] == "default"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-recap", "work"])
    cli.main()
    named = json.loads(capsys.readouterr().out)
    assert named["found"] is True
    assert named["thread_key"] == "work"


def test_cli_recall_queries_and_trace_metadata(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"])
    cli.main()
    first = json.loads(capsys.readouterr().out)
    base_thread = first["thread_key"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hol tartottunk?"])
    cli.main()
    current = json.loads(capsys.readouterr().out)
    assert current["kind"] == "recall"
    assert "Röviden itt tartottunk:" in current["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "a work szálon mi volt?"])
    cli.main()
    named = json.loads(capsys.readouterr().out)
    assert named["kind"] == "recall"
    assert "#" in named["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "az előző szálon mi volt?"])
    cli.main()
    previous = json.loads(capsys.readouterr().out)
    assert previous["kind"] == "recall"
    assert base_thread in previous["reply"] or "Röviden" in previous["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "session-status"])
    cli.main()
    status = json.loads(capsys.readouterr().out)
    assert status["thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    event_names = [event["event_name"] for event in trace["trace_events"]]
    assert "turn_interpreted" in event_names
    assert "recall_resolved" in event_names
    assert "response_plan_built" in event_names


def test_cli_thread_recap_missing_targets(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-recap", "--previous"])
    cli.main()
    previous = json.loads(capsys.readouterr().out)
    assert previous["found"] is False

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-recap", "missing"])
    cli.main()
    missing = json.loads(capsys.readouterr().out)
    assert missing["found"] is False


def test_cli_thread_snapshot_current_previous_named_and_refresh(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "első"]) 
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hol tartottunk?"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-snapshot", "--current"])
    cli.main()
    current = json.loads(capsys.readouterr().out)
    assert current["found"] is True
    assert current["snapshot"]["thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-snapshot", "--previous"])
    cli.main()
    previous = json.loads(capsys.readouterr().out)
    assert previous["found"] is True
    assert previous["snapshot"]["thread_key"] == "default"
    assert previous["snapshot"]["source_metadata"]["filtered_recap_turn_count"] >= 0

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-snapshot", "work", "--refresh"])
    cli.main()
    named = json.loads(capsys.readouterr().out)
    assert named["found"] is True
    assert named["snapshot"]["thread_key"] == "work"
    assert named["request"]["refresh"] is True


def test_cli_thread_snapshot_missing_targets_and_trace_metadata(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-snapshot", "--previous"])
    cli.main()
    previous = json.loads(capsys.readouterr().out)
    assert previous["found"] is False

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-snapshot", "missing"])
    cli.main()
    missing = json.loads(capsys.readouterr().out)
    assert missing["found"] is False

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in trace["trace_events"]]
    assert "thread_snapshot_refreshed" in names


def test_cli_resume_named_and_ambiguous_clarification(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "work állapot"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "a work szálat hozd vissza"])
    cli.main()
    named = json.loads(capsys.readouterr().out)
    assert named["kind"] == "resume"
    assert "work szálat" in named["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "folytassuk onnan"])
    cli.main()
    ambiguous = json.loads(capsys.readouterr().out)
    assert ambiguous["kind"] == "clarification"
    assert "Nem egyértelmű" in ambiguous["reply"]


def test_cli_thread_focus_current_previous_named(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "migráció terv"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-focus", "--current"])
    assert cli.main() == 0
    current = json.loads(capsys.readouterr().out)
    assert current["found"] is True

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-focus", "--previous"])
    assert cli.main() == 0
    previous = json.loads(capsys.readouterr().out)
    assert previous["found"] is True
    assert previous["focus"]["thread_key"] == "work"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "thread-focus", "work"])
    assert cli.main() == 0
    named = json.loads(capsys.readouterr().out)
    assert named["found"] is True
    assert named["focus"]["thread_key"] == "work"


def test_cli_followup_resolution_and_trace_metadata(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "projektterv"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "erről beszéljünk tovább"])
    cli.main()
    out = json.loads(capsys.readouterr().out)
    assert "innen folytatjuk" in out["reply"].lower()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in trace["trace_events"]]
    assert "thread_focus_loaded" in names
    assert "followup_reference_resolved" in names


def test_cli_followup_ambiguous_without_focus_clarifies(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "és abból mi következik?"])
    cli.main()
    out = json.loads(capsys.readouterr().out)
    assert out["kind"] == "clarification"
    assert "mire utalsz" in out["reply"].lower()

def test_cli_deliberation_comparison_and_strategy_trace(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: munka"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr(
        "sys.argv",
        ["syntaris", "--config", str(config), "talk", "--once", "nem erre gondoltam, hanem az előző szálra"],
    )
    cli.main()
    correction = json.loads(capsys.readouterr().out)
    assert correction["kind"] == "correction_redirect"

    monkeypatch.setattr(
        "sys.argv",
        ["syntaris", "--config", str(config), "talk", "--once", "várj, a másik részre térjünk vissza"],
    )
    cli.main()
    clarify = json.loads(capsys.readouterr().out)
    assert clarify["kind"] == "clarification"

    monkeypatch.setattr(
        "sys.argv",
        ["syntaris", "--config", str(config), "talk", "--once", "mi a lényeg és mi legyen a következő?"],
    )
    cli.main()
    structured = json.loads(capsys.readouterr().out)
    assert structured["kind"] == "structured"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "nem ezt kérdeztem"])
    cli.main()
    redirect = json.loads(capsys.readouterr().out)
    assert redirect["kind"] in {"correction_redirect", "clarification"}

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace_output = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in trace_output["trace_events"]]
    assert "comparison_pack_built" in names
    assert "answer_strategy_selected" in names

def test_cli_rebuild014_runtime_behaviors_no_fallback_and_compare_precedence(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztos ebben és mi csak feltételezés?"])
    cli.main()
    support = json.loads(capsys.readouterr().out)
    assert support["degraded"] is False
    assert support["reply"].strip() != "Rendben."
    assert "[fallback]" not in support["reply"]
    assert "Ami biztos" in support["reply"]
    assert "Ami nyitott" in support["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi a fő probléma és mit kell most tenni?"])
    cli.main()
    diagnose = json.loads(capsys.readouterr().out)
    assert diagnose["degraded"] is False
    assert diagnose["reply"].strip() != "Rendben."
    assert "[fallback]" not in diagnose["reply"]
    assert "Mi a fő probléma?" in diagnose["reply"]
    assert "Következő lépés" in diagnose["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hasonlítsd össze a mostanit az előző szállal"])
    cli.main()
    compare = json.loads(capsys.readouterr().out)
    assert compare["kind"] != "correction_redirect"
    assert compare["degraded"] is False
    assert compare["reply"].strip() != "Rendben."
    assert "[fallback]" not in compare["reply"]
    assert "Mostani szál:" in compare["reply"]
    assert "Előző szál:" in compare["reply"]
    assert "nincs stabil előzmény" not in compare["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in trace["trace_events"]]
    assert "objective_framed" in names
    assert "decomposition_built" in names
    assert "evidence_pack_built" in names
    assert "synthesis_plan_built" in names


def test_cli_previous_thread_recall_not_generic_ack(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "az előző szálon mi volt?"])
    cli.main()
    out = json.loads(capsys.readouterr().out)

    assert out["degraded"] is False
    assert out["reply"].strip() != "Rendben."
    assert "[fallback]" not in out["reply"]
    assert "Röviden itt tartottunk" in out["reply"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    payload_by_event = {event["event_name"]: event["payload"] for event in trace["trace_events"]}
    assert "turn_interpreted" in payload_by_event
    assert '"kind": "recall_previous"' in payload_by_event["turn_interpreted"]
    assert "response_plan_built" in payload_by_event
    assert '"kind": "recall"' in payload_by_event["response_plan_built"]


def test_cli_compare_trace_is_not_direct_fallback(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hasonlítsd össze a mostanit az előző szállal"])
    cli.main()
    out = json.loads(capsys.readouterr().out)
    assert out["reply"].strip() != "Rendben."

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    trace = json.loads(capsys.readouterr().out)
    payload_by_event = {event["event_name"]: event["payload"] for event in trace["trace_events"]}
    assert '"kind": "compare_previous"' in payload_by_event["turn_interpreted"]
    assert '"selected_strategy": "structured_answer"' in payload_by_event["answer_strategy_selected"]
    assert '"kind": "structured"' in payload_by_event["response_plan_built"]


def test_cli_previous_recall_and_compare_mojibake_forms(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "az elÅzÅ szÃ¡lon mi volt?"])
    cli.main()
    recall = json.loads(capsys.readouterr().out)
    assert recall["reply"].strip() != "Rendben."
    assert recall["kind"] == "recall"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hasonlÃ­tsd Ã¶ssze a mostanit az elÅzÅ szÃ¡llal"])
    cli.main()
    compare = json.loads(capsys.readouterr().out)
    assert compare["reply"].strip() != "Rendben."
    assert compare["kind"] == "structured"
    assert "Mostani szál:" in compare["reply"]
    assert "Előző szál:" in compare["reply"]


def test_cli_explicit_previous_recall_and_compare_clean_forms_trace_path(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "új szál: work"])
    cli.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "vissza a default szálra"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "az előző szálon mi volt?"])
    cli.main()
    recall = json.loads(capsys.readouterr().out)
    assert recall["kind"] == "recall"
    assert recall["reply"].strip() != "Rendben."

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    recall_trace = json.loads(capsys.readouterr().out)
    recall_payload = {event["event_name"]: event["payload"] for event in recall_trace["trace_events"]}
    assert '"kind": "recall_previous"' in recall_payload["turn_interpreted"]
    assert '"requested": true' in recall_payload["recall_resolved"]
    assert '"kind": "recall"' in recall_payload["response_plan_built"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hasonlítsd össze a mostanit az előző szállal"])
    cli.main()
    compare = json.loads(capsys.readouterr().out)
    assert compare["kind"] == "structured"
    assert compare["reply"].strip() != "Rendben."

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    cli.main()
    compare_trace = json.loads(capsys.readouterr().out)
    compare_payload = {event["event_name"]: event["payload"] for event in compare_trace["trace_events"]}
    assert '"kind": "compare_previous"' in compare_payload["turn_interpreted"]
    assert '"selected_strategy": "structured_answer"' in compare_payload["answer_strategy_selected"]
    assert '"kind": "structured"' in compare_payload["response_plan_built"]


def test_cli_hol_tartottunk_remains_meaningful_recall(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "szia"])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "hol tartottunk?"])
    cli.main()
    recall = json.loads(capsys.readouterr().out)
    assert recall["kind"] == "recall"
    assert recall["reply"].strip() != "Rendben."
    assert "Röviden itt tartottunk" in recall["reply"]
