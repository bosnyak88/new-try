from __future__ import annotations

from syntaris.contracts.runtime import (
    ContextLoadResult,
    ContextSource,
    RuntimeContext,
    ThreadContextPack,
    ThreadContextRequest,
    ThreadContextView,
)
from syntaris.persistence import PersistenceStore


def _resolve_limit(context: RuntimeContext, limit: int | None) -> int:
    if limit is None:
        return context.config.conversation.context_turn_window
    return max(1, limit)


def build_thread_context_view(context: RuntimeContext, request: ThreadContextRequest) -> ThreadContextView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    active = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )
    limit = _resolve_limit(context, request.limit)

    pack: ThreadContextPack | None = None
    if request.source == ContextSource.CURRENT.value:
        pack = store.build_thread_context_pack(thread_id=active.thread_id, mode=active.mode, turn_window=limit)
    elif request.source == ContextSource.PREVIOUS.value:
        previous = store.get_previous_thread()
        if previous is not None:
            pack = store.build_thread_context_pack(thread_id=previous.thread_id, mode=active.mode, turn_window=limit)
    elif request.source == ContextSource.NAMED.value:
        if request.thread_key is not None:
            thread = store.get_thread_by_key(session_id=active.session_id, thread_key=request.thread_key)
            if thread is not None:
                pack = store.build_thread_context_pack(thread_id=thread.thread_id, mode=active.mode, turn_window=limit)

    return ThreadContextView(request=request, found=pack is not None, pack=pack)


def load_execution_context_pack(
    context: RuntimeContext,
    session_id: int,
    thread_id: int,
    mode: str,
    limit: int | None = None,
) -> ContextLoadResult:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    pack = store.build_thread_context_pack(
        thread_id=thread_id,
        mode=mode,
        turn_window=_resolve_limit(context, limit),
    )
    assert pack is not None
    assert pack.session_id == session_id
    return ContextLoadResult(source=ContextSource.EXECUTION_TARGET, pack=pack)
