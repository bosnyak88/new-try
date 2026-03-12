# Syntaris (Greenfield Rebuild)

Phase-0 runtime foundation with an explicit session/thread/mode conversational state layer plus deterministic pending-route clarification for suggestive routing phrases.

## Current scope

The current repository contains:

- a modular runtime foundation
- CLI-boundary `.env` autoload
- `doctor` and `trace-boot`
- SQLite bootstrap and persistence for sessions, threads, turns, active state, and trace events
- a reply adapter boundary with deterministic fallback behavior
- shared single-turn orchestration used by both one-shot and live loop execution
- live multi-turn conversation loop with explicit control commands
- deterministic Hungarian-first routing for named switching/creation plus previous-thread return phrases
- state and latest-trace inspection from CLI
- deterministic thread context-pack projection and inspection (`thread-view`)
- deterministic thread recap projection/inspection (`thread-recap`) and recap-query responses in talk flows

## Quick start

1. Copy environment template:
   - `cp .env.example .env`
2. Install in editable mode:
   - `python -m pip install -e .`
3. Initialize local DB:
   - `python -m syntaris.cli --config config/syntaris.example.toml init-db`
4. Run one turn:
   - `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia"`
5. Run live loop:
   - `python -m syntaris.cli --config config/syntaris.example.toml talk --live`
   - controls: `/allapot`, `/szal <thread_key>`, `/mod <mode>`, `/kilep`
6. Run deterministic scripted loop:
   - `python -m syntaris.cli --config config/syntaris.example.toml talk --script path/to/loop.txt`
7. Inspect active conversation state:
   - `python -m syntaris.cli --config config/syntaris.example.toml session-status`
8. List known threads:
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-list`
9. Inspect latest persisted trace:
   - `python -m syntaris.cli --config config/syntaris.example.toml trace-last`
10. Inspect thread context packs:
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-view --current`
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-view --previous`
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-view <thread_key>`
11. Inspect thread recap views:
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-recap --current`
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-recap --previous`
   - `python -m syntaris.cli --config config/syntaris.example.toml thread-recap <thread_key>`

## Commands currently available

- `doctor`
- `trace-boot`
- `init-db`
- `talk --once "..." [--thread <thread_key>] [--mode <mode>]`
- `talk --live`
- `talk --script <path>`
- `session-status`
- `thread-list`
- `thread-view [--current|--previous|<thread_key>] [--limit <N>]`
- `thread-recap [--current|--previous|<thread_key>] [--limit <N>]`
- `trace-last`


## Natural routing phrases (deterministic)

- switch/return existing thread: `vissza a <thread_key> szálra`, `menjünk vissza a <thread_key> szálra`, `váltsunk a <thread_key> szálra`
- return to previous thread: `vissza az előző szálra`, `folytassuk az előzőt`, `térjünk vissza az előző témára`
- create/switch thread: `új szál: <thread_key>`, `legyen új szál: <thread_key>`, `nyiss új szálat: <thread_key>`
- named topic-shift aliases: `más téma: <thread_key>`, `új téma: <thread_key>`, `egy másik dolog: <thread_key>`
- unmatched text defaults to active-thread continuation
- recap queries: `hol tartunk?`, `hol tartunk most?`, `mutasd a mostani szálat`, `foglald össze ezt a szálat`, `mutasd az előző szálat`, `foglald össze az előző szálat`, `hol tartunk az előző szálon?`, `mutasd a <thread_key> szálat`, `foglald össze a <thread_key> szálat`, `hol tartunk a <thread_key> szálon?`
- precedence: explicit `--thread`/`--mode` > live slash commands > pending resolution > explicit routing phrases > suggestive pending phrases > recap query phrases > continue active


## Thread snapshot / handoff foundation

Syntaris now persists deterministic thread snapshot packs via a shared snapshot module (`orchestration/thread_snapshot.py`).
Snapshots are compact handoff packs built from the thread context window, excluding recap/control/pending turns by default.

CLI inspection uses `thread-snapshot --current`, `thread-snapshot --previous`, or `thread-snapshot <thread_key>` with optional `--refresh` and `--limit`.
Snapshots are also refreshed automatically when routing switches away from a thread so handoff state remains stable for later resume/recall work.

## Conversational recall/resume foundation (REBUILD-011)

Ordinary `talk` turns now run a shared interpretation -> recall-resolution -> response-plan pipeline before final rendering.

- Current recall: `hol tartottunk?`
- Previous-thread recall: `az előző szálon mi volt?`
- Named recall/resume: `a <thread_key> szálon mi volt?`, `a <thread_key> szálat hozd vissza`
- Ambiguous resume (`folytassuk onnan`) returns a short clarification instead of guessing.

This uses persisted thread snapshots (from `thread-snapshot`) as the recall source, then renders a compact Hungarian response from an explicit `ResponsePlan`.

`trace-last` now includes `turn_interpreted`, `recall_resolved`, and `response_plan_built` events for once/live/script shared execution.
