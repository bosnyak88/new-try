from __future__ import annotations

from datetime import datetime

from syntaris.contracts.runtime import (
    FocusLine,
    FocusSourceMetadata,
    FocusTarget,
    FocusUpdateResult,
    RuntimeContext,
    ThreadFocusPack,
    ThreadFocusRequest,
    ThreadFocusView,
)
from syntaris.orchestration.thread_snapshot import _is_control_turn, _is_pending_turn, _is_recap_turn
from syntaris.persistence import PersistenceStore
from syntaris.orchestration.text_normalize import clean_display_text, contains_degraded_text
from syntaris.orchestration.workframe_state import derive_workframe_state


def _resolve_limit(context: RuntimeContext, limit: int | None) -> int:
    return max(1, limit) if limit is not None else context.config.conversation.focus_turn_window


def _to_focus_lines(user_message: str, assistant_reply: str, max_lines: int) -> list[FocusLine]:
    lines = [
        FocusLine(key="active_topic_line", text=clean_display_text(user_message).strip()),
        FocusLine(key="latest_answer_line", text=clean_display_text(assistant_reply).strip()),
    ]
    result: list[FocusLine] = []
    for line in lines:
        if line.text:
            result.append(line)
    return result[:max_lines]


def build_thread_focus_pack(context: RuntimeContext, thread_id: int, mode: str, limit: int | None = None) -> ThreadFocusPack | None:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    context_pack = store.build_thread_context_pack(thread_id=thread_id, mode=mode, turn_window=_resolve_limit(context, limit))
    if context_pack is None:
        return None

    filtered_recap = 0
    filtered_pending = 0
    filtered_control = 0
    candidates = []
    for turn in context_pack.recent_turns:
        is_control = _is_control_turn(turn.user_message)
        is_pending = _is_pending_turn(turn.user_message, turn.assistant_reply)
        is_recap = _is_recap_turn(turn.user_message, turn.assistant_reply)
        if is_control:
            filtered_control += 1
            continue
        if is_pending:
            filtered_pending += 1
            continue
        if is_recap:
            filtered_recap += 1
            continue
        candidates.append(turn)

    selected = candidates[-1] if candidates else None
    focus_lines: list[FocusLine] = []
    if selected is not None:
        focus_lines = _to_focus_lines(
            user_message=selected.user_message,
            assistant_reply=selected.assistant_reply,
            max_lines=max(1, context.config.conversation.focus_line_limit),
        )

    semantic_pack = store.build_thread_context_pack(thread_id=thread_id, mode=mode, turn_window=max(context_pack.turn_count, 1))
    semantic_turns = semantic_pack.recent_turns if semantic_pack is not None else context_pack.recent_turns

    metadata = FocusSourceMetadata(
        source_turn_count=len(context_pack.recent_turns),
        included_turn_count=1 if selected is not None else 0,
        filtered_recap_turn_count=filtered_recap,
        filtered_pending_turn_count=filtered_pending,
        filtered_control_turn_count=filtered_control,
    )
    return ThreadFocusPack(
        session_id=context_pack.session_id,
        thread_id=context_pack.thread_id,
        thread_key=context_pack.thread_key,
        last_turn_id=context_pack.last_turn_id,
        focus_updated_at=context.clock.now(),
        focus_source_turn_count=len(context_pack.recent_turns),
        focus_lines=focus_lines,
        source_metadata=metadata,
        workframe_state=derive_workframe_state(semantic_turns, ""),
    )




def _focus_has_dirty_text(focus: ThreadFocusPack) -> bool:
    for line in focus.focus_lines:
        if clean_display_text(line.text) != line.text:
            return True
        if contains_degraded_text(line.text):
            return True
    return False


def _focus_is_stale(store: PersistenceStore, focus: ThreadFocusPack) -> bool:
    if focus.workframe_state is None:
        return True
    turn_count, last_turn_id = store.get_thread_turn_head(focus.thread_id)
    if focus.last_turn_id != last_turn_id:
        return True
    if focus.focus_source_turn_count > turn_count:
        return True
    return False

def refresh_thread_focus(context: RuntimeContext, thread_id: int, mode: str, limit: int | None = None, reason: str = "manual_refresh") -> FocusUpdateResult | None:
    focus = build_thread_focus_pack(context, thread_id=thread_id, mode=mode, limit=limit)
    if focus is None:
        return None
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    store.upsert_thread_focus(focus)
    return FocusUpdateResult(focus=focus, refreshed=True, reason=reason)


def build_thread_focus_view(context: RuntimeContext, request: ThreadFocusRequest) -> ThreadFocusView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    active = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )

    thread_id: int | None = None
    mode = active.mode
    if request.target == FocusTarget.CURRENT:
        thread_id = active.thread_id
    elif request.target == FocusTarget.PREVIOUS:
        previous = store.get_previous_thread()
        thread_id = previous.thread_id if previous is not None else None
    elif request.target == FocusTarget.NAMED and request.thread_key is not None:
        named = store.get_thread_by_key(session_id=active.session_id, thread_key=request.thread_key)
        thread_id = named.thread_id if named is not None else None

    if thread_id is None:
        return ThreadFocusView(request=request, found=False, focus=None)

    if request.refresh:
        built = refresh_thread_focus(
            context,
            thread_id=thread_id,
            mode=mode,
            limit=request.limit,
            reason=f"{request.source}:refresh",
        )
        assert built is not None
        return ThreadFocusView(request=request, found=True, focus=built.focus, loaded_from_persistence=False)

    existing = store.read_thread_focus(thread_id)
    if existing is not None:
        if _focus_has_dirty_text(existing) or _focus_is_stale(store, existing):
            built = refresh_thread_focus(
                context,
                thread_id=thread_id,
                mode=mode,
                limit=request.limit,
                reason=f"{request.source}:hygiene_or_stale_refresh",
            )
            assert built is not None
            return ThreadFocusView(request=request, found=True, focus=built.focus, loaded_from_persistence=False)
        return ThreadFocusView(request=request, found=True, focus=existing, loaded_from_persistence=True)

    built = refresh_thread_focus(
        context,
        thread_id=thread_id,
        mode=mode,
        limit=request.limit,
        reason=f"{request.source}:auto_build",
    )
    if built is None:
        return ThreadFocusView(request=request, found=False, focus=None)
    return ThreadFocusView(request=request, found=True, focus=built.focus, loaded_from_persistence=False)
