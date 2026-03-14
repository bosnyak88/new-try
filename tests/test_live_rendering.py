import json

from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop
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


def test_live_loop_surfaces_non_empty_turn_message(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["szia", "/kilep"])
    turns = [item for item in result.outputs if item.kind in {"turn", "recall", "resume", "structured", "clarification"}]

    assert turns
    assert turns[0].message.strip() != ""


def test_live_loop_empty_turn_reply_degrades_honestly(tmp_path, monkeypatch):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    from syntaris.orchestration import live_loop as module

    monkeypatch.setattr(
        module,
        "_ensure_visible_live_message",
        lambda **_kwargs: ("[degraded-live] teszt", True),
    )

    result = run_live_loop(runtime, ["szia", "/kilep"])
    turn = [item for item in result.outputs if item.kind == "turn"][0]

    assert turn.degraded is True
    assert turn.message.startswith("[degraded-live]")

    trace = trace_last(runtime)
    event_names = [event.event_name for event in trace.trace_events]
    assert "live_surface_degraded" in event_names


def test_live_loop_greeting_first_turn_variants_have_visible_reply(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(
        runtime,
        ["szia", "szia syntaris", "szia syntaris én Árpi vagyok", "/kilep"],
    )
    turns = [item for item in result.outputs if item.kind in {"turn", "recall", "resume", "structured", "clarification"}]

    assert len(turns) == 3
    for turn in turns:
        assert turn.message.strip() != ""
        assert turn.message.strip() != "Rendben."


def test_live_once_semantic_parity_for_intro_prompt(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    from syntaris.orchestration.talk import talk_once
    from syntaris.contracts.runtime import TalkRequest

    once = talk_once(runtime, TalkRequest(message="szia syntaris én Árpi vagyok"))
    live = run_live_loop(runtime, ["szia syntaris én Árpi vagyok", "/kilep"])
    live_turn = [item for item in live.outputs if item.kind in {"turn", "recall", "resume", "structured", "clarification"}][0]

    assert once.turn.assistant_reply.strip() != ""
    assert live_turn.message.strip() != ""
    assert ("Árpi" in once.turn.assistant_reply) == ("Árpi" in live_turn.message)
    assert once.route.action.value == "continue_active"


def test_live_script_json_keeps_rendered_message_non_empty(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["hol tartottunk?", "/kilep"])
    messages = [json.dumps({"kind": item.kind, "message": item.message}) for item in result.outputs]
    parsed = [json.loads(line) for line in messages]
    turn = [item for item in parsed if item["kind"] in {"turn", "recall", "resume", "structured", "clarification"}][0]

    assert turn["message"].strip() != ""
