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
    snapshot_turn_window: int = 8
    snapshot_include_recap_turns: bool = False
    snapshot_include_pending_turns: bool = False
    recall_line_limit: int = 3
    recall_prefer_snapshot: bool = True
    response_followup_enabled: bool = True
    focus_turn_window: int = 8
    focus_line_limit: int = 4
    followup_resolution_enabled: bool = True
    max_comparison_candidates: int = 6
    clarification_prefer_when_close: bool = True
    uncertainty_labeling_enabled: bool = True


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


class SnapshotTarget(str, Enum):
    CURRENT = "current"
    PREVIOUS = "previous"
    NAMED = "named"


@dataclass(frozen=True)
class ThreadSnapshotRequest:
    target: SnapshotTarget
    thread_key: str | None = None
    limit: int | None = None
    refresh: bool = False
    source: str = "unspecified"


@dataclass(frozen=True)
class ThreadSnapshotLine:
    turn_id: int
    turn_index: int
    user_message: str
    assistant_reply: str


@dataclass(frozen=True)
class SnapshotSourceMetadata:
    source_turn_count: int
    included_turn_count: int
    filtered_recap_turn_count: int
    filtered_pending_turn_count: int
    filtered_control_turn_count: int


@dataclass(frozen=True)
class ThreadSnapshotPack:
    session_id: int
    thread_id: int
    thread_key: str
    mode: str
    turn_count: int
    last_turn_id: int | None
    snapshot_built_at: datetime
    source_metadata: SnapshotSourceMetadata
    snapshot_lines: list[ThreadSnapshotLine]
    snapshot_text: str
    previous_thread_id: int | None = None
    previous_thread_key: str | None = None


@dataclass(frozen=True)
class ThreadSnapshotView:
    request: ThreadSnapshotRequest
    found: bool
    snapshot: ThreadSnapshotPack | None
    loaded_from_persistence: bool = False


@dataclass(frozen=True)
class SnapshotBuildResult:
    snapshot: ThreadSnapshotPack
    refreshed: bool
    reason: str


@dataclass(frozen=True)
class SnapshotTrace:
    built: bool
    refreshed: bool
    source: str
    thread_id: int
    thread_key: str
    source_turn_count: int
    included_turn_count: int
    filtered_recap_turn_count: int
    filtered_pending_turn_count: int
    filtered_control_turn_count: int


class TurnInterpretationKind(str, Enum):
    ORDINARY = "ordinary"
    RECALL_CURRENT = "recall_current"
    RECALL_PREVIOUS = "recall_previous"
    RECALL_NAMED = "recall_named"
    RESUME_PREVIOUS = "resume_previous"
    RESUME_NAMED = "resume_named"
    CLARIFICATION_NEEDED = "clarification_needed"


class RecallTargetKind(str, Enum):
    NONE = "none"
    CURRENT = "current"
    PREVIOUS = "previous"
    NAMED = "named"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class RecallRequest:
    target: RecallTargetKind
    thread_key: str | None = None


@dataclass(frozen=True)
class TurnInterpretation:
    kind: TurnInterpretationKind
    pattern_name: str | None = None
    recall_request: RecallRequest | None = None
    clarification_reason: str | None = None


@dataclass(frozen=True)
class RecallResolution:
    target: RecallTargetKind
    resolved: bool
    thread_id: int | None = None
    thread_key: str | None = None
    snapshot: ThreadSnapshotPack | None = None
    used_snapshot: bool = False
    loaded_from_persistence: bool = False
    refreshed_snapshot: bool = False
    clarification_message: str | None = None


@dataclass(frozen=True)
class FocusLine:
    key: str
    text: str


@dataclass(frozen=True)
class FocusSourceMetadata:
    source_turn_count: int
    included_turn_count: int
    filtered_recap_turn_count: int
    filtered_pending_turn_count: int
    filtered_control_turn_count: int


@dataclass(frozen=True)
class ThreadFocusPack:
    session_id: int
    thread_id: int
    thread_key: str
    last_turn_id: int | None
    focus_updated_at: datetime
    focus_source_turn_count: int
    focus_lines: list[FocusLine]
    source_metadata: FocusSourceMetadata


@dataclass(frozen=True)
class FocusUpdateResult:
    focus: ThreadFocusPack
    refreshed: bool
    reason: str


class FocusTarget(str, Enum):
    CURRENT = "current"
    PREVIOUS = "previous"
    NAMED = "named"


@dataclass(frozen=True)
class ThreadFocusRequest:
    target: FocusTarget
    thread_key: str | None = None
    limit: int | None = None
    refresh: bool = False
    source: str = "unspecified"


@dataclass(frozen=True)
class ThreadFocusView:
    request: ThreadFocusRequest
    found: bool
    focus: ThreadFocusPack | None
    loaded_from_persistence: bool = False


@dataclass(frozen=True)
class FollowupReference:
    detected: bool
    phrase: str | None = None


@dataclass(frozen=True)
class FollowupResolution:
    detected: bool
    resolved: bool
    ambiguous: bool
    phrase: str | None = None
    target_line: str | None = None
    clarification_message: str | None = None


class ResponsePlanKind(str, Enum):
    ORDINARY = "ordinary"
    RECALL = "recall"
    RESUME = "resume"
    CLARIFICATION = "clarification"
    STRUCTURED = "structured"
    CORRECTION_REDIRECT = "correction_redirect"
    UNCERTAINTY_LABELED = "uncertainty_labeled"


class ConfidenceBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComparisonReason(str, Enum):
    INTERPRETATION_RECALL = "interpretation_recall"
    INTERPRETATION_RESUME = "interpretation_resume"
    CORRECTION_CUE = "correction_cue"
    REDIRECT_CUE = "redirect_cue"
    STRUCTURED_REQUEST = "structured_request"
    FOLLOWUP_TARGET_RESOLVED = "followup_target_resolved"
    FOLLOWUP_AMBIGUOUS = "followup_ambiguous"
    RECALL_CLARIFICATION = "recall_clarification"
    PREVIOUS_THREAD_AVAILABLE = "previous_thread_available"
    CLOSE_CANDIDATES = "close_candidates"
    DEFAULT_FALLBACK = "default_fallback"


class CandidateKind(str, Enum):
    DIRECT = "direct"
    RECALL = "recall"
    RESUME = "resume"
    FOCUS_FOLLOWUP = "focus_followup"
    CORRECTION_REDIRECT = "correction_redirect"
    STRUCTURED = "structured"
    CLARIFICATION = "clarification"
    UNCERTAINTY = "uncertainty"


class AnswerStrategy(str, Enum):
    DIRECT_ANSWER = "direct_answer"
    STRUCTURED_ANSWER = "structured_answer"
    RECALL_ANSWER = "recall_answer"
    RESUME_ANSWER = "resume_answer"
    CORRECTION_REDIRECT = "correction_redirect"
    CLARIFICATION = "clarification"
    UNCERTAINTY_LABELED_ANSWER = "uncertainty_labeled_answer"


@dataclass(frozen=True)
class ClarificationNeed:
    needed: bool
    cause: str | None = None


@dataclass(frozen=True)
class ClarificationQuestionSpec:
    question: str
    cause: str


@dataclass(frozen=True)
class DeliberationInput:
    message: str
    interpretation_kind: str
    recall_resolved: bool
    recall_target: str
    recall_clarification: str | None
    has_focus: bool
    followup_detected: bool
    followup_resolved: bool
    followup_ambiguous: bool
    followup_target: str | None
    followup_clarification: str | None
    has_previous_thread: bool
    correction_cue: bool
    redirect_cue: bool
    references_previous_thread: bool
    references_other_target: bool
    structured_request: bool


@dataclass(frozen=True)
class DeliberationCandidate:
    kind: CandidateKind
    strategy: AnswerStrategy
    score: int
    confidence: ConfidenceBand
    reasons: list[ComparisonReason]
    clarification: ClarificationQuestionSpec | None = None


@dataclass(frozen=True)
class ComparisonPack:
    built: bool
    candidates: list[DeliberationCandidate]
    winner_kind: CandidateKind
    winner_score: int


@dataclass(frozen=True)
class AnswerStrategySelection:
    strategy: AnswerStrategy
    selected_candidate_kind: CandidateKind
    confidence: ConfidenceBand
    reasons: list[ComparisonReason]
    clarification_need: ClarificationNeed
    clarification_question: ClarificationQuestionSpec | None = None


@dataclass(frozen=True)
class ResponsePlanSection:
    title: str
    lines: list[str]


@dataclass(frozen=True)
class ResponsePlan:
    kind: ResponsePlanKind
    sections: list[ResponsePlanSection]
    followup_prompt: str | None = None
    focus_used: bool = False


@dataclass(frozen=True)
class TurnInterpretTrace:
    kind: str
    pattern_name: str | None = None
    clarification_reason: str | None = None


@dataclass(frozen=True)
class RecallTrace:
    requested: bool
    request_target: str | None = None
    resolved_target: str | None = None
    thread_id: int | None = None
    thread_key: str | None = None
    used_snapshot: bool = False
    loaded_from_persistence: bool = False
    refreshed_snapshot: bool = False
    clarification_emitted: bool = False


@dataclass(frozen=True)
class ComparisonPackTrace:
    built: bool
    candidate_count: int
    candidate_kinds: list[str]
    winner_kind: str
    winner_score: int


@dataclass(frozen=True)
class AnswerStrategyTrace:
    selected_strategy: str
    selected_candidate_kind: str
    confidence: str
    clarification_planned: bool
    clarification_cause: str | None = None

@dataclass(frozen=True)
class ResponsePlanTrace:
    kind: str
    section_count: int
    clarification_emitted: bool
    focus_used: bool = False


@dataclass(frozen=True)
class ThreadFocusTrace:
    loaded: bool
    loaded_from_persistence: bool
    thread_id: int | None
    thread_key: str | None
    source_turn_count: int
    included_turn_count: int
    filtered_recap_turn_count: int
    filtered_pending_turn_count: int
    filtered_control_turn_count: int
    updated: bool = False
    update_reason: str | None = None


@dataclass(frozen=True)
class FollowupTrace:
    detected: bool
    resolved: bool
    ambiguous: bool
    phrase: str | None = None
    target_line: str | None = None
    clarification_emitted: bool = False


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
