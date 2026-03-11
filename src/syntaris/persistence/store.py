from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from syntaris.contracts.runtime import (
    LastTurnTraceView,
    PersistenceBootstrapResult,
    SessionRecord,
    TraceEventRecord,
    TurnResult,
)
from syntaris.persistence.schema import SCHEMA_SQL


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PersistenceStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def initialize(self, data_dir: str) -> PersistenceBootstrapResult:
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                ("schema_version", "1"),
            )
            conn.commit()
        return PersistenceBootstrapResult(db_path=self.db_path, schema_initialized=True)

    def create_session(self) -> SessionRecord:
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO sessions(created_at) VALUES (?)",
                (created_at.isoformat(),),
            )
            conn.commit()
            session_id = int(cur.lastrowid)
        return SessionRecord(session_id=session_id, created_at=created_at)

    def create_turn(
        self,
        session_id: int,
        user_message: str,
        assistant_reply: str,
        reply_backend: str,
        degraded: bool,
    ) -> TurnResult:
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO turns(session_id, user_message, assistant_reply, reply_backend, degraded, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_message, assistant_reply, reply_backend, int(degraded), created_at.isoformat()),
            )
            conn.commit()
            turn_id = int(cur.lastrowid)
        return TurnResult(
            turn_id=turn_id,
            session_id=session_id,
            user_message=user_message,
            assistant_reply=assistant_reply,
            reply_backend=reply_backend,
            degraded=degraded,
            created_at=created_at,
        )

    def create_trace_events(
        self,
        session_id: int,
        turn_id: int,
        backend: str,
        degraded: bool,
        events: list[dict[str, str]],
    ) -> list[TraceEventRecord]:
        created_at = utc_now()
        trace_records: list[TraceEventRecord] = []
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                cur = conn.execute(
                    """
                    INSERT INTO trace_events(session_id, turn_id, event_name, backend, degraded, payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        turn_id,
                        event["event_name"],
                        backend,
                        int(degraded),
                        json.dumps(event.get("payload", {}), sort_keys=True),
                        created_at.isoformat(),
                    ),
                )
                trace_records.append(
                    TraceEventRecord(
                        trace_id=int(cur.lastrowid),
                        session_id=session_id,
                        turn_id=turn_id,
                        event_name=event["event_name"],
                        backend=backend,
                        degraded=degraded,
                        payload=json.dumps(event.get("payload", {}), sort_keys=True),
                        created_at=created_at,
                    )
                )
            conn.commit()
        return trace_records

    def read_last_turn_trace(self) -> LastTurnTraceView:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            turn_row = conn.execute(
                "SELECT * FROM turns ORDER BY turn_id DESC LIMIT 1"
            ).fetchone()
            if turn_row is None:
                return LastTurnTraceView(turn=None, trace_events=[])

            turn = TurnResult(
                turn_id=int(turn_row["turn_id"]),
                session_id=int(turn_row["session_id"]),
                user_message=str(turn_row["user_message"]),
                assistant_reply=str(turn_row["assistant_reply"]),
                reply_backend=str(turn_row["reply_backend"]),
                degraded=bool(turn_row["degraded"]),
                created_at=datetime.fromisoformat(str(turn_row["created_at"])),
            )

            rows = conn.execute(
                "SELECT * FROM trace_events WHERE turn_id = ? ORDER BY trace_id ASC",
                (turn.turn_id,),
            ).fetchall()

            trace_events = [
                TraceEventRecord(
                    trace_id=int(row["trace_id"]),
                    session_id=int(row["session_id"]),
                    turn_id=int(row["turn_id"]),
                    event_name=str(row["event_name"]),
                    backend=str(row["backend"]),
                    degraded=bool(row["degraded"]),
                    payload=str(row["payload"]),
                    created_at=datetime.fromisoformat(str(row["created_at"])),
                )
                for row in rows
            ]
            return LastTurnTraceView(turn=turn, trace_events=trace_events)
