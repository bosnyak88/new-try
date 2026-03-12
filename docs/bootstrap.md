# Bootstrap and configuration

## Runtime boundary

`build_runtime()` constructs `RuntimeContext` from config sources only.
It does not load `.env` implicitly.

`syntaris.cli` remains the CLI boundary that calls `load_repo_env()` before runtime construction.

## Config keys

- `app`: name/environment
- `llm`: external llama runtime paths and host/port
- `paths`: `data_dir`, `db_path`
- `conversation`: `default_thread_key`, `default_mode`, `context_turn_window`
- `reply`: backend config (`deterministic` or `llama-http`)
- `trace`: trace flags

## DB bootstrap flow

`init-db`, talk, and loop flows call `PersistenceStore.initialize()`:

1. create `data_dir` (if missing)
2. create/open `db_path`
3. apply explicit SQLite schema
4. migrate legacy REBUILD-002 schema when needed
5. write schema metadata (`app_meta.schema_version=2`) and preserve active/previous thread pointers in `app_meta`

## Active state resolution

On one-shot talk, live loop entry, and status:

1. resolve active state from `app_meta` pointers
2. if missing, create new session + default thread and set default mode
3. apply thread/mode switches as requested and maintain previous-thread pointer whenever active thread changes
4. persist resulting active pointers for subsequent turns


## Routing bootstrap note

No additional boot-time providers are required for REBUILD-005 routing. The deterministic phrase matcher runs inside orchestration using persisted active state plus known thread list from storage.


- `app_meta.pending_route` stores deterministic pending-route proposals (held message + proposed thread + reason + metadata) until confirmation, rejection, or cancellation.


## Recap bootstrap note

No new providers or schema migrations are required for REBUILD-009 recap foundation. Recap views are projected from existing persisted thread turns through the context-pack loader, with the same bounded turn window (`conversation.context_turn_window` or explicit `--limit`).


## Thread snapshot / handoff foundation

Syntaris now persists deterministic thread snapshot packs via a shared snapshot module (`orchestration/thread_snapshot.py`).
Snapshots are compact handoff packs built from the thread context window, excluding recap/control/pending turns by default.

CLI inspection uses `thread-snapshot --current`, `thread-snapshot --previous`, or `thread-snapshot <thread_key>` with optional `--refresh` and `--limit`.
Snapshots are also refreshed automatically when routing switches away from a thread so handoff state remains stable for later resume/recall work.

## Conversation config additions (REBUILD-011)

`[conversation]` now also supports:

- `recall_line_limit` (default `3`): max snapshot lines rendered in recall/resume responses.
- `recall_prefer_snapshot` (default `true`): keeps recall resolution snapshot-backed.
- `response_followup_enabled` (default `true`): appends a short continuation question for recall/resume replies.

Environment overrides:
- `SYNTARIS_RECALL_LINE_LIMIT`
- `SYNTARIS_RECALL_PREFER_SNAPSHOT`
- `SYNTARIS_RESPONSE_FOLLOWUP_ENABLED`

## Focus bootstrap notes

`init-db` now creates `thread_focus` for deterministic active-focus persistence.
Focus config knobs are available under `[conversation]`: `focus_turn_window`, `focus_line_limit`, `followup_resolution_enabled`.


## Deliberation config

REBUILD-013 adds shared deterministic comparison-pack and answer-strategy orchestration between interpretation/recall/focus resolution and response-plan rendering. Once/live/script remain on the same execution path. Trace now records `comparison_pack_built` and `answer_strategy_selected` for inspectability without exposing chain-of-thought.

## REBUILD-014 config knobs

Conversation config now includes optional deterministic reasoning controls:
- `max_reasoning_units`
- `max_evidence_items_per_unit`
- `support_labeling_enabled`
- `synthesis_include_next_step`

These are loaded at bootstrap and apply uniformly to once/live/script shared execution.

## Text normalization bootstrap note

`init-db` now migrates `turns` with raw-text columns (`user_message_raw`, `assistant_reply_raw`) and backfills them from legacy rows to keep migration-safe auditability while enabling canonical persistence/display paths.

Migration/backfill remains schema-safe; legacy artifact cleanup happens through deterministic runtime rebuild/writeback on access (not destructive migration).

Operationally, no destructive migration is required for legacy snapshot/focus staleness; runtime freshness checks rebuild stale packs from canonical turn sources on first access.

Runtime artifact hygiene now validates both freshness and line-level cleanliness, then rebuilds from canonicalized turn sources when either gate fails.
