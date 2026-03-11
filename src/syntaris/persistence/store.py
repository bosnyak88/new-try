from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from syntaris.contracts.runtime import (
    ActiveConversationState,
    LastTurnTraceView,
    PersistenceBootstrapResult,
    SessionRecord,
    ThreadListView,
    ThreadRecord,
    ThreadSummaryView,
    TraceEventRecord,
    TurnResult,
)
from syntaris.persistence.schema import SCHEMA_SQL, SCHEMA_VERSION


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
            self._run_migrations(conn)
            conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
            conn.commit()
        return PersistenceBootstrapResult(
            db_path=self.db_path,
            schema_initialized=True,
            schema_version=SCHEMA_VERSION,
        )

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        turn_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(turns)").fetchall()
        }
        if turn_cols and "thread_id" not in turn_cols:
            conn.execute("ALTER TABLE turns ADD COLUMN thread_id INTEGER")
            conn.execute("ALTER TABLE turns ADD COLUMN mode TEXT")
            conn.execute("ALTER TABLE turns ADD COLUMN turn_index INTEGER")

            session_rows = conn.execute("SELECT session_id FROM sessions").fetchall()
            for (session_id,) in session_rows:
                now = utc_now().isoformat()
                cur = conn.execute(
                    "INSERT OR IGNORE INTO threads(session_id, thread_key, created_at) VALUES (?, ?, ?)",
                    (int(session_id), "default", now),
                )
                if cur.lastrowid:
                    thread_id = int(cur.lastrowid)
                else:
                    thread_id = int(
                        conn.execute(
                            "SELECT thread_id FROM threads WHERE session_id = ? AND thread_key = ?",
                            (int(session_id), "default"),
                        ).fetchone()[0]
                    )

                turn_rows = conn.execute(
                    "SELECT turn_id FROM turns WHERE session_id = ? ORDER BY turn_id ASC",
                    (int(session_id),),
                ).fetchall()
                for idx, (turn_id,) in enumerate(turn_rows, start=1):
                    conn.execute(
                        "UPDATE turns SET thread_id = ?, mode = ?, turn_index = ? WHERE turn_id = ?",
                        (thread_id, "chat", idx, int(turn_id)),
                    )

        trace_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(trace_events)").fetchall()
        }
        if trace_cols and "thread_id" not in trace_cols:
            conn.execute("ALTER TABLE trace_events ADD COLUMN thread_id INTEGER")
            conn.execute("ALTER TABLE trace_events ADD COLUMN mode TEXT")
            conn.execute(
                """
                UPDATE trace_events
                SET thread_id = (
                    SELECT turns.thread_id FROM turns WHERE turns.turn_id = trace_events.turn_id
                ),
                mode = COALESCE(
                    (SELECT turns.mode FROM turns WHERE turns.turn_id = trace_events.turn_id),
                    'chat'
                )
                """
            )

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

    def get_active_state(self) -> ActiveConversationState | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT key, value FROM app_meta WHERE key IN ('active_session_id', 'active_thread_id', 'active_mode', 'previous_thread_id')"
            ).fetchall()
            values = {str(item["key"]): str(item["value"]) for item in row}
            if "active_session_id" not in values or "active_thread_id" not in values:
                return None

            thread = conn.execute(
                "SELECT thread_id, session_id, thread_key FROM threads WHERE thread_id = ?",
                (int(values["active_thread_id"]),),
            ).fetchone()
            if thread is None:
                return None

            turn_count, last_turn_id = conn.execute(
                "SELECT COUNT(1), MAX(turn_id) FROM turns WHERE thread_id = ?",
                (int(thread["thread_id"]),),
            ).fetchone()

            previous_thread_id = int(values["previous_thread_id"]) if "previous_thread_id" in values else None
            previous_thread_key: str | None = None
            if previous_thread_id is not None:
                prev = conn.execute(
                    "SELECT thread_key FROM threads WHERE thread_id = ?",
                    (previous_thread_id,),
                ).fetchone()
                if prev is not None:
                    previous_thread_key = str(prev["thread_key"])

            return ActiveConversationState(
                session_id=int(values["active_session_id"]),
                thread_id=int(thread["thread_id"]),
                thread_key=str(thread["thread_key"]),
                mode=values.get("active_mode", "chat"),
                turn_count=int(turn_count or 0),
                last_turn_id=int(last_turn_id) if last_turn_id is not None else None,
                previous_thread_id=previous_thread_id,
                previous_thread_key=previous_thread_key,
            )

    def set_active_state(self, session_id: int, thread_id: int, mode: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            current_active = conn.execute(
                "SELECT value FROM app_meta WHERE key = ?",
                ("active_thread_id",),
            ).fetchone()
            previous_thread_id: int | None = None
            if current_active is not None:
                existing = int(current_active["value"])
                if existing != thread_id:
                    previous_thread_id = existing

            conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                ("active_session_id", str(session_id)),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                ("active_thread_id", str(thread_id)),
            )
            conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                ("active_mode", mode),
            )
            if previous_thread_id is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                    ("previous_thread_id", str(previous_thread_id)),
                )
            conn.commit()

    def resolve_or_create_active(self, default_thread_key: str, default_mode: str) -> ActiveConversationState:
        active = self.get_active_state()
        if active is not None:
            return active

        session = self.create_session()
        thread = self.open_or_create_thread(session.session_id, default_thread_key)
        self.set_active_state(session.session_id, thread.thread_id, default_mode)
        return ActiveConversationState(
            session_id=session.session_id,
            thread_id=thread.thread_id,
            thread_key=thread.thread_key,
            mode=default_mode,
            turn_count=0,
            last_turn_id=None,
        )

    def open_or_create_thread(self, session_id: int, thread_key: str) -> ThreadRecord:
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT thread_id, created_at FROM threads WHERE session_id = ? AND thread_key = ?",
                (session_id, thread_key),
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    "INSERT INTO threads(session_id, thread_key, created_at) VALUES (?, ?, ?)",
                    (session_id, thread_key, created_at.isoformat()),
                )
                conn.commit()
                return ThreadRecord(
                    thread_id=int(cur.lastrowid),
                    session_id=session_id,
                    thread_key=thread_key,
                    created_at=created_at,
                )

            return ThreadRecord(
                thread_id=int(row["thread_id"]),
                session_id=session_id,
                thread_key=thread_key,
                created_at=datetime.fromisoformat(str(row["created_at"])),
            )


    def list_threads_view(self, session_id: int, active_thread_id: int) -> ThreadListView:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    t.thread_id,
                    t.thread_key,
                    COUNT(turns.turn_id) AS turn_count,
                    MAX(turns.turn_id) AS last_turn_id
                FROM threads t
                LEFT JOIN turns ON turns.thread_id = t.thread_id
                WHERE t.session_id = ?
                GROUP BY t.thread_id, t.thread_key
                ORDER BY t.thread_id ASC
                """,
                (session_id,),
            ).fetchall()

            previous_row = conn.execute(
                "SELECT value FROM app_meta WHERE key = ?",
                ("previous_thread_id",),
            ).fetchone()
            previous_thread_id = int(previous_row["value"]) if previous_row is not None else None

            threads = [
                ThreadSummaryView(
                    thread_id=int(row["thread_id"]),
                    thread_key=str(row["thread_key"]),
                    turn_count=int(row["turn_count"] or 0),
                    last_turn_id=int(row["last_turn_id"]) if row["last_turn_id"] is not None else None,
                    is_active=int(row["thread_id"]) == active_thread_id,
                    is_previous=int(row["thread_id"]) == previous_thread_id,
                )
                for row in rows
            ]

            active_thread = next((thread for thread in threads if thread.thread_id == active_thread_id), None)
            previous_thread = next((thread for thread in threads if thread.thread_id == previous_thread_id), None)
            active_key = active_thread.thread_key if active_thread is not None else ""
            previous_key = previous_thread.thread_key if previous_thread is not None else None
            return ThreadListView(
                session_id=session_id,
                active_thread_id=active_thread_id,
                active_thread_key=active_key,
                previous_thread_id=previous_thread_id,
                previous_thread_key=previous_key,
                threads=threads,
            )

    def create_turn(
        self,
        session_id: int,
        thread_id: int,
        thread_key: str,
        mode: str,
        user_message: str,
        assistant_reply: str,
        reply_backend: str,
        degraded: bool,
    ) -> TurnResult:
        created_at = utc_now()
        with sqlite3.connect(self.db_path) as conn:
            turn_count = int(
                conn.execute(
                    "SELECT COUNT(1) FROM turns WHERE thread_id = ?",
                    (thread_id,),
                ).fetchone()[0]
            )
            turn_index = turn_count + 1
            cur = conn.execute(
                """
                INSERT INTO turns(session_id, thread_id, mode, turn_index, user_message, assistant_reply, reply_backend, degraded, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    thread_id,
                    mode,
                    turn_index,
                    user_message,
                    assistant_reply,
                    reply_backend,
                    int(degraded),
                    created_at.isoformat(),
                ),
            )
            conn.commit()
            turn_id = int(cur.lastrowid)
        return TurnResult(
            turn_id=turn_id,
            session_id=session_id,
            thread_id=thread_id,
            thread_key=thread_key,
            mode=mode,
            turn_index=turn_index,
            user_message=user_message,
            assistant_reply=assistant_reply,
            reply_backend=reply_backend,
            degraded=degraded,
            created_at=created_at,
        )

    def create_trace_events(
        self,
        session_id: int,
        thread_id: int,
        turn_id: int,
        mode: str,
        backend: str,
        degraded: bool,
        events: list[dict[str, object]],
    ) -> list[TraceEventRecord]:
        created_at = utc_now()
        trace_records: list[TraceEventRecord] = []
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                payload = json.dumps(event.get("payload", {}), sort_keys=True)
                cur = conn.execute(
                    """
                    INSERT INTO trace_events(session_id, thread_id, turn_id, mode, event_name, backend, degraded, payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        thread_id,
                        turn_id,
                        mode,
                        str(event["event_name"]),
                        backend,
                        int(degraded),
                        payload,
                        created_at.isoformat(),
                    ),
                )
                trace_records.append(
                    TraceEventRecord(
                        trace_id=int(cur.lastrowid),
                        session_id=session_id,
                        thread_id=thread_id,
                        turn_id=turn_id,
                        mode=mode,
                        event_name=str(event["event_name"]),
                        backend=backend,
                        degraded=degraded,
                        payload=payload,
                        created_at=created_at,
                    )
                )
            conn.commit()
        return trace_records

    def read_last_turn_trace(self) -> LastTurnTraceView:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            turn_row = conn.execute(
                """
                SELECT turns.*, threads.thread_key
                FROM turns
                INNER JOIN threads ON turns.thread_id = threads.thread_id
                ORDER BY turns.turn_id DESC
                LIMIT 1
                """
            ).fetchone()
            if turn_row is None:
                return LastTurnTraceView(turn=None, trace_events=[])

            turn = TurnResult(
                turn_id=int(turn_row["turn_id"]),
                session_id=int(turn_row["session_id"]),
                thread_id=int(turn_row["thread_id"]),
                thread_key=str(turn_row["thread_key"]),
                mode=str(turn_row["mode"]),
                turn_index=int(turn_row["turn_index"]),
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
                    thread_id=int(row["thread_id"]),
                    turn_id=int(row["turn_id"]),
                    mode=str(row["mode"]),
                    event_name=str(row["event_name"]),
                    backend=str(row["backend"]),
                    degraded=bool(row["degraded"]),
                    payload=str(row["payload"]),
                    created_at=datetime.fromisoformat(str(row["created_at"])),
                )
                for row in rows
            ]
            return LastTurnTraceView(turn=turn, trace_events=trace_events)
