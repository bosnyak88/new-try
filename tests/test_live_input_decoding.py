import json

from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.text_normalize import decode_live_input_line
from syntaris import cli


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


def test_decode_live_input_line_repairs_mojibake_hungarian_text():
    raw = "szia syntaris én Árpi vagyok\n".encode("utf-8").decode("latin1").encode("utf-8")
    result = decode_live_input_line(raw, preferred_encoding="cp1250")

    assert "Árpi" in result.text
    assert result.repaired is True


def test_cli_live_pipeline_records_input_repair_trace(tmp_path, monkeypatch, capsys):
    config = tmp_path / "syntaris.toml"
    data_dir = tmp_path / "data"
    db_path = data_dir / "runtime.db"
    _write_config(config, db_path, data_dir)

    class _FakeBuffer:
        def __init__(self, chunks):
            self._chunks = chunks
            self._idx = 0

        def readline(self):
            if self._idx >= len(self._chunks):
                return b""
            c = self._chunks[self._idx]
            self._idx += 1
            return c

    class _FakeStdin:
        def __init__(self, chunks):
            self.buffer = _FakeBuffer(chunks)
            self.encoding = "cp1250"

        def isatty(self):
            return False

    live_bytes = ["szia syntaris én Árpi vagyok\n".encode("utf-8").decode("latin1").encode("utf-8")]

    monkeypatch.setattr("sys.stdin", _FakeStdin(live_bytes))
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "talk", "--live"])
    assert cli.main() == 0
    capsys.readouterr()

    runtime = build_runtime(config_path=str(config))
    monkeypatch.setattr("sys.argv", ["syntaris", "--config", str(config), "trace-last"])
    assert cli.main() == 0
    trace = json.loads(capsys.readouterr().out)
    names = [event["event_name"] for event in trace["trace_events"]]
    assert "live_input_repaired" in names
