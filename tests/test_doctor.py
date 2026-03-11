from syntaris.bootstrap.init_app import build_runtime
from syntaris.orchestration.doctor import run_doctor


def test_doctor_healthy_when_paths_exist(tmp_path, monkeypatch):
    server = tmp_path / "llama-server"
    model = tmp_path / "model.gguf"
    server.write_text("bin")
    model.write_text("model")

    monkeypatch.setenv("SYNTARIS_LLM_SERVER_BIN", str(server))
    monkeypatch.setenv("SYNTARIS_LLM_MODEL_PATH", str(model))

    runtime = build_runtime("config/syntaris.example.toml")
    result = run_doctor(runtime)

    assert result.healthy is True


def test_doctor_unhealthy_when_missing_paths(monkeypatch):
    monkeypatch.delenv("SYNTARIS_LLM_SERVER_BIN", raising=False)
    monkeypatch.delenv("SYNTARIS_LLM_MODEL_PATH", raising=False)

    runtime = build_runtime("config/syntaris.example.toml")
    result = run_doctor(runtime)

    assert result.healthy is False
