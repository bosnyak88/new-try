import sqlite3

from syntaris.contracts.runtime import PendingRouteProposal
from syntaris.persistence.store import PersistenceStore


def test_initialize_creates_schema(tmp_path):
    db_path = tmp_path / "data" / "runtime.db"
    store = PersistenceStore(str(db_path))

    result = store.initialize(data_dir=str(tmp_path / "data"))

    assert result.schema_initialized is True
    assert result.schema_version == 2
    with sqlite3.connect(db_path) as conn:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"app_meta", "sessions", "threads", "turns", "trace_events"}.issubset(names)


def test_write_and_read_turn_and_trace(tmp_path):
    db_path = tmp_path / "runtime.db"
    store = PersistenceStore(str(db_path))
    store.initialize(data_dir=str(tmp_path))

    state = store.resolve_or_create_active(default_thread_key="default", default_mode="chat")
    turn = store.create_turn(
        session_id=state.session_id,
        thread_id=state.thread_id,
        thread_key=state.thread_key,
        mode="chat",
        user_message="hello",
        assistant_reply="world",
        reply_backend="deterministic",
        degraded=True,
    )
    store.create_trace_events(
        session_id=state.session_id,
        thread_id=state.thread_id,
        turn_id=turn.turn_id,
        mode="chat",
        backend="deterministic",
        degraded=True,
        events=[{"event_name": "turn_persisted", "payload": {"ok": True}}],
    )

    view = store.read_last_turn_trace()

    assert view.turn is not None
    assert view.turn.thread_key == "default"
    assert view.turn.mode == "chat"
    assert view.turn.user_message == "hello"
    assert len(view.trace_events) == 1
    assert view.trace_events[0].thread_id == state.thread_id


def test_v1_migration_adds_thread_mode_columns(tmp_path):
    db_path = tmp_path / "runtime.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO app_meta(key, value) VALUES ('schema_version', '1');
            CREATE TABLE sessions (session_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL);
            CREATE TABLE turns (
              turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              user_message TEXT NOT NULL,
              assistant_reply TEXT NOT NULL,
              reply_backend TEXT NOT NULL,
              degraded INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE trace_events (
              trace_id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              turn_id INTEGER NOT NULL,
              event_name TEXT NOT NULL,
              backend TEXT NOT NULL,
              degraded INTEGER NOT NULL,
              payload TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            INSERT INTO sessions(created_at) VALUES ('2024-01-01T00:00:00+00:00');
            INSERT INTO turns(session_id, user_message, assistant_reply, reply_backend, degraded, created_at)
            VALUES (1, 'old', 'data', 'deterministic', 1, '2024-01-01T00:00:01+00:00');
            INSERT INTO trace_events(session_id, turn_id, event_name, backend, degraded, payload, created_at)
            VALUES (1, 1, 'turn_persisted', 'deterministic', 1, '{}', '2024-01-01T00:00:01+00:00');
            """
        )

    store = PersistenceStore(str(db_path))
    store.initialize(data_dir=str(tmp_path))

    view = store.read_last_turn_trace()
    assert view.turn is not None
    assert view.turn.thread_key == "default"
    assert view.turn.mode == "chat"
    assert view.trace_events[0].mode == "chat"


def test_active_state_tracks_previous_thread(tmp_path):
    db_path = tmp_path / "runtime.db"
    store = PersistenceStore(str(db_path))
    store.initialize(data_dir=str(tmp_path))

    state = store.resolve_or_create_active(default_thread_key="default", default_mode="chat")
    work = store.open_or_create_thread(state.session_id, "work")
    store.set_active_state(session_id=state.session_id, thread_id=work.thread_id, mode="chat")
    back = store.get_active_state()

    assert back is not None
    assert back.thread_key == "work"
    assert back.previous_thread_key == "default"


def test_pending_route_roundtrip(tmp_path):
    db_path = tmp_path / "runtime.db"
    store = PersistenceStore(str(db_path))
    store.initialize(data_dir=str(tmp_path))

    state = store.resolve_or_create_active(default_thread_key="default", default_mode="chat")
    pending = store.set_pending_route(
        proposal=PendingRouteProposal(
            held_user_message="folytassuk a worköt",
            proposed_thread_key="work",
            current_thread_key="default",
            reason="matched_suggestive_named_thread_phrase",
            match_pattern="suggestive_named_folytassuk",
            source="talk_once",
            proposed_at="2024-01-01T00:00:00+00:00",
        )
    )
    assert pending.pending_thread_key == "work"

    status = store.get_session_status_view(default_thread_key="default", default_mode="chat")
    assert status.session_id == state.session_id
    assert status.pending_route is not None
    assert status.pending_route.pending_original_message == "folytassuk a worköt"

    store.clear_pending_route()
    cleared = store.get_session_status_view(default_thread_key="default", default_mode="chat")
    assert cleared.pending_route is None
