## 0.11.0 - REBUILD-011 snapshot-backed conversational recall/resume + response-plan foundation

- Introduced first-class contracts: `TurnInterpretation`, `RecallRequest`, `RecallResolution`, `ResponsePlan`, `ResponsePlanSection`, and trace metadata contracts for interpretation/recall/plan.
- Added shared orchestration layers (`turn_interpret.py`, `thread_recall.py`, `response_plan.py`) and removed recap-query branching from turn execution path.
- Added deterministic snapshot-backed conversational recall/resume responses in ordinary talk flows for current/previous/named thread requests.
- Added deterministic ambiguity clarification for unresolved resume-style phrasing (`folytassuk onnan`).
- Added plan rendering boundary (`reply/plan_renderer.py`) so response planning is separated from final rendering.
- Extended turn trace events with `turn_interpreted`, `recall_resolved`, and `response_plan_built`.
- Extended conversation config with recall/response-plan controls (`recall_line_limit`, `recall_prefer_snapshot`, `response_followup_enabled`).
- Updated README + architecture/bootstrap/operations/propagation docs and expanded deterministic tests across once/live/script + trace coverage.

## Unreleased

- REBUILD-014 fix: centralized early turn-message preprocessing in shared orchestration so explicit recall/compare intents are interpreted consistently before strategy selection.
- REBUILD-014 fix: added shared mojibake/diacritic-safe Hungarian text normalization so explicit previous-thread recall and compare intents are recognized before ordinary/direct fallback.
- REBUILD-014 fix: hardened Hungarian normalization/phrase coverage for explicit previous-thread recall and explicit compare phrasing so these intents no longer fall through to ordinary direct answers.
- REBUILD-014 fix: explicit current-vs-previous compare phrasing is now interpreted as `compare_previous` on the real talk runtime path (including mojibake forms), so trace intent kind, strategy selection, and final structured reply stay aligned.
- REBUILD-014 fix: response-plan now consumes synthesis sections for target direct-strategy intents (support-check/diagnose+next-step/compare), preventing generic `Rendben.` replies and preserving meaningful previous-thread recall behavior.
- REBUILD-014 fix: explicit support-check / diagnose+next-step / compare intent now deterministically triggers structured synthesis output instead of falling through to direct fallback or correction redirect in clear compare cases.
- REBUILD-014: Added shared deterministic objective framing, question decomposition, evidence-pack assembly, and answer synthesis layers.
- Introduced first-class contracts: `ObjectiveFrame`, `ObjectiveKind`, `ReasoningUnit`, `DecompositionPlan`, `EvidenceItem`, `EvidencePack`, `SupportLabel`, `SynthesisPlan`, and related trace contracts.
- Updated shared turn orchestration to flow: strategy -> objective -> decomposition -> evidence -> synthesis -> response plan.
- Extended trace events with `objective_framed`, `decomposition_built`, `evidence_pack_built`, `synthesis_plan_built`.
- Extended conversation config with bounded reasoning controls (`max_reasoning_units`, `max_evidence_items_per_unit`, `support_labeling_enabled`, `synthesis_include_next_step`).
- Added deterministic tests for multi-part decomposition, uncertainty/support labeling behavior, compare clarification behavior, and trace metadata propagation.

- REBUILD-013: Added deterministic deliberation input assembly, comparison-pack candidates, and answer-strategy selection as shared orchestration layers.
- Added first-class deliberation contracts (`DeliberationInput`, `DeliberationCandidate`, `ComparisonPack`, `AnswerStrategySelection`, clarification contracts).
- Extended response planning to consume selected answer strategy explicitly (direct/structured/recall/resume/correction/clarification/uncertainty-labeled).
- Extended trace metadata with `comparison_pack_built` and `answer_strategy_selected`.
- Added conversation config controls: `max_comparison_candidates`, `clarification_prefer_when_close`, `uncertainty_labeling_enabled`.
- Added deterministic tests for comparison close-call clarification vs clear winner behavior and CLI-level strategy/trace propagation.

- Added deterministic thread snapshot/handoff foundation with persisted `thread_snapshots` records and shared orchestration snapshot builder.
- Added `thread-snapshot` CLI command supporting `--current`, `--previous`, named thread keys, `--refresh`, and `--limit`.
- Added automatic snapshot refresh on deterministic thread transitions plus trace metadata (`thread_snapshot_refreshed`).

## 0.9.0 - REBUILD-009 deterministic thread recap / resume foundation

- Added first-class recap contracts: `RecapTarget`, `RecapRequest`, `ThreadRecapLine`, `ThreadRecapView`, recap query/trace metadata contracts.
- Introduced dedicated recap orchestration module to build deterministic recap views from `ThreadContextPack` data.
- Added `thread-recap` CLI command (`--current`, `--previous`, named thread, optional `--limit`).
- Added deterministic recap query phrase families (current/previous/named) in shared turn execution path; once/live/script now reuse the same recap handling.
- Recap query responses bypass reply adapter generation but persist normal turns and preserve active thread unless explicit routing already changed it.
- Extended turn trace events with recap handling metadata (`recap_query_recognized`, `thread_recap_built`).
- Added deterministic tests for recap command targets, missing target handling, recap query outputs, live-loop recap kind, and trace metadata propagation.

## 0.8.0 - REBUILD-008 deterministic thread context / resume-pack foundation

- Added first-class thread context contracts and config key `conversation.context_turn_window`.
- Added shared context projection/loading orchestration for current/previous/named/execution-target thread context packs.
- Added `thread-view` CLI command for deterministic context inspection (`--current`, `--previous`, named thread, optional `--limit`).
- Wired once/live/script turn execution through shared execution-target context load path and trace propagation.
- Extended trace events with `thread_context_loaded` metadata.
- Added deterministic tests for thread-view behavior, missing-context handling, bounded context windows, and trace alignment.

## 0.7.1 - REBUILD-007a previous-thread suggestive + BOM-safe script hotfix

- Reclassified `folytassuk az előzőt` as suggestive previous-thread routing so it creates pending clarification instead of direct switch.
- Fixed pending proposal trace/action propagation to preserve `propose_switch_previous` for previous-thread suggestive proposals.
- Made `talk --script` BOM-safe by reading script input with UTF-8 BOM handling (`utf-8-sig`).
- Added deterministic tests for previous-thread pending confirm/reject flow and BOM-prefixed scripted pending resolution.

## 0.7.0 - REBUILD-007 deterministic pending-route clarification foundation

- Added first-class pending-route contracts (`PendingRouteProposal`, `PendingRouteStatusView`, `PendingResolutionAction`, `SessionStatusView`) and extended route decision metadata.
- Extended deterministic Hungarian-first routing with suggestive phrase families that create persisted pending proposals instead of immediate route changes.
- Added deterministic yes/no pending resolution (confirm/reject/cancel) with held-message execution semantics.
- Kept once/live/script aligned through shared route+pending resolution before normal turn execution.
- Exposed pending state via `session-status` and propagated pending metadata to trace events and payloads.
- Added deterministic tests for suggestive pending proposals, confirmation/rejection/cancellation behavior, and live loop alignment.


## 0.6.0 - REBUILD-006 deterministic topic-shift + previous-thread foundation

- Extended conversation state contracts and persistence projection with explicit previous-thread metadata.
- Added `SWITCH_PREVIOUS` route action and explicit route transition metadata (before/after thread pointers).
- Expanded deterministic Hungarian-first routing with previous-thread return phrases and topic-shift alias phrases.
- Kept once/live/script normal turn execution aligned through shared route/state resolution in turn orchestration.
- Extended `session-status`, `thread-list`, and trace payload visibility for current vs previous thread context.
- Added deterministic tests for previous-thread return, topic-shift routing, slash-command precedence, and persistence of previous-thread state.
- Updated README and architecture/bootstrap/operations/propagation docs with precedence and scope details.

## 0.5.0 - REBUILD-005 deterministic natural thread routing

- Added first-class routing contracts and thread list view contracts.
- Added deterministic Hungarian-first natural route resolver for return/switch and create/switch thread phrases.
- Unified routing path in shared turn execution for once/live/script message execution.
- Added `thread-list` CLI command for known-thread inspection and active marker visibility.
- Extended turn trace events with route decision metadata.
- Added deterministic tests for route matching, route precedence, thread listing, and trace alignment.
- Updated architecture/operations/bootstrap/README propagation docs for route behavior and precedence.

## 0.4.0 - REBUILD-004 multi-turn conversational loop

- Added live-loop contracts: `LoopAction`, `LoopCommand`, `LiveConversationState`, and `LiveTurnOutput`.
- Introduced shared single-turn orchestration (`execute_turn`) and made `talk --once` a thin wrapper around it.
- Added multi-turn loop orchestration with in-loop control commands (`/allapot`, `/szal`, `/mod`, `/kilep` plus aliases).
- Expanded CLI with `talk --live` and deterministic scripted loop mode `talk --script <path>`.
- Extended trace events with turn execution source and loop lifecycle/control audit events.
- Added deterministic tests for scripted multi-turn flow, control behavior, state reuse, and trace alignment.
- Updated docs and propagation report to describe live-loop architecture and command surface.

## 0.3.0 - REBUILD-003 session/thread/mode foundation

- Added first-class contracts for mode/thread/active conversation state and talk request metadata.
- Added `[conversation]` config defaults (`default_thread_key`, `default_mode`).
- Extended persistence schema with `threads` and active-state pointers, and persisted thread/mode fields on turns and trace events.
- Added migration behavior to keep REBUILD-002 databases readable while moving to schema version 2.
- Updated orchestration to resolve/reuse active session/thread state and support `talk --once` thread/mode overrides.
- Added `session-status` CLI command and expanded `trace-last` output with session/thread/mode context.
- Extended deterministic tests for migration, active-state reuse, thread switching, mode persistence, and trace projection.

## 0.2.0 - REBUILD-002 vertical slice

- Added persistence package with SQLite bootstrap schema (`app_meta`, `sessions`, `turns`, `trace_events`).
- Extended runtime contracts with app paths, reply config, session/turn/trace entities, and persistence bootstrap result.
- Added reply adapter boundary with deterministic degraded fallback and optional llama-http integration.
- Added orchestration + CLI commands: `init-db`, `talk --once`, `trace-last`.
- Added turn-level trace persistence and inspection path.
- Updated docs, config templates, and tests for the modular talk slice.

## 0.1.0 - Phase-0 foundation

- Established modular package skeleton and contract-first runtime definitions.
- Added config and env templates with external llama server/model path support.
- Added CLI with `doctor` and `trace-boot` commands.
- Added baseline docs and tests for bootstrap behavior.

## Unreleased

- REBUILD-014 fix: centralized early turn-message preprocessing in shared orchestration so explicit recall/compare intents are interpreted consistently before strategy selection.
- REBUILD-014 fix: added shared mojibake/diacritic-safe Hungarian text normalization so explicit previous-thread recall and compare intents are recognized before ordinary/direct fallback.
- REBUILD-014 fix: hardened Hungarian normalization/phrase coverage for explicit previous-thread recall and explicit compare phrasing so these intents no longer fall through to ordinary direct answers.
- REBUILD-014 fix: explicit current-vs-previous compare phrasing is now interpreted as `compare_previous` on the real talk runtime path (including mojibake forms), so trace intent kind, strategy selection, and final structured reply stay aligned.
- REBUILD-014 fix: response-plan now consumes synthesis sections for target direct-strategy intents (support-check/diagnose+next-step/compare), preventing generic `Rendben.` replies and preserving meaningful previous-thread recall behavior.
- REBUILD-014 fix: explicit support-check / diagnose+next-step / compare intent now deterministically triggers structured synthesis output instead of falling through to direct fallback or correction redirect in clear compare cases.
- Added deterministic active-focus foundation (`thread_focus` persistence + orchestration) and new `thread-focus` CLI command.
- Added shared deterministic follow-up reference resolution on top of active focus with clarification fallback.
- Propagated focus metadata into response planning and trace events.

## Unreleased

- REBUILD-015: introduced shared canonical text normalization + mojibake repair policy and propagated it across talk/reasoning/persistence/derived artifacts/trace rendering.
- Added migration-safe raw text preservation columns in `turns` while persisting canonical text for runtime use.
- Added hygiene refresh behavior and regression tests for snapshot/focus/recall/compare quality.

- REBUILD-015 follow-up: fixed previous-thread legacy snapshot/focus pollution by loading persisted artifacts raw for hygiene checks and forcing rebuild/writeback when dirty, including previous recall paths.

- REBUILD-015 follow-up: enforced snapshot/focus freshness checks against live thread head and rebuild/writeback on stale persisted artifacts, including current recall path.
