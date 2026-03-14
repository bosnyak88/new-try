from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from syntaris.contracts.runtime import (
    ActiveConversationState,
    LastTurnTraceView,
    PendingRouteProposal,
    PendingRouteStatusView,
    PersistenceBootstrapResult,
    SessionRecord,
    SessionStatusView,
    ThreadContextPack,
    ThreadContextTurn,
    ThreadFocusPack,
    ThreadListView,
    ThreadRecord,
    ThreadSnapshotLine,
    ThreadSnapshotPack,
    SnapshotSourceMetadata,
    FocusLine,
    FocusSourceMetadata,
    ThreadSummaryView,
    TraceEventRecord,
    TurnResult,
    OwnerIdentityProfile,
    PersonalMemoryView,
    ClaimCapture,
    ClaimScope,
    ClaimKind,
    ScopedStateItem,
    ScopedStateStatus,
    ScopedStateView,
    ThreadWeaveState,
    ThreadRelationKind,
    ConclusionStatus,
    ApplicabilityStatus,
    ConclusionValidityStatus,
    TemporaryStateLifecycle,
    ThreadLifecycleStatus,
)
from syntaris.persistence.schema import SCHEMA_SQL, SCHEMA_VERSION
from syntaris.orchestration.text_normalize import clean_display_text, normalize_text


def _dirty_marker_count(text: str) -> int:
    markers = ("Ã", "Å", "Ă", "ĺ", "Ĺ", "�")
    return sum(text.count(marker) for marker in markers)


def _best_canonical_text(stored_text: str, raw_text: str | None) -> str:
    stored_canonical = normalize_text(stored_text).canonical_text
    if raw_text is None:
        return stored_canonical

    raw_canonical = normalize_text(raw_text).canonical_text
    stored_score = _dirty_marker_count(stored_canonical)
    raw_score = _dirty_marker_count(raw_canonical)
    if raw_score < stored_score:
        return raw_canonical
    return stored_canonical


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_scoped_state_status(
    *,
    scope: ClaimScope,
    active: bool,
    created_at: datetime,
    now_local: datetime,
    short_stale_minutes: int,
    same_day_stale_minutes: int,
) -> ScopedStateStatus:
    if not active:
        return ScopedStateStatus.EXPIRED
    if scope == ClaimScope.STABLE:
        return ScopedStateStatus.ACTIVE

    created_local = created_at.astimezone(now_local.tzinfo)
    if scope in {ClaimScope.DAY, ClaimScope.SESSION} and created_local.date() != now_local.date():
        return ScopedStateStatus.EXPIRED
    delta_minutes = max(0, int((now_local - created_local).total_seconds() // 60))
    if delta_minutes <= short_stale_minutes:
        return ScopedStateStatus.ACTIVE
    if delta_minutes <= same_day_stale_minutes:
        return ScopedStateStatus.STALE
    return ScopedStateStatus.EXPIRED


def _parse_pending_route(value: str | None) -> PendingRouteStatusView | None:
    if value is None:
        return None
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return None
    required = {"pending_action", "pending_thread_key", "pending_reason", "pending_original_message", "source", "proposed_at"}
    if not required.issubset(set(data.keys())):
        return None
    return PendingRouteStatusView(
        pending_action=str(data["pending_action"]),
        pending_thread_key=str(data["pending_thread_key"]),
        pending_reason=str(data["pending_reason"]),
        pending_original_message=str(data["pending_original_message"]),
        match_pattern=str(data["match_pattern"]) if data.get("match_pattern") is not None else None,
        source=str(data["source"]),
        proposed_at=str(data["proposed_at"]),
    )


def _pending_status_from_proposal(proposal: PendingRouteProposal) -> PendingRouteStatusView:
    return PendingRouteStatusView(
        pending_action="switch_thread",
        pending_thread_key=proposal.proposed_thread_key,
        pending_reason=proposal.reason,
        pending_original_message=proposal.held_user_message,
        match_pattern=proposal.match_pattern,
        source=proposal.source,
        proposed_at=proposal.proposed_at,
    )


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

        turn_cols = {row[1] for row in conn.execute("PRAGMA table_info(turns)").fetchall()}
        if turn_cols and "user_message_raw" not in turn_cols:
            conn.execute("ALTER TABLE turns ADD COLUMN user_message_raw TEXT")
        if turn_cols and "assistant_reply_raw" not in turn_cols:
            conn.execute("ALTER TABLE turns ADD COLUMN assistant_reply_raw TEXT")

        turn_cols = {row[1] for row in conn.execute("PRAGMA table_info(turns)").fetchall()}
        if "user_message_raw" in turn_cols:
            conn.execute("UPDATE turns SET user_message_raw = user_message WHERE user_message_raw IS NULL")
        if "assistant_reply_raw" in turn_cols:
            conn.execute("UPDATE turns SET assistant_reply_raw = assistant_reply WHERE assistant_reply_raw IS NULL")

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

        snapshot_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(thread_snapshots)").fetchall()
        }
        if snapshot_cols and "thread_key" not in snapshot_cols:
            conn.execute("ALTER TABLE thread_snapshots ADD COLUMN thread_key TEXT")
        if snapshot_cols and "thread_weave_json" not in snapshot_cols:
            conn.execute("ALTER TABLE thread_snapshots ADD COLUMN thread_weave_json TEXT")


        claims_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='personal_claims'").fetchone()
        if claims_exists is None:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS personal_claims (
                    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    thread_id INTEGER,
                    claim_kind TEXT NOT NULL,
                    claim_scope TEXT NOT NULL,
                    claim_value TEXT NOT NULL,
                    source_turn_id INTEGER NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    superseded_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY(thread_id) REFERENCES threads(thread_id),
                    FOREIGN KEY(source_turn_id) REFERENCES turns(turn_id)
                )
                """
            )

        focus_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='thread_focus'").fetchone()
        if focus_exists is None:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thread_focus (
                    focus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    thread_id INTEGER NOT NULL UNIQUE,
                    thread_key TEXT NOT NULL,
                    last_turn_id INTEGER,
                    focus_updated_at TEXT NOT NULL,
                    focus_source_turn_count INTEGER NOT NULL,
                    source_turn_count INTEGER NOT NULL,
                    included_turn_count INTEGER NOT NULL,
                    filtered_recap_turn_count INTEGER NOT NULL,
                    filtered_pending_turn_count INTEGER NOT NULL,
                    filtered_control_turn_count INTEGER NOT NULL,
                    focus_lines_json TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
                )
                """
            )
        else:
            focus_cols = {row[1] for row in conn.execute("PRAGMA table_info(thread_focus)").fetchall()}
            if focus_cols and "thread_weave_json" not in focus_cols:
                conn.execute("ALTER TABLE thread_focus ADD COLUMN thread_weave_json TEXT")

    def _serialize_thread_weave(self, weave: ThreadWeaveState | None) -> str | None:
        if weave is None:
            return None
        return json.dumps(
            {
                "relation": weave.relation.value,
                "main_thread_key": weave.main_thread_key,
                "related_thread_key": weave.related_thread_key,
                "detour_thread_key": weave.detour_thread_key,
                "conclusion_status": weave.conclusion_status.value,
                "conclusion_text": weave.conclusion_text,
                "applicability_status": weave.applicability_status.value,
                "applicability_reason": weave.applicability_reason,
                "conclusion_validity": weave.conclusion_validity.value,
                "temporary_state_lifecycle": weave.temporary_state_lifecycle.value,
                "thread_lifecycle": weave.thread_lifecycle.value,
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def _deserialize_thread_weave(self, payload: str | None) -> ThreadWeaveState | None:
        if payload is None:
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        try:
            return ThreadWeaveState(
                relation=ThreadRelationKind(str(data.get("relation", ThreadRelationKind.RELATION_UNKNOWN.value))),
                main_thread_key=str(data["main_thread_key"]) if data.get("main_thread_key") is not None else None,
                related_thread_key=str(data["related_thread_key"]) if data.get("related_thread_key") is not None else None,
                detour_thread_key=str(data["detour_thread_key"]) if data.get("detour_thread_key") is not None else None,
                conclusion_status=ConclusionStatus(str(data.get("conclusion_status", ConclusionStatus.NONE.value))),
                conclusion_text=str(data["conclusion_text"]) if data.get("conclusion_text") is not None else None,
                applicability_status=ApplicabilityStatus(str(data.get("applicability_status", ApplicabilityStatus.UNCERTAIN.value))),
                applicability_reason=str(data["applicability_reason"]) if data.get("applicability_reason") is not None else None,
                conclusion_validity=ConclusionValidityStatus(str(data.get("conclusion_validity", ConclusionValidityStatus.HISTORICAL_REMINDER.value))),
                temporary_state_lifecycle=TemporaryStateLifecycle(str(data.get("temporary_state_lifecycle", TemporaryStateLifecycle.AGED_STALE.value))),
                thread_lifecycle=ThreadLifecycleStatus(str(data.get("thread_lifecycle", ThreadLifecycleStatus.ACTIVE.value))),
            )
        except Exception:
            return None

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
                "SELECT key, value FROM app_meta WHERE key IN ('active_session_id', 'active_thread_id', 'active_mode', 'previous_thread_id', 'pending_route')"
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
                pending_route=_parse_pending_route(values.get("pending_route")),
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

    def set_pending_route(self, proposal: PendingRouteProposal) -> PendingRouteStatusView:
        pending = _pending_status_from_proposal(proposal)
        payload = json.dumps(
            {
                "pending_action": pending.pending_action,
                "pending_thread_key": pending.pending_thread_key,
                "pending_reason": pending.pending_reason,
                "pending_original_message": pending.pending_original_message,
                "match_pattern": pending.match_pattern,
                "source": pending.source,
                "proposed_at": pending.proposed_at,
            },
            sort_keys=True,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                ("pending_route", payload),
            )
            conn.commit()
        return pending

    def clear_pending_route(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM app_meta WHERE key = ?", ("pending_route",))
            conn.commit()

    def get_personal_memory(
        self,
        session_id: int,
        thread_id: int,
        *,
        now: datetime,
        timezone_name: str,
        short_stale_minutes: int,
        same_day_stale_minutes: int,
    ) -> PersonalMemoryView:
        now_local = now.astimezone(ZoneInfo(timezone_name))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            stable_rows = conn.execute(
                """
                SELECT claim_kind, claim_value
                FROM personal_claims
                WHERE session_id = ? AND claim_scope = 'stable' AND active = 1
                """,
                (session_id,),
            ).fetchall()
            scoped_rows = conn.execute(
                """
                SELECT claim_kind, claim_scope, claim_value, source_turn_id, active, created_at, superseded_at
                FROM personal_claims
                WHERE session_id = ?
                  AND claim_scope IN ('day', 'session', 'thread')
                  AND (thread_id = ? OR claim_scope IN ('day', 'session'))
                ORDER BY claim_id DESC
                """,
                (session_id, thread_id),
            ).fetchall()

        stable = {str(r["claim_kind"]): str(r["claim_value"]) for r in stable_rows}
        scoped_items: list[ScopedStateItem] = []
        latest_by_kind: dict[str, ScopedStateItem] = {}
        for row in scoped_rows:
            scope = ClaimScope(str(row["claim_scope"]))
            status = _resolve_scoped_state_status(
                scope=scope,
                active=bool(int(row["active"])),
                created_at=datetime.fromisoformat(str(row["created_at"])),
                now_local=now_local,
                short_stale_minutes=short_stale_minutes,
                same_day_stale_minutes=same_day_stale_minutes,
            )
            item = ScopedStateItem(
                kind=ClaimKind(str(row["claim_kind"])),
                value=str(row["claim_value"]),
                scope=scope,
                status=status,
                source_turn_id=int(row["source_turn_id"]),
                created_at_iso=str(row["created_at"]),
                superseded_at_iso=str(row["superseded_at"]) if row["superseded_at"] is not None else None,
            )
            scoped_items.append(item)
            key = item.kind.value
            if key not in latest_by_kind:
                latest_by_kind[key] = item

        focus_item = latest_by_kind.get(ClaimKind.CURRENT_FOCUS.value)
        direction_item = latest_by_kind.get(ClaimKind.CURRENT_DIRECTION.value)

        return PersonalMemoryView(
            owner_name=stable.get("owner_name"),
            system_name=stable.get("system_name"),
            owner_relation=stable.get("owner_relation"),
            system_role=stable.get("system_role"),
            current_focus=focus_item.value if focus_item is not None else None,
            current_direction=direction_item.value if direction_item is not None else None,
            current_focus_status=focus_item.status if focus_item is not None else None,
            current_direction_status=direction_item.status if direction_item is not None else None,
            scoped_state=ScopedStateView(items=scoped_items),
        )

    def capture_claims(self, session_id: int, thread_id: int, source_turn_id: int, captures: list[ClaimCapture], created_at: datetime | None = None) -> None:
        if not captures:
            return
        created_at_iso = (created_at or utc_now()).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for item in captures:
                scoped_thread_id = thread_id if item.scope == ClaimScope.THREAD else None
                conn.execute(
                    """
                    UPDATE personal_claims
                    SET active = 0, superseded_at = ?
                    WHERE session_id = ? AND claim_kind = ? AND claim_scope = ?
                      AND (thread_id = ? OR (? IS NULL AND thread_id IS NULL))
                      AND active = 1
                    """,
                    (created_at_iso, session_id, item.kind.value, item.scope.value, scoped_thread_id, scoped_thread_id),
                )
                conn.execute(
                    """
                    INSERT INTO personal_claims(
                        session_id, thread_id, claim_kind, claim_scope, claim_value, source_turn_id, active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        session_id,
                        scoped_thread_id,
                        item.kind.value,
                        item.scope.value,
                        clean_display_text(item.value),
                        source_turn_id,
                        created_at_iso,
                    ),
                )
            conn.commit()

    def get_owner_identity(self) -> OwnerIdentityProfile:
        state = self.get_active_state()
        if state is None:
            return OwnerIdentityProfile()
        now = utc_now()
        memory = self.get_personal_memory(
            session_id=state.session_id,
            thread_id=state.thread_id,
            now=now,
            timezone_name="UTC",
            short_stale_minutes=120,
            same_day_stale_minutes=480,
        )
        return OwnerIdentityProfile(
            owner_name=memory.owner_name,
            system_name=memory.system_name,
            owner_relation=memory.owner_relation,
            system_role=memory.system_role,
        )

    def set_owner_identity(self, owner_name: str | None = None, system_name: str | None = None, owner_relation: str | None = None, system_role: str | None = None) -> OwnerIdentityProfile:
        state = self.get_active_state()
        if state is None:
            return OwnerIdentityProfile()
        captures: list[ClaimCapture] = []
        if owner_name:
            captures.append(ClaimCapture(kind=ClaimKind.OWNER_NAME, value=owner_name, scope=ClaimScope.STABLE))
        if system_name:
            captures.append(ClaimCapture(kind=ClaimKind.SYSTEM_NAME, value=system_name, scope=ClaimScope.STABLE))
        if owner_relation:
            captures.append(ClaimCapture(kind=ClaimKind.OWNER_RELATION, value=owner_relation, scope=ClaimScope.STABLE))
        if system_role:
            captures.append(ClaimCapture(kind=ClaimKind.SYSTEM_ROLE, value=system_role, scope=ClaimScope.STABLE))
        if captures:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT MAX(turn_id) AS turn_id FROM turns WHERE session_id = ?",
                    (state.session_id,),
                ).fetchone()
                source_turn_id = int(row["turn_id"]) if row is not None and row["turn_id"] is not None else 0
            if source_turn_id > 0:
                self.capture_claims(state.session_id, state.thread_id, source_turn_id, captures)
        return self.get_owner_identity()

    def get_session_status_view(self, default_thread_key: str, default_mode: str) -> SessionStatusView:
        state = self.resolve_or_create_active(default_thread_key=default_thread_key, default_mode=default_mode)
        return SessionStatusView(
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




    def get_previous_thread(self) -> ThreadRecord | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            previous_row = conn.execute(
                "SELECT value FROM app_meta WHERE key = ?",
                ("previous_thread_id",),
            ).fetchone()
            if previous_row is None:
                return None
            row = conn.execute(
                "SELECT thread_id, session_id, thread_key, created_at FROM threads WHERE thread_id = ?",
                (int(previous_row["value"]),),
            ).fetchone()
            if row is None:
                return None
            return ThreadRecord(
                thread_id=int(row["thread_id"]),
                session_id=int(row["session_id"]),
                thread_key=str(row["thread_key"]),
                created_at=datetime.fromisoformat(str(row["created_at"])),
            )

    def get_thread_by_key(self, session_id: int, thread_key: str) -> ThreadRecord | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT thread_id, session_id, thread_key, created_at FROM threads WHERE session_id = ? AND thread_key = ?",
                (session_id, thread_key),
            ).fetchone()
            if row is None:
                return None
            return ThreadRecord(
                thread_id=int(row["thread_id"]),
                session_id=int(row["session_id"]),
                thread_key=str(row["thread_key"]),
                created_at=datetime.fromisoformat(str(row["created_at"])),
            )

    def build_thread_context_pack(self, thread_id: int, mode: str, turn_window: int) -> ThreadContextPack | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            thread_row = conn.execute(
                "SELECT thread_id, session_id, thread_key FROM threads WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            if thread_row is None:
                return None

            turn_count, last_turn_id = conn.execute(
                "SELECT COUNT(1), MAX(turn_id) FROM turns WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()

            rows = conn.execute(
                """
                SELECT turn_id, turn_index, user_message, assistant_reply, user_message_raw, assistant_reply_raw, reply_backend, degraded
                FROM turns
                WHERE thread_id = ?
                ORDER BY turn_id DESC
                LIMIT ?
                """,
                (thread_id, max(1, turn_window)),
            ).fetchall()

            recent_turns = [
                ThreadContextTurn(
                    turn_id=int(row["turn_id"]),
                    turn_index=int(row["turn_index"]),
                    user_message=clean_display_text(
                        _best_canonical_text(
                            stored_text=str(row["user_message"]),
                            raw_text=str(row["user_message_raw"]) if row["user_message_raw"] is not None else None,
                        )
                    ),
                    assistant_reply=clean_display_text(
                        _best_canonical_text(
                            stored_text=str(row["assistant_reply"]),
                            raw_text=str(row["assistant_reply_raw"]) if row["assistant_reply_raw"] is not None else None,
                        )
                    ),
                    backend=str(row["reply_backend"]),
                    degraded=bool(row["degraded"]),
                )
                for row in reversed(rows)
            ]

            previous_row = conn.execute(
                "SELECT value FROM app_meta WHERE key = ?",
                ("previous_thread_id",),
            ).fetchone()
            previous_thread_id = int(previous_row["value"]) if previous_row is not None else None
            previous_thread_key = None
            if previous_thread_id is not None:
                prev = conn.execute(
                    "SELECT thread_key FROM threads WHERE thread_id = ?",
                    (previous_thread_id,),
                ).fetchone()
                if prev is not None:
                    previous_thread_key = str(prev["thread_key"])

            return ThreadContextPack(
                session_id=int(thread_row["session_id"]),
                thread_id=int(thread_row["thread_id"]),
                thread_key=str(thread_row["thread_key"]),
                mode=mode,
                turn_count=int(turn_count or 0),
                last_turn_id=int(last_turn_id) if last_turn_id is not None else None,
                recent_turns=recent_turns,
                previous_thread_id=previous_thread_id,
                previous_thread_key=previous_thread_key,
            )

    def get_thread_turn_head(self, thread_id: int) -> tuple[int, int | None]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(1), MAX(turn_id) FROM turns WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            assert row is not None
            return int(row[0] or 0), int(row[1]) if row[1] is not None else None


    def upsert_thread_snapshot(self, snapshot: ThreadSnapshotPack) -> None:
        lines_json = json.dumps(
            [
                {
                    "turn_id": line.turn_id,
                    "turn_index": line.turn_index,
                    "user_message": clean_display_text(line.user_message),
                    "assistant_reply": clean_display_text(line.assistant_reply),
                }
                for line in snapshot.snapshot_lines
            ],
            ensure_ascii=False,
            sort_keys=True,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO thread_snapshots(
                    session_id, thread_id, thread_key, mode, turn_count, last_turn_id,
                    snapshot_built_at, source_turn_count, included_turn_count,
                    filtered_recap_turn_count, filtered_pending_turn_count, filtered_control_turn_count,
                    snapshot_lines_json, snapshot_text, previous_thread_id, previous_thread_key, thread_weave_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    session_id=excluded.session_id,
                    thread_key=excluded.thread_key,
                    mode=excluded.mode,
                    turn_count=excluded.turn_count,
                    last_turn_id=excluded.last_turn_id,
                    snapshot_built_at=excluded.snapshot_built_at,
                    source_turn_count=excluded.source_turn_count,
                    included_turn_count=excluded.included_turn_count,
                    filtered_recap_turn_count=excluded.filtered_recap_turn_count,
                    filtered_pending_turn_count=excluded.filtered_pending_turn_count,
                    filtered_control_turn_count=excluded.filtered_control_turn_count,
                    snapshot_lines_json=excluded.snapshot_lines_json,
                    snapshot_text=excluded.snapshot_text,
                    previous_thread_id=excluded.previous_thread_id,
                    previous_thread_key=excluded.previous_thread_key,
                    thread_weave_json=excluded.thread_weave_json
                """,
                (
                    snapshot.session_id,
                    snapshot.thread_id,
                    snapshot.thread_key,
                    snapshot.mode,
                    snapshot.turn_count,
                    snapshot.last_turn_id,
                    snapshot.snapshot_built_at.isoformat(),
                    snapshot.source_metadata.source_turn_count,
                    snapshot.source_metadata.included_turn_count,
                    snapshot.source_metadata.filtered_recap_turn_count,
                    snapshot.source_metadata.filtered_pending_turn_count,
                    snapshot.source_metadata.filtered_control_turn_count,
                    lines_json,
                    clean_display_text(snapshot.snapshot_text),
                    snapshot.previous_thread_id,
                    snapshot.previous_thread_key,
                    self._serialize_thread_weave(snapshot.thread_weave_state),
                ),
            )
            conn.commit()

    def read_thread_snapshot(self, thread_id: int) -> ThreadSnapshotPack | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM thread_snapshots WHERE thread_id = ?", (thread_id,)).fetchone()
            if row is None:
                return None
            line_data = json.loads(str(row["snapshot_lines_json"]))
            lines = [
                ThreadSnapshotLine(
                    turn_id=int(item["turn_id"]),
                    turn_index=int(item["turn_index"]),
                    user_message=str(item["user_message"]),
                    assistant_reply=str(item["assistant_reply"]),
                )
                for item in line_data
            ]
            return ThreadSnapshotPack(
                session_id=int(row["session_id"]),
                thread_id=int(row["thread_id"]),
                thread_key=str(row["thread_key"]),
                mode=str(row["mode"]),
                turn_count=int(row["turn_count"]),
                last_turn_id=int(row["last_turn_id"]) if row["last_turn_id"] is not None else None,
                snapshot_built_at=datetime.fromisoformat(str(row["snapshot_built_at"])),
                source_metadata=SnapshotSourceMetadata(
                    source_turn_count=int(row["source_turn_count"]),
                    included_turn_count=int(row["included_turn_count"]),
                    filtered_recap_turn_count=int(row["filtered_recap_turn_count"]),
                    filtered_pending_turn_count=int(row["filtered_pending_turn_count"]),
                    filtered_control_turn_count=int(row["filtered_control_turn_count"]),
                ),
                snapshot_lines=lines,
                snapshot_text=str(row["snapshot_text"]),
                previous_thread_id=int(row["previous_thread_id"]) if row["previous_thread_id"] is not None else None,
                previous_thread_key=str(row["previous_thread_key"]) if row["previous_thread_key"] is not None else None,
                thread_weave_state=self._deserialize_thread_weave(str(row["thread_weave_json"]) if row["thread_weave_json"] is not None else None),
            )

    def upsert_thread_focus(self, focus: ThreadFocusPack) -> None:
        lines_json = json.dumps([{"key": line.key, "text": clean_display_text(line.text)} for line in focus.focus_lines], ensure_ascii=False, sort_keys=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO thread_focus(
                    session_id, thread_id, thread_key, last_turn_id, focus_updated_at,
                    focus_source_turn_count, source_turn_count, included_turn_count,
                    filtered_recap_turn_count, filtered_pending_turn_count, filtered_control_turn_count,
                    focus_lines_json, thread_weave_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    session_id=excluded.session_id,
                    thread_key=excluded.thread_key,
                    last_turn_id=excluded.last_turn_id,
                    focus_updated_at=excluded.focus_updated_at,
                    focus_source_turn_count=excluded.focus_source_turn_count,
                    source_turn_count=excluded.source_turn_count,
                    included_turn_count=excluded.included_turn_count,
                    filtered_recap_turn_count=excluded.filtered_recap_turn_count,
                    filtered_pending_turn_count=excluded.filtered_pending_turn_count,
                    filtered_control_turn_count=excluded.filtered_control_turn_count,
                    focus_lines_json=excluded.focus_lines_json,
                    thread_weave_json=excluded.thread_weave_json
                """,
                (
                    focus.session_id,
                    focus.thread_id,
                    focus.thread_key,
                    focus.last_turn_id,
                    focus.focus_updated_at.isoformat(),
                    focus.focus_source_turn_count,
                    focus.source_metadata.source_turn_count,
                    focus.source_metadata.included_turn_count,
                    focus.source_metadata.filtered_recap_turn_count,
                    focus.source_metadata.filtered_pending_turn_count,
                    focus.source_metadata.filtered_control_turn_count,
                    lines_json,
                    self._serialize_thread_weave(focus.thread_weave_state),
                ),
            )
            conn.commit()

    def read_thread_focus(self, thread_id: int) -> ThreadFocusPack | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM thread_focus WHERE thread_id = ?", (thread_id,)).fetchone()
            if row is None:
                return None
            line_data = json.loads(str(row["focus_lines_json"]))
            lines = [FocusLine(key=str(item["key"]), text=str(item["text"])) for item in line_data]
            return ThreadFocusPack(
                session_id=int(row["session_id"]),
                thread_id=int(row["thread_id"]),
                thread_key=str(row["thread_key"]),
                last_turn_id=int(row["last_turn_id"]) if row["last_turn_id"] is not None else None,
                focus_updated_at=datetime.fromisoformat(str(row["focus_updated_at"])),
                focus_source_turn_count=int(row["focus_source_turn_count"]),
                focus_lines=lines,
                source_metadata=FocusSourceMetadata(
                    source_turn_count=int(row["source_turn_count"]),
                    included_turn_count=int(row["included_turn_count"]),
                    filtered_recap_turn_count=int(row["filtered_recap_turn_count"]),
                    filtered_pending_turn_count=int(row["filtered_pending_turn_count"]),
                    filtered_control_turn_count=int(row["filtered_control_turn_count"]),
                ),
                thread_weave_state=self._deserialize_thread_weave(str(row["thread_weave_json"]) if row["thread_weave_json"] is not None else None),
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


    def read_last_turn_at(self, thread_id: int) -> datetime | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT created_at FROM turns WHERE thread_id = ? ORDER BY turn_id DESC LIMIT 1",
                (thread_id,),
            ).fetchone()
            if row is None or row[0] is None:
                return None
            return datetime.fromisoformat(str(row[0]))

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
        created_at: datetime | None = None,
    ) -> TurnResult:
        created_at = created_at or utc_now()
        normalized_user = normalize_text(user_message)
        normalized_reply = normalize_text(assistant_reply)
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
                INSERT INTO turns(session_id, thread_id, mode, turn_index, user_message, user_message_raw, assistant_reply, assistant_reply_raw, reply_backend, degraded, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    thread_id,
                    mode,
                    turn_index,
                    normalized_user.canonical_text,
                    normalized_user.raw_text,
                    normalized_reply.canonical_text,
                    normalized_reply.raw_text,
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
            user_message=normalized_user.canonical_text,
            assistant_reply=normalized_reply.canonical_text,
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
                rows = conn.execute(
                    "SELECT * FROM trace_events WHERE turn_id = 0 ORDER BY trace_id DESC LIMIT 20"
                ).fetchall()
                rows = list(reversed(rows))
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
                return LastTurnTraceView(turn=None, trace_events=trace_events)

            turn = TurnResult(
                turn_id=int(turn_row["turn_id"]),
                session_id=int(turn_row["session_id"]),
                thread_id=int(turn_row["thread_id"]),
                thread_key=str(turn_row["thread_key"]),
                mode=str(turn_row["mode"]),
                turn_index=int(turn_row["turn_index"]),
                user_message=clean_display_text(
                    _best_canonical_text(
                        stored_text=str(turn_row["user_message"]),
                        raw_text=str(turn_row["user_message_raw"]) if "user_message_raw" in turn_row.keys() and turn_row["user_message_raw"] is not None else None,
                    )
                ),
                assistant_reply=clean_display_text(
                    _best_canonical_text(
                        stored_text=str(turn_row["assistant_reply"]),
                        raw_text=str(turn_row["assistant_reply_raw"]) if "assistant_reply_raw" in turn_row.keys() and turn_row["assistant_reply_raw"] is not None else None,
                    )
                ),
                reply_backend=str(turn_row["reply_backend"]),
                degraded=bool(turn_row["degraded"]),
                created_at=datetime.fromisoformat(str(turn_row["created_at"])),
            )

            rows = conn.execute(
                "SELECT * FROM trace_events WHERE turn_id = ? ORDER BY trace_id ASC",
                (turn.turn_id,),
            ).fetchall()
            loop_rows = conn.execute(
                """
                SELECT * FROM trace_events
                WHERE turn_id = 0
                AND session_id = ?
                AND thread_id = ?
                ORDER BY trace_id DESC
                LIMIT 20
                """,
                (turn.session_id, turn.thread_id),
            ).fetchall()
            loop_rows = list(reversed(loop_rows))

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
            trace_events.extend(
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
                for row in loop_rows
            )
            return LastTurnTraceView(turn=turn, trace_events=trace_events)
