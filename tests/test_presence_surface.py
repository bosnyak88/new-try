from syntaris.bootstrap.init_app import build_runtime
from syntaris.contracts.runtime import TalkRequest
from syntaris.orchestration.live_loop import run_live_loop
from syntaris.orchestration.talk import talk_once


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


def test_live_presence_identity_sequence_remains_visible_and_owner_aware(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    live = run_live_loop(
        runtime,
        [
            "szia syntaris én Árpi vagyok",
            "mit tudsz rólam biztosan?",
            "ki vagy te?",
            "mi a kapcsolatunk?",
            "/kilep",
        ],
    )

    turns = [item.message for item in live.outputs if item.kind in {"turn", "structured", "recall", "resume", "clarification"}]
    assert len(turns) >= 4
    assert all(text.strip() != "Rendben." for text in turns[-4:])
    assert any("Árpi" in text for text in turns)
    assert any("syntaris" in text.lower() for text in turns)
    assert any("kapcsolat" in text.lower() for text in turns)



def test_once_sequence_has_presence_without_owner_system_confusion(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    talk_once(runtime, TalkRequest(message="az én nevem Árpi"))
    talk_once(runtime, TalkRequest(message="a te neved syntaris"))
    talk_once(runtime, TalkRequest(message="én tervezlek és fejlesztelek"))

    who_owner = talk_once(runtime, TalkRequest(message="ki vagyok?"))
    who_system = talk_once(runtime, TalkRequest(message="ki vagy te?"))
    relation = talk_once(runtime, TalkRequest(message="mi a kapcsolatunk?"))

    assert "Árpi" in who_owner.turn.assistant_reply
    assert "Árpi" not in who_system.turn.assistant_reply
    assert "syntaris" in who_system.turn.assistant_reply.lower()
    assert "tervez" in relation.turn.assistant_reply.lower() or "fejleszt" in relation.turn.assistant_reply.lower()
