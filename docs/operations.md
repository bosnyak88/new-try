# Operations baseline

## Commands

### `doctor`

Validates external llama binary/model path presence and port sanity.

### `init-db`

Initializes runtime data directory and SQLite schema/migrations.

### `talk --once "..." [--thread <thread_key>] [--mode <mode>]`

Runs one turn through shared `execute_turn()` orchestration.

### `talk --live`

Runs interactive multi-turn loop:

- normal text => persisted talk turn (via shared deterministic route resolver)
- `/allapot` => compact status
- `/szal <thread_key>` => switch active thread
- `/mod <mode>` => switch active mode
- `/kilep` => exit cleanly

### `talk --script <path>`

Runs deterministic non-interactive loop from newline-delimited input file.
Each output row is emitted as compact JSON for tests.

### `session-status`

Prints compact JSON view of active conversation state, including `previous_thread_id` and `previous_thread_key`.

### `trace-last`

Prints latest persisted turn and its trace events including session/thread/mode/backend/degraded context, plus thread context-load metadata.


### `thread-list`

Prints known threads for the active session with active/previous markers, turn counts, and last turn ids.

### `thread-view --current | --previous | <thread_key> [--limit <N>]`

Prints compact deterministic context-pack JSON for active, previous, or named thread target.
Includes session/thread metadata, bounded recent turns, and previous-thread pointers when present.

## Route precedence

1. explicit CLI flags (`--thread`, `--mode`)
2. live slash control commands (`/szal`, `/mod`, etc.)
3. deterministic named thread-routing phrases
4. deterministic previous-thread/topic-shift phrases
5. active-thread continuation fallback


## Pending-route operations

- `session-status` now surfaces `pending_route` metadata when clarification is waiting.
- `trace-last` includes proposal/resolution metadata (`pending_route_proposed`, `pending_route_confirmed`, `pending_route_rejected`, `pending_route_cancelled`).


### `thread-recap [--current|--previous|<thread_key>] [--limit <N>]`

Builds and prints a compact deterministic recap view for the selected thread target.

- `--current`: active thread recap
- `--previous`: previous-thread recap (returns `found=false` when missing)
- `<thread_key>`: named-thread recap

### Recap queries in talk flows

The same recap builder is used in once/live/script execution when deterministic recap phrases are matched:

- current: `hol tartunk?`, `hol tartunk most?`, `mutasd a mostani szálat`, `foglald össze ezt a szálat`
- previous: `mutasd az előző szálat`, `foglald össze az előző szálat`, `hol tartunk az előző szálon?`
- named: `mutasd a <thread_key> szálat`, `foglald össze a <thread_key> szálat`, `hol tartunk a <thread_key> szálon?`

Recap queries do not implicitly switch active thread and produce trace metadata for recap handling.


## Thread snapshot / handoff foundation

Syntaris now persists deterministic thread snapshot packs via a shared snapshot module (`orchestration/thread_snapshot.py`).
Snapshots are compact handoff packs built from the thread context window, excluding recap/control/pending turns by default.

CLI inspection uses `thread-snapshot --current`, `thread-snapshot --previous`, or `thread-snapshot <thread_key>` with optional `--refresh` and `--limit`.
Snapshots are also refreshed automatically when routing switches away from a thread so handoff state remains stable for later resume/recall work.

## Conversational recall/resume operations (REBUILD-011)

Use ordinary talk commands for recall/resume checks:

- `talk --once "hol tartottunk?"` (current thread)
- `talk --once "az előző szálon mi volt?"` (previous thread)
- `talk --once "a work szálat hozd vissza"` (named resume)
- `talk --once "folytassuk onnan"` (ambiguous -> clarification)

Operational distinction:

- `thread-view`: raw bounded context projection.
- `thread-recap`: deterministic recap projection output.
- `thread-snapshot`: persisted handoff/recall source pack.
- conversational recall/resume in `talk`: user-facing compact answers built from snapshot-backed `ResponsePlan`.

## Thread focus inspection

Use:
- `python -m syntaris.cli ... thread-focus --current`
- `python -m syntaris.cli ... thread-focus --previous`
- `python -m syntaris.cli ... thread-focus <thread_key>`
- add `--refresh` to force deterministic rebuild.


## Deliberation observability

REBUILD-013 adds shared deterministic comparison-pack and answer-strategy orchestration between interpretation/recall/focus resolution and response-plan rendering. Once/live/script remain on the same execution path. Trace now records `comparison_pack_built` and `answer_strategy_selected` for inspectability without exposing chain-of-thought.

## REBUILD-014 inspectability

Use `trace-last` after `talk` turns to inspect high-level reasoning metadata:
- `objective_framed`
- `decomposition_built`
- `evidence_pack_built`
- `synthesis_plan_built`

Events intentionally avoid hidden chain-of-thought and expose only safe summary-level structure.

Note: REBUILD-014 recall/compare intent matching is now preprocessing-hardened (diacritic/mojibake repair) in the shared turn path; `trace-last` should align with visible recall/structured compare output for explicit phrases.

## Operational text-hygiene behavior

If old persisted snapshot/focus artifacts contain degraded text, `thread-snapshot` / `thread-focus` will rebuild via hygiene refresh when needed (or immediately with `--refresh`).

Legacy previous-thread snapshot/focus payloads are no longer only cleaned in-memory: dirty detection now triggers real rebuild + persistence writeback from canonical turn sources.

Snapshot/focus views now enforce freshness: if persisted `last_turn_id`/`turn_count` is behind the live thread head, runtime performs deterministic rebuild+writeback before returning the artifact.

Operationally, snapshot hygiene is line-level (not only blob-level): dirty/degraded text inside any snapshot line forces rebuild/writeback.

`hol tartottunk?` / snapshot reuse now include recap-flattening safeguards so historical generated summaries do not recursively re-expand through snapshot-backed recall.

## Personal-entry deterministic checks (REBUILD-016)

Run on a clean DB:

- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia syntaris"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "én Árpi vagyok"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "szia syntaris én Árpi vagyok"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "én terveztem a rendszered"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "folytassuk innen"`

Expected:
- natural compact Hungarian reply
- no mojibake
- no bare `Rendben.` full reply
- no fake-memory overclaim
- one compact next-step question at most


## Owner-aware intake quick checks (REBUILD-017)
- `python -m syntaris.cli ... talk --once "ma beszélgetni szeretnék"`
- `python -m syntaris.cli ... talk --once "segíts a timesheetben"`
- `python -m syntaris.cli ... talk --once "a mai fókusz a syntaris"`
- `python -m syntaris.cli ... talk --once "folytassuk a syntarist"`

Expected: natural Hungarian, no bare `Rendben.`, one compact next-step prompt at most.


## Determinisztikus időtudat (REBUILD-018)
- REBUILD-018 üzemeltetési megjegyzés: Windowson a `tzdata` projektfüggőség automatikusan települ, ezért nincs külön kézi `pip install tzdata` operátori lépés.
- A runtime közös, tesztelhető órát (`RuntimeContext.clock`) és explicit időzónát (`[time].timezone`) használ.
- A rendszer daypart-érzékeny magyar köszönést ad (reggel/délelőtt/délután/este/éjjel).
- Visszatérésnél a válaszok csak perzisztált turn-időbélyeg + aktuális helyi idő alapján jeleznek gap-et (nincs megfigyelés- vagy fake-memory állítás).
- Relatív időkifejezések (`most`, `ma`, `tegnap`, `holnap`, `majd`) determinisztikusan kerülnek groundingra és trace-ben láthatók.
- Scope-határ: ez még nem reminder/executor/rutin-tanulás.


## Explicit-memory operational checks
Use `talk --once` with: `én Árpi vagyok`, `ki vagyok?`, `én terveztem a rendszered`, `mi a kapcsolatunk?`, `a mai fókusz a syntaris`, `mi a mostani fókusz?`, `mit tudsz rólam biztosan?`.
Use `trace-last` to confirm `explicit_claims_captured` appears after capture turns.
