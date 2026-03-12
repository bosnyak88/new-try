from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import parse_loop_command, run_live_loop
from syntaris.orchestration.talk import trace_last


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


def test_parse_loop_commands():
    assert parse_loop_command("hello").action.value == "turn"
    assert parse_loop_command("/allapot").action.value == "status"
    assert parse_loop_command("/status").action.value == "status"
    assert parse_loop_command("/szal munka").action.value == "switch_thread"
    assert parse_loop_command("/thread munka").action.value == "switch_thread"
    assert parse_loop_command("/mod focus").action.value == "switch_mode"
    assert parse_loop_command("/mode focus").action.value == "switch_mode"
    assert parse_loop_command("/kilep").action.value == "exit"


def test_live_loop_controls_not_persisted_as_turns(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["elso", "/allapot", "/mod focus", "/szal munka", "masodik", "/kilep"])

    kinds = [item.kind for item in result.outputs]
    assert kinds == ["turn", "status", "control", "control", "turn", "exit"]

    last = trace_last(runtime)
    assert last.turn is not None
    assert last.turn.user_message == "masodik"
    assert last.turn.thread_key == "munka"
    assert last.turn.mode == "focus"


def test_live_loop_natural_routing_and_slash_precedence(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["más téma: work", "/szal manual", "vissza az előző szálra", "/kilep"])
    turns = [item for item in result.outputs if item.kind == "turn"]
    assert turns[0].state.thread_key == "work"
    assert turns[1].state.thread_key == "work"

    controls = [item for item in result.outputs if item.kind == "control"]
    assert len(controls) == 1
    assert '"thread_key": "manual"' in controls[0].message


def test_live_loop_pending_resolution(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["új szál: work", "vissza a default szálra", "folytassuk a worköt", "igen", "/kilep"])
    turns = [item for item in result.outputs if item.kind == "turn"]
    assert turns[2].message.startswith("A(z) work")
    assert turns[3].state.thread_key == "work"


def test_live_loop_recap_kind_uses_shared_turn_path(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["szia", "hol tartunk?", "/kilep"])
    turns = [item for item in result.outputs if item.kind in {"turn", "recap"}]
    assert turns[0].kind == "turn"
    assert turns[1].kind == "recap"
    assert "Szál recap:" in turns[1].message
