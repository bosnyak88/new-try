import os
import tomli
from pathlib import Path

from syntaris.contracts.runtime import AppConfig, LLMConfig


def _pick(value: str | None, fallback: str) -> str:
    return value if value else fallback


def _pick_int(value: str | None, fallback: int) -> int:
    return int(value) if value else fallback


def load_app_config(config_path: str | None = None) -> AppConfig:
    resolved_path = Path(
        config_path or os.getenv("SYNTARIS_CONFIG_PATH", "config/syntaris.example.toml")
    )

    with resolved_path.open("rb") as handle:
        raw = tomli.load(handle)

    app = raw.get("app", {})
    llm = raw.get("llm", {})
    trace = raw.get("trace", {})

    llm_config = LLMConfig(
        server_bin_path=_pick(os.getenv("SYNTARIS_LLM_SERVER_BIN"), llm.get("server_bin_path", "")),
        model_path=_pick(os.getenv("SYNTARIS_LLM_MODEL_PATH"), llm.get("model_path", "")),
        host=_pick(os.getenv("SYNTARIS_LLM_HOST"), llm.get("host", "127.0.0.1")),
        port=_pick_int(os.getenv("SYNTARIS_LLM_PORT"), llm.get("port", 8080)),
    )

    return AppConfig(
        name=app.get("name", "syntaris"),
        environment=os.getenv("SYNTARIS_ENV", app.get("environment", "development")),
        llm=llm_config,
        trace_enabled=trace.get("enabled", True),
        trace_level=trace.get("level", "info"),
    )
