import os
from pathlib import Path

import tomli

from syntaris.contracts.runtime import AppConfig, AppPaths, ConversationConfig, LLMConfig, ReplyConfig, TimeConfig


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
    time = raw.get("time", {})

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
        recall_line_limit=_pick_int(
            os.getenv("SYNTARIS_RECALL_LINE_LIMIT"),
            conversation.get("recall_line_limit", 3),
        ),
        recall_prefer_snapshot=(
            os.getenv("SYNTARIS_RECALL_PREFER_SNAPSHOT", str(conversation.get("recall_prefer_snapshot", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        response_followup_enabled=(
            os.getenv("SYNTARIS_RESPONSE_FOLLOWUP_ENABLED", str(conversation.get("response_followup_enabled", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        focus_turn_window=_pick_int(
            os.getenv("SYNTARIS_FOCUS_TURN_WINDOW"),
            conversation.get("focus_turn_window", 8),
        ),
        focus_line_limit=_pick_int(
            os.getenv("SYNTARIS_FOCUS_LINE_LIMIT"),
            conversation.get("focus_line_limit", 4),
        ),
        followup_resolution_enabled=(
            os.getenv("SYNTARIS_FOLLOWUP_RESOLUTION_ENABLED", str(conversation.get("followup_resolution_enabled", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        max_comparison_candidates=_pick_int(
            os.getenv("SYNTARIS_MAX_COMPARISON_CANDIDATES"),
            conversation.get("max_comparison_candidates", 6),
        ),
        clarification_prefer_when_close=(
            os.getenv("SYNTARIS_CLARIFICATION_PREFER_WHEN_CLOSE", str(conversation.get("clarification_prefer_when_close", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        uncertainty_labeling_enabled=(
            os.getenv("SYNTARIS_UNCERTAINTY_LABELING_ENABLED", str(conversation.get("uncertainty_labeling_enabled", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        max_reasoning_units=_pick_int(
            os.getenv("SYNTARIS_MAX_REASONING_UNITS"),
            conversation.get("max_reasoning_units", 4),
        ),
        max_evidence_items_per_unit=_pick_int(
            os.getenv("SYNTARIS_MAX_EVIDENCE_ITEMS_PER_UNIT"),
            conversation.get("max_evidence_items_per_unit", 3),
        ),
        support_labeling_enabled=(
            os.getenv("SYNTARIS_SUPPORT_LABELING_ENABLED", str(conversation.get("support_labeling_enabled", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        synthesis_include_next_step=(
            os.getenv("SYNTARIS_SYNTHESIS_INCLUDE_NEXT_STEP", str(conversation.get("synthesis_include_next_step", True))).lower()
            in {"1", "true", "yes", "on"}
        ),
        scoped_state_short_stale_minutes=_pick_int(
            os.getenv("SYNTARIS_SCOPED_STATE_SHORT_STALE_MINUTES"),
            conversation.get("scoped_state_short_stale_minutes", 120),
        ),
        scoped_state_same_day_stale_minutes=_pick_int(
            os.getenv("SYNTARIS_SCOPED_STATE_SAME_DAY_STALE_MINUTES"),
            conversation.get("scoped_state_same_day_stale_minutes", 480),
        ),
        evidence_chunk_line_limit=_pick_int(
            os.getenv("SYNTARIS_EVIDENCE_CHUNK_LINE_LIMIT"),
            conversation.get("evidence_chunk_line_limit", 24),
        ),
        evidence_max_chunks=_pick_int(
            os.getenv("SYNTARIS_EVIDENCE_MAX_CHUNKS"),
            conversation.get("evidence_max_chunks", 6),
        ),
        evidence_summary_line_limit=_pick_int(
            os.getenv("SYNTARIS_EVIDENCE_SUMMARY_LINE_LIMIT"),
            conversation.get("evidence_summary_line_limit", 5),
        ),
    )

    time_config = TimeConfig(
        timezone=_pick(os.getenv("SYNTARIS_TIMEZONE"), time.get("timezone", "Europe/Budapest")),
    )

    return AppConfig(
        name=app.get("name", "syntaris"),
        environment=os.getenv("SYNTARIS_ENV", app.get("environment", "development")),
        llm=llm_config,
        paths=paths_config,
        reply=reply_config,
        conversation=conversation_config,
        time=time_config,
        trace_enabled=trace.get("enabled", True),
        trace_level=trace.get("level", "info"),
    )
