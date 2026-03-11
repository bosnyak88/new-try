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

## Commands currently available

- `doctor`
- `trace-boot`
- `init-db`
- `talk --once "..." [--thread <thread_key>] [--mode <mode>]`
- `talk --live`
- `talk --script <path>`
- `session-status`
- `thread-list`
- `trace-last`


## Natural routing phrases (deterministic)

- switch/return existing thread: `vissza a <thread_key> szálra`, `menjünk vissza a <thread_key> szálra`, `váltsunk a <thread_key> szálra`
- return to previous thread: `vissza az előző szálra`, `folytassuk az előzőt`, `térjünk vissza az előző témára`
- create/switch thread: `új szál: <thread_key>`, `legyen új szál: <thread_key>`, `nyiss új szálat: <thread_key>`
- named topic-shift aliases: `más téma: <thread_key>`, `új téma: <thread_key>`, `egy másik dolog: <thread_key>`
- unmatched text defaults to active-thread continuation
- precedence: explicit `--thread`/`--mode` > live slash commands > named thread phrases > previous-thread/topic-shift phrases > continue active
