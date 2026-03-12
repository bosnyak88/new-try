from __future__ import annotations

from syntaris.contracts.runtime import ActiveConversationState, ContextSource, FocusTarget, LastTurnTraceView, RecapRequest, RecapTarget, RuntimeContext, SessionStatusView, SnapshotTarget, TalkRequest, ThreadContextRequest, ThreadContextView, ThreadFocusRequest, ThreadFocusView, ThreadListView, ThreadRecapView, ThreadSnapshotRequest, ThreadSnapshotView
from syntaris.orchestration.context_pack import build_thread_context_view
from syntaris.orchestration.recap import build_thread_recap_view
from syntaris.orchestration.thread_focus import build_thread_focus_view
from syntaris.orchestration.thread_snapshot import build_thread_snapshot_view
from syntaris.orchestration.turns import TalkRunResult, execute_turn
from syntaris.persistence import PersistenceStore


def init_db(context: RuntimeContext) -> dict[str, str | bool | int]:
    store = PersistenceStore(context.config.paths.db_path)
    result = store.initialize(data_dir=context.config.paths.data_dir)
    return {
        "db_path": result.db_path,
        "schema_initialized": result.schema_initialized,
        "schema_version": result.schema_version,
    }


def resolve_active_state(context: RuntimeContext) -> ActiveConversationState:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    return store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )


def talk_once(context: RuntimeContext, request: TalkRequest) -> TalkRunResult:
    return execute_turn(context, request, source="talk_once")


def trace_last(context: RuntimeContext) -> LastTurnTraceView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    return store.read_last_turn_trace()


def list_threads(context: RuntimeContext) -> ThreadListView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    state = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )
    return store.list_threads_view(session_id=state.session_id, active_thread_id=state.thread_id)


def session_status(context: RuntimeContext) -> SessionStatusView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    return store.get_session_status_view(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )


def thread_view_current(context: RuntimeContext, limit: int | None = None) -> ThreadContextView:
    return build_thread_context_view(
        context,
        ThreadContextRequest(source=ContextSource.CURRENT.value, limit=limit),
    )


def thread_view_previous(context: RuntimeContext, limit: int | None = None) -> ThreadContextView:
    return build_thread_context_view(
        context,
        ThreadContextRequest(source=ContextSource.PREVIOUS.value, limit=limit),
    )


def thread_view_named(context: RuntimeContext, thread_key: str, limit: int | None = None) -> ThreadContextView:
    return build_thread_context_view(
        context,
        ThreadContextRequest(source=ContextSource.NAMED.value, thread_key=thread_key, limit=limit),
    )


def thread_recap_current(context: RuntimeContext, limit: int | None = None) -> ThreadRecapView:
    return build_thread_recap_view(context, RecapRequest(target=RecapTarget.CURRENT, limit=limit))


def thread_recap_previous(context: RuntimeContext, limit: int | None = None) -> ThreadRecapView:
    return build_thread_recap_view(context, RecapRequest(target=RecapTarget.PREVIOUS, limit=limit))


def thread_recap_named(context: RuntimeContext, thread_key: str, limit: int | None = None) -> ThreadRecapView:
    return build_thread_recap_view(context, RecapRequest(target=RecapTarget.NAMED, thread_key=thread_key, limit=limit))


def thread_snapshot_current(context: RuntimeContext, limit: int | None = None, refresh: bool = False) -> ThreadSnapshotView:
    return build_thread_snapshot_view(
        context,
        ThreadSnapshotRequest(target=SnapshotTarget.CURRENT, limit=limit, refresh=refresh, source="cli_thread_snapshot"),
    )


def thread_snapshot_previous(context: RuntimeContext, limit: int | None = None, refresh: bool = False) -> ThreadSnapshotView:
    return build_thread_snapshot_view(
        context,
        ThreadSnapshotRequest(target=SnapshotTarget.PREVIOUS, limit=limit, refresh=refresh, source="cli_thread_snapshot"),
    )


def thread_snapshot_named(context: RuntimeContext, thread_key: str, limit: int | None = None, refresh: bool = False) -> ThreadSnapshotView:
    return build_thread_snapshot_view(
        context,
        ThreadSnapshotRequest(target=SnapshotTarget.NAMED, thread_key=thread_key, limit=limit, refresh=refresh, source="cli_thread_snapshot"),
    )


def thread_focus_current(context: RuntimeContext, limit: int | None = None, refresh: bool = False) -> ThreadFocusView:
    return build_thread_focus_view(
        context,
        ThreadFocusRequest(target=FocusTarget.CURRENT, limit=limit, refresh=refresh, source="cli_thread_focus"),
    )


def thread_focus_previous(context: RuntimeContext, limit: int | None = None, refresh: bool = False) -> ThreadFocusView:
    return build_thread_focus_view(
        context,
        ThreadFocusRequest(target=FocusTarget.PREVIOUS, limit=limit, refresh=refresh, source="cli_thread_focus"),
    )


def thread_focus_named(context: RuntimeContext, thread_key: str, limit: int | None = None, refresh: bool = False) -> ThreadFocusView:
    return build_thread_focus_view(
        context,
        ThreadFocusRequest(target=FocusTarget.NAMED, thread_key=thread_key, limit=limit, refresh=refresh, source="cli_thread_focus"),
    )
