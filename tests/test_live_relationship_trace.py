import json

from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.live_loop import run_live_loop
from syntaris.orchestration.talk import trace_last


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


def test_live_relationship_trace_is_not_empty_when_relationship_answer_is_explicit(tmp_path):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)
    runtime = build_runtime(config_path=str(config))

    run_live_loop(runtime, ["szia syntaris én Árpi vagyok", "ki vagy te?", "mi a kapcsolatunk?", "/kilep"])
    trace = trace_last(runtime)
    payloads = {event.event_name: json.loads(event.payload) for event in trace.trace_events}

    assert "thread_weave_state_derived" in payloads
    weave = payloads["thread_weave_state_derived"]
    assert weave["query_family"] == "relationship_query"
    assert weave["relation"] != "relation_unknown"
    assert weave["conclusion_status"] != "no_conclusion_established"
    assert weave["applicability_status"] != "applicability_uncertain"
