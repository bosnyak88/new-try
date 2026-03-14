from syntaris.bootstrap.init_app import build_runtime
from syntaris.contracts.runtime import TalkRequest
from syntaris.orchestration.live_loop import run_live_loop
from syntaris.orchestration.talk import talk_once, trace_last


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


def test_once_live_self_intro_semantic_parity(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    once = talk_once(runtime, TalkRequest(message="szia syntaris én Árpi vagyok"))
    live = run_live_loop(runtime, ["szia syntaris én Árpi vagyok", "/kilep"])
    turn = [item for item in live.outputs if item.kind in {"turn", "structured", "recall", "resume", "clarification"}][0]

    assert "Árpi" in once.turn.assistant_reply
    assert "Árpi" in turn.message


def test_live_followup_after_intro_uses_owner_context(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    run_live_loop(runtime, ["szia syntaris", "szia syntaris én Árpi vagyok", "mit tudsz rólam biztosan?", "/kilep"])
    last = trace_last(runtime)

    assert last.turn is not None
    assert "mit tudsz rólam biztosan" in last.turn.user_message.lower()
    assert "Árpi" in last.turn.assistant_reply or "árpi" in last.turn.assistant_reply.lower()
