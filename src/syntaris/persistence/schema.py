SCHEMA_VERSION = 4

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS threads (
    thread_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    thread_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(session_id, thread_key),
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS turns (
    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    thread_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    assistant_reply TEXT NOT NULL,
    reply_backend TEXT NOT NULL,
    degraded INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
);



CREATE TABLE IF NOT EXISTS thread_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    thread_id INTEGER NOT NULL UNIQUE,
    thread_key TEXT NOT NULL,
    mode TEXT NOT NULL,
    turn_count INTEGER NOT NULL,
    last_turn_id INTEGER,
    snapshot_built_at TEXT NOT NULL,
    source_turn_count INTEGER NOT NULL,
    included_turn_count INTEGER NOT NULL,
    filtered_recap_turn_count INTEGER NOT NULL,
    filtered_pending_turn_count INTEGER NOT NULL,
    filtered_control_turn_count INTEGER NOT NULL,
    snapshot_lines_json TEXT NOT NULL,
    snapshot_text TEXT NOT NULL,
    previous_thread_id INTEGER,
    previous_thread_key TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
);


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
);

CREATE TABLE IF NOT EXISTS trace_events (
    trace_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    thread_id INTEGER NOT NULL,
    turn_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    event_name TEXT NOT NULL,
    backend TEXT NOT NULL,
    degraded INTEGER NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(thread_id) REFERENCES threads(thread_id),
    FOREIGN KEY(turn_id) REFERENCES turns(turn_id)
);
"""
