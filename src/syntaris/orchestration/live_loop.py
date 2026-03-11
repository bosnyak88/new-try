from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Iterable

from syntaris.contracts.runtime import (
    LiveConversationState,
    LiveTurnOutput,
    LoopAction,
    LoopCommand,
    RuntimeContext,
    TalkRequest,
)
from syntaris.orchestration.talk import resolve_active_state
from syntaris.orchestration.turns import execute_turn
from syntaris.persistence import PersistenceStore


@dataclass(frozen=True)
class LiveLoopResult:
    outputs: list[LiveTurnOutput]


def parse_loop_command(raw: str) -> LoopCommand:
    text = raw.strip()
    if not text:
        return LoopCommand(action=LoopAction.INVALID, raw_input=raw, error="empty_input")

    if not text.startswith("/"):
        return LoopCommand(action=LoopAction.TURN, raw_input=raw, value=raw)

    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else None

    if command in {"/kilep", "/exit"}:
        return LoopCommand(action=LoopAction.EXIT, raw_input=raw)
    if command in {"/allapot", "/status"}:
        return LoopCommand(action=LoopAction.STATUS, raw_input=raw)
    if command in {"/szal", "/thread"}:
        if not arg:
            return LoopCommand(action=LoopAction.INVALID, raw_input=raw, error="missing_thread_key")
        return LoopCommand(action=LoopAction.SWITCH_THREAD, raw_input=raw, value=arg)
    if command in {"/mod", "/mode"}:
        if not arg:
            return LoopCommand(action=LoopAction.INVALID, raw_input=raw, error="missing_mode")
        return LoopCommand(action=LoopAction.SWITCH_MODE, raw_input=raw, value=arg)

    return LoopCommand(action=LoopAction.INVALID, raw_input=raw, error="unknown_command")


def _to_live_state(context: RuntimeContext) -> LiveConversationState:
    state = resolve_active_state(context)
    return LiveConversationState(
        session_id=state.session_id,
        thread_id=state.thread_id,
        thread_key=state.thread_key,
        mode=state.mode,
        turn_count=state.turn_count,
        last_turn_id=state.last_turn_id,
        previous_thread_id=state.previous_thread_id,
        previous_thread_key=state.previous_thread_key,
        pending_route=state.pending_route,
    )


def _output(kind: str, message: str, state: LiveConversationState, **kwargs: object) -> LiveTurnOutput:
    return LiveTurnOutput(kind=kind, message=message, state=state, **kwargs)


def run_live_loop(
    context: RuntimeContext,
    lines: Iterable[str],
    emit_trace: bool = True,
) -> LiveLoopResult:
    outputs: list[LiveTurnOutput] = []
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    state = _to_live_state(context)

    if emit_trace:
        store.create_trace_events(
            session_id=state.session_id,
            thread_id=state.thread_id,
            turn_id=0,
            mode=state.mode,
            backend="loop",
            degraded=False,
            events=[{"event_name": "live_loop_started", "payload": {"session_id": state.session_id}}],
        )

    for raw in lines:
        command = parse_loop_command(raw)

        if command.action == LoopAction.INVALID:
            outputs.append(_output("error", json.dumps({"error": command.error}), state))
            continue

        if command.action == LoopAction.EXIT:
            outputs.append(_output("exit", json.dumps({"event": "loop_exit"}), state))
            break

        if command.action == LoopAction.STATUS:
            state = _to_live_state(context)
            outputs.append(_output("status", json.dumps(_status_payload(state), sort_keys=True), state))
            continue

        if command.action == LoopAction.SWITCH_THREAD:
            active = resolve_active_state(context)
            thread_key = str(command.value)
            thread = store.open_or_create_thread(active.session_id, thread_key)
            store.set_active_state(session_id=active.session_id, thread_id=thread.thread_id, mode=active.mode)
            state = _to_live_state(context)
            outputs.append(_output("control", json.dumps({"event": "thread_switched", "thread_key": state.thread_key}, sort_keys=True), state))
            if emit_trace:
                store.create_trace_events(
                    session_id=state.session_id,
                    thread_id=state.thread_id,
                    turn_id=0,
                    mode=state.mode,
                    backend="loop",
                    degraded=False,
                    events=[{"event_name": "live_loop_command_handled", "payload": {"command": "switch_thread", "thread_key": state.thread_key}}],
                )
            continue

        if command.action == LoopAction.SWITCH_MODE:
            active = resolve_active_state(context)
            store.set_active_state(session_id=active.session_id, thread_id=active.thread_id, mode=str(command.value))
            state = _to_live_state(context)
            outputs.append(_output("control", json.dumps({"event": "mode_switched", "mode": state.mode}, sort_keys=True), state))
            if emit_trace:
                store.create_trace_events(
                    session_id=state.session_id,
                    thread_id=state.thread_id,
                    turn_id=0,
                    mode=state.mode,
                    backend="loop",
                    degraded=False,
                    events=[{"event_name": "live_loop_command_handled", "payload": {"command": "switch_mode", "mode": state.mode}}],
                )
            continue

        if command.action == LoopAction.TURN:
            result = execute_turn(context, TalkRequest(message=str(command.value)), source="talk_live")
            state = _to_live_state(context)
            outputs.append(
                _output(
                    "turn",
                    result.turn.assistant_reply,
                    state,
                    turn_id=result.turn.turn_id,
                    backend=result.turn.reply_backend,
                    degraded=result.turn.degraded,
                )
            )

    return LiveLoopResult(outputs=outputs)


def run_live_loop_interactive(
    context: RuntimeContext,
    input_func: Callable[[str], str] = input,
) -> LiveLoopResult:
    def line_iter() -> Iterable[str]:
        while True:
            try:
                yield input_func("")
            except EOFError:
                yield "/kilep"
                return

    return run_live_loop(context, line_iter())


def _status_payload(state: LiveConversationState) -> dict[str, int | str | None]:
    return {
        "session_id": state.session_id,
        "thread_id": state.thread_id,
        "thread_key": state.thread_key,
        "mode": state.mode,
        "turn_count": state.turn_count,
        "last_turn_id": state.last_turn_id,
        "previous_thread_id": state.previous_thread_id,
        "previous_thread_key": state.previous_thread_key,
        "pending_route": {
            "pending_action": state.pending_route.pending_action,
            "pending_thread_key": state.pending_route.pending_thread_key,
            "pending_reason": state.pending_route.pending_reason,
            "pending_original_message": state.pending_route.pending_original_message,
            "match_pattern": state.pending_route.match_pattern,
            "source": state.pending_route.source,
            "proposed_at": state.pending_route.proposed_at,
        } if state.pending_route else None,
    }
