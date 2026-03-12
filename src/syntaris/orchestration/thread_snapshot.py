from __future__ import annotations

from datetime import datetime, timezone

from syntaris.contracts.runtime import (
    RuntimeContext,
    SnapshotBuildResult,
    SnapshotSourceMetadata,
    SnapshotTarget,
    ThreadSnapshotLine,
    ThreadSnapshotPack,
    ThreadSnapshotRequest,
    ThreadSnapshotView,
)
from syntaris.orchestration.recap import match_recap_query
from syntaris.persistence import PersistenceStore
from syntaris.orchestration.text_normalize import clean_display_text

_CONTROL_PREFIXES = ("/",)
_AFFIRMATIVE = {"igen", "oké", "mehet", "arra", "igen arra"}
_NEGATIVE = {"nem", "mégse", "maradjon", "ne", "nem arra"}


def _resolve_limit(context: RuntimeContext, limit: int | None) -> int:
    return max(1, limit) if limit is not None else context.config.conversation.snapshot_turn_window


def _is_control_turn(user_message: str) -> bool:
    return user_message.strip().startswith(_CONTROL_PREFIXES)


def _is_pending_turn(user_message: str, assistant_reply: str) -> bool:
    normalized = clean_display_text(user_message).strip().lower()
    if normalized in _AFFIRMATIVE or normalized in _NEGATIVE:
        return True
    return "váltsak? (igen/nem)" in clean_display_text(assistant_reply).lower()


def _is_recap_turn(user_message: str, assistant_reply: str) -> bool:
    return match_recap_query(clean_display_text(user_message)).action.value != "none" or clean_display_text(assistant_reply).startswith("Szál recap:")


def _build_snapshot_text(pack: ThreadSnapshotPack) -> str:
    header = (
        f"Thread snapshot: {pack.thread_key} (session={pack.session_id}, thread_id={pack.thread_id}, "
        f"turn_count={pack.turn_count}, last_turn_id={pack.last_turn_id}, built_at={pack.snapshot_built_at.isoformat()})"
    )
    if not pack.snapshot_lines:
        return f"{header}\nNincs snapshot-kompatibilis turn ezen a szálon."
    lines = [
        f"- #{line.turn_index} user={line.user_message} | assistant={line.assistant_reply}"
        for line in pack.snapshot_lines
    ]
    return "\n".join([header, *lines])


def build_thread_snapshot_pack(context: RuntimeContext, thread_id: int, mode: str, limit: int | None = None) -> ThreadSnapshotPack | None:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    context_pack = store.build_thread_context_pack(thread_id=thread_id, mode=mode, turn_window=_resolve_limit(context, limit))
    if context_pack is None:
        return None

    filtered_recap = 0
    filtered_pending = 0
    filtered_control = 0
    lines: list[ThreadSnapshotLine] = []

    for turn in context_pack.recent_turns:
        is_control = _is_control_turn(turn.user_message)
        is_pending = _is_pending_turn(turn.user_message, turn.assistant_reply)
        is_recap = _is_recap_turn(turn.user_message, turn.assistant_reply)

        if is_control:
            filtered_control += 1
            continue
        if is_pending and not context.config.conversation.snapshot_include_pending_turns:
            filtered_pending += 1
            continue
        if is_recap and not context.config.conversation.snapshot_include_recap_turns:
            filtered_recap += 1
            continue

        lines.append(
            ThreadSnapshotLine(
                turn_id=turn.turn_id,
                turn_index=turn.turn_index,
                user_message=clean_display_text(turn.user_message),
                assistant_reply=clean_display_text(turn.assistant_reply),
            )
        )

    metadata = SnapshotSourceMetadata(
        source_turn_count=len(context_pack.recent_turns),
        included_turn_count=len(lines),
        filtered_recap_turn_count=filtered_recap,
        filtered_pending_turn_count=filtered_pending,
        filtered_control_turn_count=filtered_control,
    )
    provisional = ThreadSnapshotPack(
        session_id=context_pack.session_id,
        thread_id=context_pack.thread_id,
        thread_key=context_pack.thread_key,
        mode=context_pack.mode,
        turn_count=context_pack.turn_count,
        last_turn_id=context_pack.last_turn_id,
        snapshot_built_at=datetime.now(timezone.utc),
        source_metadata=metadata,
        snapshot_lines=lines,
        snapshot_text="",
        previous_thread_id=context_pack.previous_thread_id,
        previous_thread_key=context_pack.previous_thread_key,
    )
    return ThreadSnapshotPack(**{**provisional.__dict__, "snapshot_text": _build_snapshot_text(provisional)})




def _snapshot_has_dirty_text(snapshot: ThreadSnapshotPack) -> bool:
    if clean_display_text(snapshot.snapshot_text) != snapshot.snapshot_text:
        return True
    if any(marker in snapshot.snapshot_text for marker in ("Ã", "Å", "�")):
        return True
    for line in snapshot.snapshot_lines:
        if clean_display_text(line.user_message) != line.user_message:
            return True
        if clean_display_text(line.assistant_reply) != line.assistant_reply:
            return True
        if any(marker in line.user_message for marker in ("Ã", "Å", "�")):
            return True
        if any(marker in line.assistant_reply for marker in ("Ã", "Å", "�")):
            return True
    return False


def _snapshot_is_stale(store: PersistenceStore, snapshot: ThreadSnapshotPack) -> bool:
    turn_count, last_turn_id = store.get_thread_turn_head(snapshot.thread_id)
    if snapshot.turn_count != turn_count:
        return True
    if snapshot.last_turn_id != last_turn_id:
        return True
    return False

def refresh_thread_snapshot(context: RuntimeContext, thread_id: int, mode: str, limit: int | None = None, reason: str = "manual_refresh") -> SnapshotBuildResult | None:
    snapshot = build_thread_snapshot_pack(context, thread_id=thread_id, mode=mode, limit=limit)
    if snapshot is None:
        return None
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    store.upsert_thread_snapshot(snapshot)
    return SnapshotBuildResult(snapshot=snapshot, refreshed=True, reason=reason)


def build_thread_snapshot_view(context: RuntimeContext, request: ThreadSnapshotRequest) -> ThreadSnapshotView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    active = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )

    thread_id: int | None = None
    mode = active.mode
    if request.target == SnapshotTarget.CURRENT:
        thread_id = active.thread_id
    elif request.target == SnapshotTarget.PREVIOUS:
        previous = store.get_previous_thread()
        thread_id = previous.thread_id if previous is not None else None
    elif request.target == SnapshotTarget.NAMED and request.thread_key is not None:
        named = store.get_thread_by_key(session_id=active.session_id, thread_key=request.thread_key)
        thread_id = named.thread_id if named is not None else None

    if thread_id is None:
        return ThreadSnapshotView(request=request, found=False, snapshot=None)

    if request.refresh:
        built = refresh_thread_snapshot(
            context,
            thread_id=thread_id,
            mode=mode,
            limit=request.limit,
            reason=f"{request.source}:refresh",
        )
        assert built is not None
        return ThreadSnapshotView(request=request, found=True, snapshot=built.snapshot, loaded_from_persistence=False)

    existing = store.read_thread_snapshot(thread_id)
    if existing is not None:
        if _snapshot_has_dirty_text(existing) or _snapshot_is_stale(store, existing):
            built = refresh_thread_snapshot(
                context,
                thread_id=thread_id,
                mode=mode,
                limit=request.limit,
                reason=f"{request.source}:hygiene_or_stale_refresh",
            )
            assert built is not None
            return ThreadSnapshotView(request=request, found=True, snapshot=built.snapshot, loaded_from_persistence=False)
        return ThreadSnapshotView(request=request, found=True, snapshot=existing, loaded_from_persistence=True)

    built = refresh_thread_snapshot(
        context,
        thread_id=thread_id,
        mode=mode,
        limit=request.limit,
        reason=f"{request.source}:auto_build",
    )
    if built is None:
        return ThreadSnapshotView(request=request, found=False, snapshot=None)
    return ThreadSnapshotView(request=request, found=True, snapshot=built.snapshot, loaded_from_persistence=False)


def refresh_snapshot_for_transition(
    context: RuntimeContext,
    from_thread_id: int,
    from_mode: str,
    switched: bool,
    source: str,
) -> SnapshotBuildResult | None:
    if not switched:
        return None
    return refresh_thread_snapshot(
        context,
        thread_id=from_thread_id,
        mode=from_mode,
        reason=f"{source}:thread_switch",
    )
