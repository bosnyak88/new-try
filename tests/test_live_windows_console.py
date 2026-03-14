from syntaris import cli
from syntaris.orchestration.text_normalize import render_console_text


def test_render_console_text_cp1250_degrades_unencodable_arrow():
    result = render_console_text("első → második", encoding="cp1250")

    assert result.degraded is True
    assert result.reason == "console_encoding_replace:cp1250"
    assert "?" in result.text


def test_emit_console_text_does_not_crash_on_cp1250_only_stream(monkeypatch):
    captured: list[str] = []

    class _Stdout:
        encoding = "cp1250"
        buffer = None

        def write(self, s: str):
            s.encode("cp1250")
            captured.append(s)
            return len(s)

        def flush(self):
            return None

    monkeypatch.setattr("sys.stdout", _Stdout())
    degraded, reason = cli._emit_console_text("első → második")

    assert degraded is True
    assert reason == "console_encoding_replace:cp1250"
    assert captured
