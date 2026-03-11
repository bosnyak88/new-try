from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ModeKind(str, Enum):
    CHAT = "chat"


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
class ConversationConfig:
    default_thread_key: str = "default"
    default_mode: str = ModeKind.CHAT.value


@dataclass(frozen=True)
class AppConfig:
    name: str
    environment: str
    llm: LLMConfig
    paths: AppPaths
    reply: ReplyConfig
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
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
    schema_version: int


@dataclass(frozen=True)
class SessionRecord:
    session_id: int
    created_at: datetime


@dataclass(frozen=True)
class ThreadRecord:
    thread_id: int
    session_id: int
    thread_key: str
    created_at: datetime


@dataclass(frozen=True)
class ActiveConversationState:
    session_id: int
    thread_id: int
    thread_key: str
    mode: str
    turn_count: int
    last_turn_id: int | None = None


@dataclass(frozen=True)
class TalkRequest:
    message: str
    thread_key: str | None = None
    mode: str | None = None


@dataclass(frozen=True)
class TurnInput:
    message: str
    session_id: int
    thread_id: int
    mode: str


@dataclass(frozen=True)
class TurnResult:
    turn_id: int
    session_id: int
    thread_id: int
    thread_key: str
    mode: str
    turn_index: int
    user_message: str
    assistant_reply: str
    reply_backend: str
    degraded: bool
    created_at: datetime


@dataclass(frozen=True)
class TraceEventRecord:
    trace_id: int
    session_id: int
    thread_id: int
    turn_id: int
    mode: str
    event_name: str
    backend: str
    degraded: bool
    payload: str
    created_at: datetime


@dataclass(frozen=True)
class LastTurnTraceView:
    turn: TurnResult | None
    trace_events: list[TraceEventRecord]
