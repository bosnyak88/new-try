from __future__ import annotations

from dataclasses import dataclass

from syntaris.contracts.runtime import LastTurnTraceView, RuntimeContext, TurnInput, TurnResult
from syntaris.persistence import PersistenceStore
from syntaris.reply.adapters import ReplyOutput
from syntaris.reply.factory import build_reply_adapter
from syntaris.trace.events import build_turn_trace_events


@dataclass(frozen=True)
class TalkRunResult:
    turn: TurnResult


def init_db(context: RuntimeContext) -> dict[str, str | bool]:
    store = PersistenceStore(context.config.paths.db_path)
    result = store.initialize(data_dir=context.config.paths.data_dir)
    return {"db_path": result.db_path, "schema_initialized": result.schema_initialized}


def talk_once(context: RuntimeContext, message: str) -> TalkRunResult:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)

    session = store.create_session()
    reply_adapter = build_reply_adapter(context.config.reply)
    turn_input = TurnInput(message=message, session_id=session.session_id)
    reply: ReplyOutput = reply_adapter.generate(turn_input)

    turn = store.create_turn(
        session_id=session.session_id,
        user_message=message,
        assistant_reply=reply.text,
        reply_backend=reply.backend,
        degraded=reply.degraded,
    )

    trace_events = build_turn_trace_events(turn=turn, backend=reply.backend, degraded=reply.degraded)
    store.create_trace_events(
        session_id=turn.session_id,
        turn_id=turn.turn_id,
        backend=reply.backend,
        degraded=reply.degraded,
        events=trace_events,
    )

    return TalkRunResult(turn=turn)


def trace_last(context: RuntimeContext) -> LastTurnTraceView:
    store = PersistenceStore(context.config.paths.db_path)
    store.initialize(data_dir=context.config.paths.data_dir)
    return store.read_last_turn_trace()
