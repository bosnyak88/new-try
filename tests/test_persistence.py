import sqlite3

from syntaris.persistence.store import PersistenceStore


def test_initialize_creates_schema(tmp_path):
    db_path = tmp_path / "data" / "runtime.db"
    store = PersistenceStore(str(db_path))

    result = store.initialize(data_dir=str(tmp_path / "data"))

    assert result.schema_initialized is True
    with sqlite3.connect(db_path) as conn:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"app_meta", "sessions", "turns", "trace_events"}.issubset(names)


def test_write_and_read_turn_and_trace(tmp_path):
    db_path = tmp_path / "runtime.db"
    store = PersistenceStore(str(db_path))
    store.initialize(data_dir=str(tmp_path))

    session = store.create_session()
    turn = store.create_turn(
        session_id=session.session_id,
        user_message="hello",
        assistant_reply="world",
        reply_backend="deterministic",
        degraded=True,
    )
    store.create_trace_events(
        session_id=session.session_id,
        turn_id=turn.turn_id,
        backend="deterministic",
        degraded=True,
        events=[{"event_name": "turn_persisted", "payload": {"ok": True}}],
    )

    view = store.read_last_turn_trace()

    assert view.turn is not None
    assert view.turn.user_message == "hello"
    assert view.turn.assistant_reply == "world"
    assert len(view.trace_events) == 1
    assert view.trace_events[0].event_name == "turn_persisted"
