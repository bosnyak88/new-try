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


def test_artifact_registry_from_once_file_and_local_read(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    cfg = tmp_path / "syntaris.toml"
    _write_config(cfg, db_path, data_dir, sandbox)

    file_path = sandbox / "build_error.log"
    file_path.write_text("Traceback\nRuntimeError: lock\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "talk", "--once-file", str(file_path)])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-list", "--current"])
    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifacts"]
    assert any(item["source_kind"] == "once_file_import" for item in payload["artifacts"])

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-read", str(file_path)])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-list", "--current"])
    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(item["source_kind"] == "local_text_file" for item in payload["artifacts"])
