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
    context_turn_window: int = 5


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
    previous_thread_id: int | None = None
    previous_thread_key: str | None = None
    pending_route: PendingRouteStatusView | None = None


@dataclass(frozen=True)
class TalkRequest:
    message: str
    thread_key: str | None = None
    mode: str | None = None


class RouteDecisionAction(str, Enum):
    CONTINUE_ACTIVE = "continue_active"
    SWITCH_EXISTING = "switch_existing"
    CREATE_AND_SWITCH = "create_and_switch"
    SWITCH_PREVIOUS = "switch_previous"
    PROPOSE_SWITCH_EXISTING = "propose_switch_existing"
    PROPOSE_SWITCH_PREVIOUS = "propose_switch_previous"
    NO_ROUTE_CHANGE = "no_route_change"


class PendingResolutionAction(str, Enum):
    NONE = "none"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PendingRouteProposal:
    held_user_message: str
    proposed_thread_key: str
    current_thread_key: str
    reason: str
    match_pattern: str | None
    source: str
    proposed_at: str


@dataclass(frozen=True)
class PendingRouteStatusView:
    pending_action: str
    pending_thread_key: str
    pending_reason: str
    pending_original_message: str
    match_pattern: str | None
    source: str
    proposed_at: str


@dataclass(frozen=True)
class RouteMatch:
    pattern_name: str
    thread_key: str


@dataclass(frozen=True)
class RouteStateTransition:
    before_thread_id: int
    before_thread_key: str
    before_previous_thread_id: int | None
    before_previous_thread_key: str | None
    after_thread_id: int
    after_thread_key: str
    after_previous_thread_id: int | None
    after_previous_thread_key: str | None


@dataclass(frozen=True)
class RouteDecision:
    action: RouteDecisionAction
    reason: str
    thread_key: str | None = None
    match: RouteMatch | None = None
    created_thread: bool = False
    transition: RouteStateTransition | None = None
    pending_proposal: PendingRouteProposal | None = None
    pending_resolution: PendingResolutionAction = PendingResolutionAction.NONE
    execution_message: str | None = None


@dataclass(frozen=True)
class ThreadSummaryView:
    thread_id: int
    thread_key: str
    turn_count: int
    last_turn_id: int | None
    is_active: bool
    is_previous: bool = False


@dataclass(frozen=True)
class ThreadListView:
    session_id: int
    active_thread_id: int
    active_thread_key: str
    previous_thread_id: int | None
    previous_thread_key: str | None
    threads: list[ThreadSummaryView]


@dataclass(frozen=True)
class ThreadContextTurn:
    turn_id: int
    turn_index: int
    user_message: str
    assistant_reply: str
    backend: str
    degraded: bool


@dataclass(frozen=True)
class ThreadContextPack:
    session_id: int
    thread_id: int
    thread_key: str
    mode: str
    turn_count: int
    last_turn_id: int | None
    recent_turns: list[ThreadContextTurn]
    previous_thread_id: int | None = None
    previous_thread_key: str | None = None


@dataclass(frozen=True)
class ThreadContextRequest:
    source: str
    thread_key: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class ThreadContextView:
    request: ThreadContextRequest
    found: bool
    pack: ThreadContextPack | None


class ContextSource(str, Enum):
    CURRENT = "current"
    PREVIOUS = "previous"
    NAMED = "named"
    EXECUTION_TARGET = "execution_target"


class RecapTarget(str, Enum):
    CURRENT = "current"
    PREVIOUS = "previous"
    NAMED = "named"


@dataclass(frozen=True)
class RecapRequest:
    target: RecapTarget
    thread_key: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class ThreadRecapLine:
    turn_id: int
    turn_index: int
    user_message: str
    assistant_reply: str


@dataclass(frozen=True)
class ThreadRecapView:
    request: RecapRequest
    found: bool
    session_id: int | None
    thread_id: int | None
    thread_key: str | None
    turn_count: int | None
    last_turn_id: int | None
    mode: str | None
    previous_thread_id: int | None
    previous_thread_key: str | None
    recap_lines: list[ThreadRecapLine]
    recap_text: str


class RecapQueryAction(str, Enum):
    NONE = "none"
    CURRENT = "current"
    PREVIOUS = "previous"
    NAMED = "named"


@dataclass(frozen=True)
class RecapQueryMatch:
    action: RecapQueryAction
    thread_key: str | None = None
    pattern_name: str | None = None


@dataclass(frozen=True)
class RecapTrace:
    recognized: bool
    source: str | None = None
    target_thread_key: str | None = None
    context_turn_count: int | None = None
    bypassed_reply_adapter: bool = False


@dataclass(frozen=True)
class ContextLoadResult:
    source: ContextSource
    pack: ThreadContextPack


class LoopAction(str, Enum):
    TURN = "turn"
    STATUS = "status"
    SWITCH_THREAD = "switch_thread"
    SWITCH_MODE = "switch_mode"
    EXIT = "exit"
    INVALID = "invalid"


@dataclass(frozen=True)
class LoopCommand:
    action: LoopAction
    raw_input: str
    value: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class LiveConversationState:
    session_id: int
    thread_id: int
    thread_key: str
    mode: str
    turn_count: int
    last_turn_id: int | None
    previous_thread_id: int | None = None
    previous_thread_key: str | None = None
    pending_route: PendingRouteStatusView | None = None


@dataclass(frozen=True)
class LiveTurnOutput:
    kind: str
    message: str
    state: LiveConversationState
    turn_id: int | None = None
    backend: str | None = None
    degraded: bool | None = None


@dataclass(frozen=True)
class SessionStatusView:
    session_id: int
    thread_id: int
    thread_key: str
    mode: str
    turn_count: int
    last_turn_id: int | None
    previous_thread_id: int | None = None
    previous_thread_key: str | None = None
    pending_route: PendingRouteStatusView | None = None


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
