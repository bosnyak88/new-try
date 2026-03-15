import json
from pathlib import Path

from syntaris import cli


def _write_config(path: Path, db_path: Path, data_dir: Path):
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
artifact_allowed_roots = ""
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


def test_env_aliases_enable_temp_db_and_allowed_roots_runtime(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    log_path = sandbox / "build_error.log"
    log_path.write_text("Traceback\nRuntimeError: database lock\n", encoding="utf-8")
    config = tmp_path / "syntaris.toml"
    env_db = tmp_path / "runtime_env.db"
    _write_config(config, tmp_path / "cfg.db", tmp_path / "data")

    monkeypatch.setenv("SYNTARIS_DB", str(env_db))
    monkeypatch.setenv("SYNTARIS_SANDBOX_ROOTS", str(sandbox))

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "init-db"])
    assert cli.main() == 0
    init_payload = json.loads(capsys.readouterr().out)
    assert init_payload["db_path"] == str(env_db)

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "artifact-find", "build_error"])
    assert cli.main() == 0
    find_payload = json.loads(capsys.readouterr().out)
    assert str(log_path) in find_payload["matches"]

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "artifact-read", str(log_path)])
    assert cli.main() == 0
    capsys.readouterr()


def test_once_file_evidence_followup_and_historical_reuse(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    config = tmp_path / "syntaris.toml"
    _write_config(config, tmp_path / "runtime.db", tmp_path / "data")
    monkeypatch.setenv("SYNTARIS_SANDBOX_ROOTS", str(sandbox))

    log_path = sandbox / "build_error.log"
    log_path.write_text("Traceback\nRuntimeError: database lock\n", encoding="utf-8")
    plan_path = sandbox / "plan.md"
    plan_path.write_text("# Plan\n- review retry policy\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once-file", str(log_path)])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztosan látszik ebből?"])
    assert cli.main() == 0
    support = json.loads(capsys.readouterr().out)["reply"].lower()
    assert "nincs korábban ténylegesen ingesztált" not in support
    assert "runtimeerror" in support or "database lock" in support

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "ez most raw blokk vagy helyi fájl?"])
    assert cli.main() == 0
    source_kind = json.loads(capsys.readouterr().out)["reply"].lower()
    assert "forrás típusa" in source_kind

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once-file", str(plan_path)])
    assert cli.main() == 0
    capsys.readouterr()

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "miből dolgozol most?"])
    assert cli.main() == 0
    now = json.loads(capsys.readouterr().out)["reply"]
    assert str(plan_path) in now

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--once", "mi biztosan látszik a korábbi logból?"])
    assert cli.main() == 0
    previous = json.loads(capsys.readouterr().out)["reply"].lower()
    assert "runtimeerror" in previous or "database lock" in previous


def test_binary_refusal_inside_allowed_root_reports_supported_reason(tmp_path, monkeypatch, capsys):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    bin_path = sandbox / "sample.bin"
    bin_path.write_bytes(bytes(range(32)))
    config = tmp_path / "syntaris.toml"
    _write_config(config, tmp_path / "runtime.db", tmp_path / "data")
    monkeypatch.setenv("SYNTARIS_SANDBOX_ROOTS", str(sandbox))

    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "artifact-read", str(bin_path)])
    assert cli.main() == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["reason"] in {"unsupported_file_type", "binary_or_non_utf8"}
