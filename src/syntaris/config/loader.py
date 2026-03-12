import os
from pathlib import Path

import tomli

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig


def _pick(value: str | None, fallback: str) -> str:
    return value if value else fallback


def _pick_int(value: str | None, fallback: int) -> int:
    return int(value) if value else fallback


def _pick_float(value: str | None, fallback: float) -> float:
    return float(value) if value else fallback


def load_app_config(config_path: str | None = None) -> AppConfig:
    resolved_path = Path(
        config_path or os.getenv("SYNTARIS_CONFIG_PATH", "config/syntaris.example.toml")
    )

    with resolved_path.open("rb") as handle:
        raw = tomli.load(handle)

    app = raw.get("app", {})
    llm = raw.get("llm", {})
    trace = raw.get("trace", {})
    paths = raw.get("paths", {})
    reply = raw.get("reply", {})
    conversation = raw.get("conversation", {})

    llm_config = LLMConfig(
        server_bin_path=_pick(os.getenv("SYNTARIS_LLM_SERVER_BIN"), llm.get("server_bin_path", "")),
        model_path=_pick(os.getenv("SYNTARIS_LLM_MODEL_PATH"), llm.get("model_path", "")),
        host=_pick(os.getenv("SYNTARIS_LLM_HOST"), llm.get("host", "127.0.0.1")),
        port=_pick_int(os.getenv("SYNTARIS_LLM_PORT"), llm.get("port", 8080)),
    )

    paths_config = AppPaths(
        data_dir=_pick(os.getenv("SYNTARIS_DATA_DIR"), paths.get("data_dir", "./.syntaris")),
        db_path=_pick(os.getenv("SYNTARIS_DB_PATH"), paths.get("db_path", "./.syntaris/runtime.db")),
    )

    reply_config = ReplyConfig(
        backend=_pick(os.getenv("SYNTARIS_REPLY_BACKEND"), reply.get("backend", "deterministic")),
        live_url=_pick(os.getenv("SYNTARIS_REPLY_LIVE_URL"), reply.get("live_url", "")),
        live_model=_pick(os.getenv("SYNTARIS_REPLY_LIVE_MODEL"), reply.get("live_model", "")),
        timeout_seconds=_pick_float(
            os.getenv("SYNTARIS_REPLY_TIMEOUT_SECONDS"), reply.get("timeout_seconds", 10.0)
        ),
    )

    conversation_config = ConversationConfig(
        default_thread_key=_pick(
            os.getenv("SYNTARIS_DEFAULT_THREAD_KEY"), conversation.get("default_thread_key", "default")
        ),
        default_mode=_pick(os.getenv("SYNTARIS_DEFAULT_MODE"), conversation.get("default_mode", "chat")),
        context_turn_window=_pick_int(
            os.getenv("SYNTARIS_CONTEXT_TURN_WINDOW"),
            conversation.get("context_turn_window", 5),
        ),
        snapshot_turn_window=_pick_int(
            os.getenv("SYNTARIS_SNAPSHOT_TURN_WINDOW"),
            conversation.get("snapshot_turn_window", 8),
        ),
        snapshot_include_recap_turns=(
            os.getenv("SYNTARIS_SNAPSHOT_INCLUDE_RECAP_TURNS", str(conversation.get("snapshot_include_recap_turns", False))).lower()
            in {"1", "true", "yes", "on"}
        ),
        snapshot_include_pending_turns=(
            os.getenv("SYNTARIS_SNAPSHOT_INCLUDE_PENDING_TURNS", str(conversation.get("snapshot_include_pending_turns", False))).lower()
            in {"1", "true", "yes", "on"}
        ),
    )

    return AppConfig(
        name=app.get("name", "syntaris"),
        environment=os.getenv("SYNTARIS_ENV", app.get("environment", "development")),
        llm=llm_config,
        paths=paths_config,
        reply=reply_config,
        conversation=conversation_config,
        trace_enabled=trace.get("enabled", True),
        trace_level=trace.get("level", "info"),
    )
