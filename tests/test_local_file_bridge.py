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


def test_artifact_find_and_show(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    f = sandbox / "build_error.log"
    f.write_text("error", encoding="utf-8")
    cfg = tmp_path / "syntaris.toml"
    _write_config(cfg, tmp_path / "data" / "runtime.db", tmp_path / "data", sandbox)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-find", "build_error"])
    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["matches"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-read", str(f)])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(cfg), "artifact-show", "--last"])
    assert cli.main() == 0
    show = json.loads(capsys.readouterr().out)
    assert show["source_kind"] == "local_text_file"
