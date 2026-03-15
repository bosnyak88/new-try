import json

from syntaris import cli


def _write_config(path, db_path, data_dir, allowed_root):
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
artifact_allowed_roots = "{allowed_root.as_posix()}"
artifact_max_read_bytes = 262144
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


def test_source_awareness_after_artifact_read(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    logf = sandbox / "a.log"
    logf.write_text("Traceback\nRuntimeError: lock\n", encoding="utf-8")
    cfg = tmp_path / "syntaris.toml"
    _write_config(cfg, tmp_path / "data" / "runtime.db", tmp_path / "data", sandbox)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-read", str(logf)])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "talk", "--once", "miből dolgozol most?"])
    assert cli.main() == 0
    reply = json.loads(capsys.readouterr().out)["reply"].lower()
    assert "dolgozom" in reply and "forrás" in reply or "artifactból" in reply
