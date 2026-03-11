from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class LLMConfig:
    server_bin_path: str
    model_path: str
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass(frozen=True)
class AppPaths:
    data_dir: str
    db_path: str


@dataclass(frozen=True)
class ReplyConfig:
    backend: str = "deterministic"
    live_url: str = ""
    live_model: str = ""
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class AppConfig:
    name: str
    environment: str
    llm: LLMConfig
    paths: AppPaths
    reply: ReplyConfig
    trace_enabled: bool = True
    trace_level: str = "info"


@dataclass(frozen=True)
class RuntimeContext:
    config: AppConfig


@dataclass(frozen=True)
class DoctorResult:
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return all(self.checks.values())


@dataclass(frozen=True)
class PersistenceBootstrapResult:
    db_path: str
    schema_initialized: bool


@dataclass(frozen=True)
class SessionRecord:
    session_id: int
    created_at: datetime


@dataclass(frozen=True)
class TurnInput:
    message: str
    session_id: int | None = None


@dataclass(frozen=True)
class TurnResult:
    turn_id: int
    session_id: int
    user_message: str
    assistant_reply: str
    reply_backend: str
    degraded: bool
    created_at: datetime


@dataclass(frozen=True)
class TraceEventRecord:
    trace_id: int
    session_id: int
    turn_id: int
    event_name: str
    backend: str
    degraded: bool
    payload: str
    created_at: datetime


@dataclass(frozen=True)
class LastTurnTraceView:
    turn: TurnResult | None
    trace_events: list[TraceEventRecord]
