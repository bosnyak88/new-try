from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop
from syntaris.orchestration.talk import thread_snapshot_current


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


def test_live_relationship_visible_answer_and_retained_state_are_aligned(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    result = run_live_loop(runtime, ["szia syntaris én Árpi vagyok", "ki vagy te?", "mi a kapcsolatunk?", "/kilep"])
    rendered = [item.message for item in result.outputs if item.kind in {"turn", "structured", "recall", "resume", "clarification"}]

    assert any("kapcsolat" in text.lower() for text in rendered)
    assert any("owner" in text.lower() or "árpi" in text.lower() for text in rendered)

    snapshot = thread_snapshot_current(runtime)
    assert snapshot.found and snapshot.snapshot is not None
    assert snapshot.snapshot.thread_weave_state is not None
    weave = snapshot.snapshot.thread_weave_state

    assert weave.relation.value != "relation_unknown"
    assert weave.conclusion_status.value != "no_conclusion_established"
    assert weave.applicability_status.value != "applicability_uncertain"
