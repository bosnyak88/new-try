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


def test_artifact_read_refuses_outside_root_and_binary(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    cfg = tmp_path / "syntaris.toml"
    _write_config(cfg, db_path, data_dir, sandbox)

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    binary = sandbox / "sample.bin"
    binary.write_bytes(bytes(range(32)))

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-read", str(outside)])
    assert cli.main() == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "artifact_read_refused"

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-read", str(binary)])
    assert cli.main() == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "artifact_read_refused"
