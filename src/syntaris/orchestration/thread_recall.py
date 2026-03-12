from __future__ import annotations

from syntaris.contracts.runtime import (
    RecallRequest,
    RecallResolution,
    RecallTargetKind,
    RuntimeContext,
    SnapshotTarget,
    ThreadSnapshotRequest,
    TurnInterpretation,
)
from syntaris.orchestration.thread_snapshot import build_thread_snapshot_view
from syntaris.persistence import PersistenceStore


_CLARIFY_MESSAGE = "Nem egyértelmű, melyik szálra gondolsz. Írd meg: jelenlegi, előző, vagy a szál nevét."


def _clarify(target: RecallTargetKind) -> RecallResolution:
    return RecallResolution(
        target=target,
        resolved=False,
        clarification_message=_CLARIFY_MESSAGE,
    )


def resolve_recall_request(context: RuntimeContext, interpretation: TurnInterpretation) -> RecallResolution:
    request: RecallRequest | None = interpretation.recall_request
    if request is None:
        if interpretation.clarification_reason is not None:
            return _clarify(RecallTargetKind.AMBIGUOUS)
        return RecallResolution(target=RecallTargetKind.NONE, resolved=False)

    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    active = store.resolve_or_create_active(
        default_thread_key=context.config.conversation.default_thread_key,
        default_mode=context.config.conversation.default_mode,
    )

    if request.target == RecallTargetKind.CURRENT:
        view = build_thread_snapshot_view(
            context,
            ThreadSnapshotRequest(target=SnapshotTarget.CURRENT, source="talk_recall_current"),
        )
    elif request.target == RecallTargetKind.PREVIOUS:
        if active.previous_thread_id is None:
            return _clarify(RecallTargetKind.PREVIOUS)
        view = build_thread_snapshot_view(
            context,
            ThreadSnapshotRequest(target=SnapshotTarget.PREVIOUS, source="talk_recall_previous"),
        )
    elif request.target == RecallTargetKind.NAMED:
        if not request.thread_key:
            return _clarify(RecallTargetKind.NAMED)
        view = build_thread_snapshot_view(
            context,
            ThreadSnapshotRequest(target=SnapshotTarget.NAMED, thread_key=request.thread_key, source="talk_recall_named"),
        )
    else:
        return _clarify(RecallTargetKind.AMBIGUOUS)

    if not view.found or view.snapshot is None:
        return _clarify(request.target)

    return RecallResolution(
        target=request.target,
        resolved=True,
        thread_id=view.snapshot.thread_id,
        thread_key=view.snapshot.thread_key,
        snapshot=view.snapshot,
        used_snapshot=True,
        loaded_from_persistence=view.loaded_from_persistence,
        refreshed_snapshot=not view.loaded_from_persistence,
    )
