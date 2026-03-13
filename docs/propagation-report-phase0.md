
## 0.11.0 - REBUILD-011 snapshot-backed conversational recall/resume + response-plan foundation

- Added first-class contracts for turn interpretation, recall requests/resolution, response-plan structure, and corresponding trace metadata payloads.
- Added dedicated orchestration modules: `turn_interpret`, `thread_recall`, and `response_plan`; integrated them into shared turn execution used by once/live/script.
- Added snapshot-backed deterministic recall/resume handling for current/previous/named thread targets, with explicit clarification on ambiguous unresolved requests.
- Added reply-plan rendering boundary (`reply/plan_renderer.py`) so response planning stays separate from final textual rendering.
- Extended trace with `turn_interpreted`, `recall_resolved`, `response_plan_built` while preserving route/context/snapshot events.
- Extended conversation config and example config with recall/response-plan knobs.
- Updated docs and deterministic test coverage for recall/resume behavior and trace propagation.

## REBUILD-009 deterministic thread recap / resume foundation

- Added recap contracts (`RecapTarget`, `RecapRequest`, `ThreadRecapLine`, `ThreadRecapView`, recap query/trace contracts).
- Added dedicated recap orchestration module that projects deterministic recap views from existing context packs.
- Added `thread-recap` CLI command with `--current`, `--previous`, named target, and optional `--limit`.
- Added deterministic recap query handling inside shared turn execution so once/live/script reuse exactly one recap path.
- Extended turn trace propagation with recap metadata events: `recap_query_recognized`, `thread_recap_built`.
- Added deterministic CLI/live tests for recap command targets, missing-target handling, recap-query responses, shared output kind, non-mutation of active thread, and trace visibility.

## REBUILD-008 propagation addendum

- Added first-class thread context-pack contracts (`ThreadContextTurn`, `ThreadContextPack`, `ThreadContextRequest`, `ThreadContextView`) and execution-time context load result metadata.
- Added shared projection module for current/previous/named context inspection and execution-target context loading.
- Added `thread-view` CLI command surface (`--current`, `--previous`, named thread key, optional `--limit`).
- Extended trace with `thread_context_loaded` event so once/live/script execution paths expose loaded-context metadata.
- Updated config/docs/tests to keep contracts/orchestration/persistence/trace/CLI alignment explicit without reintroducing monolithic pipeline architecture.


## REBUILD-007 propagation

- Contracts extended with first-class pending-route proposal/status/resolution types.
- Orchestration now runs a shared pre-turn route/pending resolver across once/live/script paths.
- Persistence now stores pending-route state explicitly in `app_meta.pending_route`.
- CLI `session-status` and scripted live output expose pending metadata.
- Trace payloads include pending proposal/resolution metadata.

# Propagation report — REBUILD-006 deterministic topic-shift + previous-thread foundation

## Direct changes

- Extended active conversation contracts/state with explicit `previous_thread_id` / `previous_thread_key`.
- Extended route contracts with `SWITCH_PREVIOUS` and before/after transition metadata.
- Expanded deterministic Hungarian-first routing with previous-thread return phrases and topic-shift aliases.
- Kept one shared route/state resolution path in turn orchestration used by once/live/script execution for normal talk turns.
- Extended session/thread inspection CLI outputs for current + previous thread visibility.
- Extended trace payloads with route decision transition fields (before/after + previous-thread context).

## Supported deterministic phrases

- Return/switch existing thread: `vissza a <thread_key> szálra`, `menjünk vissza a <thread_key> szálra`, `váltsunk a <thread_key> szálra`
- Return to previous thread: `vissza az előző szálra`, `folytassuk az előzőt`, `térjünk vissza az előző témára`
- Create/switch thread: `új szál: <thread_key>`, `legyen új szál: <thread_key>`, `nyiss új szálat: <thread_key>`
- Topic-shift aliases: `más téma: <thread_key>`, `új téma: <thread_key>`, `egy másik dolog: <thread_key>`

## Precedence

1. explicit CLI overrides (`--thread`, `--mode`)
2. explicit live slash commands
3. deterministic named thread-routing phrases
4. deterministic previous-thread/topic-shift phrases
5. continue active thread

## Structural self-check

- No monolithic central pipeline was introduced.
- Routing, turn execution, live controls, persistence, trace, and CLI boundary remain separated.
- No fuzzy semantic routing, embeddings, or LLM intent routing was added.

## Deferred intentionally

- semantic/LLM routing
- embeddings or fuzzy intent classification
- broad thread history stack beyond current+previous
- summarization or memory graph


## Thread snapshot / handoff foundation

Syntaris now persists deterministic thread snapshot packs via a shared snapshot module (`orchestration/thread_snapshot.py`).
Snapshots are compact handoff packs built from the thread context window, excluding recap/control/pending turns by default.

CLI inspection uses `thread-snapshot --current`, `thread-snapshot --previous`, or `thread-snapshot <thread_key>` with optional `--refresh` and `--limit`.
Snapshots are also refreshed automatically when routing switches away from a thread so handoff state remains stable for later resume/recall work.

## REBUILD-012 propagation summary

- Contracts: introduced first-class focus/follow-up contracts (`ThreadFocusPack`, `FocusLine`, `FollowupResolution`, related trace structs).
- Orchestration: added shared focus build/load/update path and shared follow-up resolver.
- Persistence: added `thread_focus` table + migration-safe upsert/read.
- Reply/plan: response planning now marks and uses focus context.
- CLI: added `thread-focus` for current/previous/named inspection.
- Trace: added `thread_focus_loaded` and `followup_reference_resolved` events.


## REBUILD-013 propagation note

REBUILD-013 adds shared deterministic comparison-pack and answer-strategy orchestration between interpretation/recall/focus resolution and response-plan rendering. Once/live/script remain on the same execution path. Trace now records `comparison_pack_built` and `answer_strategy_selected` for inspectability without exposing chain-of-thought.

## REBUILD-014 propagation summary

- Contracts: added objective/decomposition/evidence/synthesis contracts and trace DTOs.
- Orchestration: added four dedicated reasoning modules and wired shared turn path (`execute_turn`) so once/live/script stay aligned.
- Response planning: now consumes objective/decomposition/evidence/synthesis artifacts explicitly.
- Trace: added objective/decomposition/evidence/synthesis events.
- Config/example + loader: added bounded reasoning/evidence controls.
- Tests: added deterministic objective/synthesis coverage and trace metadata assertions.

- REBUILD-014 follow-up: added shared preprocessing normalization in turn execution before interpretation/deliberation/objective/decomposition, plus mojibake regression tests at CLI/unit level.

- REBUILD-014 follow-up: explicit current-vs-previous compare phrases now map to `turn_interpreted.kind=compare_previous` (clean + mojibake forms), ensuring intent precedence is preserved through deliberation/strategy/response-plan and trace output matches visible behavior.

## REBUILD-015 propagation addendum

Text normalization/repair was propagated across contracts-adjacent runtime behavior, orchestration, persistence migration, derived artifacts, response rendering, trace readability, CLI outputs, and regression coverage.

- REBUILD-015 follow-up: fixed previous-thread legacy artifact pollution by making dirty persisted snapshot/focus detection trigger actual rebuild-and-writeback; previous recall now resolves from refreshed clean artifacts.

- REBUILD-015 follow-up-2: added stale artifact freshness enforcement (`last_turn_id`/`turn_count` checks) so current snapshot/recall paths no longer reuse outdated persisted packs.

- REBUILD-015 follow-up-3: strengthened line-level degraded-pattern detection (including observed forms like `errĺ‘l`, `beszĂ©ljĂĽnk`, `elĺ‘zĺ‘`, `hasonlĂ­tsd`) and enforced transitive historical cleanup in snapshot rebuild/writeback.

- REBUILD-015 follow-up-4: added recap/summary flattening in snapshot line construction to reduce recursive summary-of-summary pollution while preserving deterministic recall behavior.

## REBUILD-016 personal-entry/owner-intro propagation

Reviewed and updated layers:
- contracts: added explicit personal-entry interpretation contracts and minimal owner identity profile contract
- orchestration: deterministic personal-entry detection + response planning path, including explicit intro/owner/return distinctions
- persistence: minimal explicit identity persistence through `app_meta` keys (`owner_name`, `owner_relation`)
- trace: `turn_interpreted` payload extended with personal-entry metadata
- CLI/runtime behavior: once/live/script continue to use shared turn path with deterministic no-LLM compatibility
- docs/changelog/tests: updated for operator visibility and deterministic regression coverage

Guardrails kept:
- no architecture redesign
- no fake-memory claims
- no broad profile inference
- no menu-style interrogation


## REBUILD-017 owner-aware intake bridge propagation

- contracts: extended personal-entry signal with explicit intake kinds and optional declared focus/direction fields
- orchestration: deterministic HU-first intake interpretation for personal chat / concrete help / focus setting / resume directions
- reply/renderer: direction-specific compact intake responses with at most one natural next-step question
- persistence: unchanged minimal identity persistence (`owner_name`, `owner_relation`) only; no broad profile graph added
- trace: `turn_interpreted` now carries explicit declared focus/direction metadata when present
- tests: added deterministic regression coverage for intake bridge sequences and trace metadata
