from __future__ import annotations

from syntaris.contracts.runtime import ActiveConversationState, LastTurnTraceView, RuntimeContext, SessionStatusView, TalkRequest, ThreadListView
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
