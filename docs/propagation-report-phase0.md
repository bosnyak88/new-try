# Propagation report — REBUILD-022 personal cognitive baseline propagation

## Scope
Contracts, orchestration, persistence semantics, reply surface, trace semantics, CLI smoke paths, config comments, tests, and top-level docs were reviewed.

## Changed
- contracts: memory-query and claim-capture trace extensions.
- orchestration: Hungarian memory-query interpretation extensions and response-surface certainty split.
- turns+trace: explicit capture counters (`stable_count`, `temporary_count`, `strengthened_count`).
- tests: regression coverage for new memory queries and trace payload semantics.
- docs/changelog/config comments synchronized to post-022 semantics.

## Reviewed intentionally unchanged
- schema/storage shape stayed on v6 (`personal_claims` already supports stable + scoped-state semantics).
- routing/recall/snapshot/focus orchestration modules remained coherent with current semantics.
- CLI remained thin (no orchestration migration into CLI).

## Removed
- none.

## Deferred (explicit non-goals)
- executor/tool workflows,
- BioGraph/profile graph,
- architecture redesign.


## REBUILD-023 propagation note
Reviewed core contracts/orchestration/reply/trace/CLI/tests/docs for workframe, objective, blocker, and next-step alignment. Added deterministic workframe derivation and trace event; no schema migration required in this pass.

## REBUILD-024 propagation note
Reviewed and propagated contracts/orchestration/reply/trace/tests/docs/config for missing-info, open-question, assumption/evidence, and decision-needed semantics. No schema migration was required; persistence remains context-first while snapshot/focus keep aligned derived workframe state.


## REBUILD-024 follow-up correction note
Narrow semantic correction pass: explicit blocker declaration now stays on blocker-update path, meta state-queries are inspection-only (no open-question writeback from query text), evidence-gap question family includes `mihez nincs még elég bizonyíték?`, and decision-status questions no longer force `decision_made` without grounded resolution. Snapshot/focus/trace now retain grounded state without meta-query pollution.


## REBUILD-025 propagation note
Full-system propagation pass completed for deterministic thread-weave/conclusion/applicability baseline.
- contracts: added authoritative relation/conclusion/applicability enums + `ThreadWeaveState` + `ThreadWeaveTrace`.
- orchestration: added `thread_weave.py` derivation and query-family detection; integrated into turns/response planning/snapshot/focus.
- persistence/schema: schema v7, added `thread_weave_json` columns and migration/read-write support in store.
- trace: added `thread_weave_state_derived` event.
- CLI: thread-snapshot/thread-focus JSON surfaces now include thread-weave payload.
- tests: added deterministic regressions for relation/conclusion/applicability answers, trace integrity, and snapshot/focus alignment.
- docs/config/changelog: synchronized to post-025 semantics.


## REBUILD-025 follow-up correction note
Narrow semantic correction pass on the same PR: detour declaration and return-to-main declaration are now explicitly captured as thread-weave updates, and relation/conclusion/applicability answers are derived from retained weave state (not generic fallback). Direct answers are aligned with snapshot/focus/trace (`thread_weave_state_derived`) for the in-thread main-vs-detour scenario.


## REBUILD-026 propagation note
- follow-up correction: raw evidence turn now emits explicit ingest acknowledgement and evidence query family (`hiba/következtetés/fontos rész/blocker/recall`) no longer falls back to generic filler.
- CLI boundary: added explicit deterministic multiline ingest path (`talk --once-file`, `talk --once-stdin`) and tests.
- response surface: evidence-query family now emits explicit no-evidence guidance when ingest state is absent (no generic filler).
Full-system propagation pass completed for deterministic large-text evidence ingest + source-grounding baseline.
- contracts/config: new evidence ingest/chunk/grounding DTOs and config knobs
- orchestration: evidence ingest reducer + evidence-pack integration + follow-up evidence reuse
- response/reply: source-grounded vs inferred/unresolved separation in answer surface
- trace: ingest/chunk/key-line visibility in `evidence_pack_built`
- tests: deterministic regressions for ingest extraction and follow-up grounded reuse
- docs/config/changelog: synchronized to post-026 semantics

Schema migration: not required in this phase (v7 unchanged).


## REBUILD-027 propagation snapshot
- contracts: extended `ThreadWeaveState` + trace DTO for maintenance lifecycle and conclusion validity
- orchestration: deterministic maintenance/applicability derivation updated, including park/return/close cues
- persistence: thread-weave serialization/deserialization updated for new lifecycle fields
- response surface: Hungarian-first lifecycle/maintenance wording added for update + query families
- trace: lifecycle and maintenance fields added to `thread_weave_state_derived` payload
- regression: added deterministic tests for memory maintenance, thread lifecycle maintenance, and applicability gate
- schema: unchanged (v7)


## REBUILD-028 narrow follow-up snapshot
- fixed interpretation/update routing gap where maintenance setup/update prompts were incorrectly collapsing into generic time-reference fallback
- expanded workframe blocker query/update detection for `blocker` phrasing (`mi a blocker most?`, `a blocker most ...`)
- added deterministic blocker replacement handling for `most már más a helyzet ... megszűnt ..., ... maradt gond`
- completed Scenario-A applicability/conclusion path so maintained conclusion is not left empty when supersession is explicitly present
- kept REBUILD-027 lifecycle cues and REBUILD-026 evidence behavior intact (validated by regressions)
- schema unchanged (v7)


## REBUILD-029 propagation note (live runtime stabilization)

### Changed
- `src/syntaris/orchestration/live_loop.py`: added visibility guard for empty live replies and explicit `live_surface_degraded` trace emission.
- `src/syntaris/reply/adapters.py`: hardened llama HTTP extraction for structured/malformed payloads and deterministic fallback on empty/malformed content.
- `tests/test_live_rendering.py`, `tests/test_reply_adapter.py`: added deterministic regressions for live visibility, degraded handling, greeting first-turn stability, once/live parity spot-check, and structured extraction fallback.

### Reviewed unchanged
- `src/syntaris/orchestration/turns.py`, `src/syntaris/trace/events.py`, `src/syntaris/contracts/runtime.py`, `src/syntaris/cli.py`, persistence schema/store modules.
- Evidence/workframe/thread-weave/maintenance orchestration modules were reviewed for regression risk; no behavior change required in this runtime-only fix.

### Schema/contracts
- No schema migration required.
- No contract shape change required; live visibility is enforced within existing `LiveTurnOutput.message` semantics and trace events.

### Scope control
- Kept separate from presence/persona/onboarding architecture work.
- Kept separate from executor/tooling/reminder concerns.


## REBUILD-030 propagation note (Windows live text-boundary follow-up)

### Changed
- `src/syntaris/orchestration/text_normalize.py`: added surrogate replacement and console-safe rendering helpers.
- `src/syntaris/persistence/store.py`: create-turn writes now use normalized surrogate-safe raw/canonical text; `read_last_turn_trace` now surfaces loop-level trace signals (`turn_id=0`) for bounded live failure visibility.
- `src/syntaris/orchestration/live_loop.py`: bounded exception handling around live turn execution with explicit degraded message + `live_turn_failed` trace, while keeping existing REBUILD-029 visibility guard.
- `src/syntaris/cli.py`: live output now goes through console-safe emission; sanitization emits `live_output_sanitized` trace.
- Added regressions: `tests/test_live_windows_console.py`, `tests/test_live_text_sanitization.py`, `tests/test_live_trace_honesty.py`.

### Reviewed unchanged
- `src/syntaris/orchestration/turns.py`, `src/syntaris/reply/*` (except previous REBUILD-029 hardening), contracts enums/DTOs, schema versioning migration files.
- REBUILD-026 evidence and REBUILD-027/028 maintenance routes reviewed for regressions.

### Schema/contracts
- Schema unchanged (v7).
- No contract redesign; behavior change implemented at normalization/live boundary + trace event payload level.

### Scope control
- Narrow live-runtime follow-up only (no identity/presence/onboarding redesign, no executor/workspace expansion).


## REBUILD-031 propagation note (Windows stdin mojibake/parity follow-up)

### Changed
- `src/syntaris/cli.py`: live non-tty path now decodes stdin bytes deterministically and records `live_input_repaired` trace when repair/degradation happened.
- `src/syntaris/orchestration/text_normalize.py`: added `decode_live_input_line` with bounded encoding candidates + mojibake repair scoring.
- `src/syntaris/persistence/store.py`: `trace-last` now includes recent loop-level events for same thread/session without time-cutoff loss so ingress-repair signals remain inspectable.
- Added regressions: `tests/test_live_input_decoding.py`, `tests/test_live_parity.py`.

### Reviewed unchanged
- `src/syntaris/orchestration/turns.py`, `src/syntaris/orchestration/live_loop.py`, `src/syntaris/reply/*`, contracts/schema remained stable for this narrow ingress parity fix.

### Schema/contracts
- Schema unchanged (v7).
- No contract redesign; only ingress decoding/trace observability behavior adjusted.

### Scope control
- Narrow live-ingress parity fix only; no presence/persona/onboarding redesign and no evidence/maintenance feature expansion.


## REBUILD-032 propagation snapshot
### Changed
- `src/syntaris/orchestration/live_loop.py`: added optional `on_output` callback and `reply_adapted_rendered` trace to expose generated/adapted output before console emission.
- `src/syntaris/cli.py`: live interactive path now streams emissions per output and records `reply_emit_attempted` / `reply_emitted_successfully` / `reply_emit_failed`; output writes are explicitly flushed.
- Added regressions: `tests/test_live_interactive_emit.py` for callback-order visibility and emit-honesty failure/success trace semantics.

### Reviewed unchanged
- `src/syntaris/orchestration/turns.py`, `src/syntaris/reply/*`, persistence schema/store core behavior, maintenance/evidence orchestration families.

### Schema/contracts
- Schema unchanged (v7).
- Contract shape unchanged; behavior extended via existing live loop/trace event payloads.


## REBUILD-033 propagation snapshot
### Changed
- `src/syntaris/contracts/runtime.py`: extended deterministic contracts with `ClaimKind.SYSTEM_NAME`, `MemoryQueryKind.WHO_ARE_YOU`, and owner/system identity fields in `OwnerIdentityProfile` + `PersonalMemoryView`.
- `src/syntaris/orchestration/turn_interpret.py`: widened HU identity intake coverage (`az én nevem ...`, `a te neved ...`, `én tervezlek és fejlesztelek`, `te a személyes kognitív rendszerem leszel`) and added `ki vagy te?` memory-query routing.
- `src/syntaris/orchestration/response_plan.py`: strengthened claim-capture acknowledgements and memory-query coherence so owner/system/relationship answers stay mutually aligned and non-filler.
- `src/syntaris/persistence/store.py`: propagated stable `system_name` persistence/readback into personal-memory/owner-identity views.
- Added deterministic regressions: `tests/test_identity_relationship.py`, `tests/test_presence_surface.py`.

### Reviewed unchanged
- Live transport/emission chain (`src/syntaris/orchestration/live_loop.py`, `src/syntaris/cli.py`) kept intact to preserve REBUILD-032 visibility/emit honesty and REBUILD-031 ingress parity.
- Evidence and maintenance families (`tests/test_evidence_grounded_talk.py`, `tests/test_maintenance_route_hijack.py`) validated unchanged behavior.
- Thread/snapshot/focus/trace architecture remained in current deterministic shape.

### Schema/contracts
- Schema unchanged (v7): `personal_claims` already supports additional stable claim kinds without migration.
- Contracts changed in a narrow, additive way for owner/system identity coherence.

### Scope control
- No workspace shell / tool bridge / execution engine / A/B orchestration broadening.
- No theatrical persona simulation; tone improvements remain bounded by explicit captured claims.


## REBUILD-033 follow-up completion note
### Changed
- `src/syntaris/orchestration/turn_interpret.py`: completed explicit relationship-frame intake for the non-"te" variant (`a személyes kognitív rendszerem leszel`) so the turn routes to deterministic claim capture instead of low-value fallback.
- `src/syntaris/orchestration/thread_weave.py`: added conservative relationship-frame derivation from explicit owner/system cues, including non-empty relation/conclusion/applicability semantics and relationship query/update trace tagging.
- Added deterministic regressions: `tests/test_relationship_alignment.py`, `tests/test_relationship_trace.py`.

### Reviewed unchanged
- `src/syntaris/orchestration/live_loop.py`, `src/syntaris/cli.py` (REBUILD-032/031/030 live guarantees preserved).
- Evidence and maintenance families verified via targeted suites (`tests/test_evidence_grounded_talk.py`, `tests/test_maintenance_route_hijack.py`).

### Schema/contracts
- Schema unchanged (v7).
- No contract migration required for this follow-up; completion is in interpretation + weave-state derivation/trace alignment.

### Scope control
- Kept as narrow in-place completion on REBUILD-033 branch/PR; no architecture redesign, no A/B orchestration, no workspace/tool bridge expansion.


## REBUILD-033 live-alignment completion note
### Changed
- `src/syntaris/orchestration/thread_weave.py`: completed live relationship alignment by deriving conservative non-empty weave semantics (`relation`/`conclusion`/`applicability`) from relationship-query + explicit owner/system signals, and exposing `relationship_query` in trace.
- Added deterministic live regressions: `tests/test_live_relationship_alignment.py`, `tests/test_live_relationship_trace.py`.

### Reviewed unchanged
- `src/syntaris/orchestration/live_loop.py`, `src/syntaris/cli.py` (emit/visibility/input hardening preserved).
- Identity/evidence/maintenance families and their deterministic suites remained green.

### Schema/contracts
- Schema unchanged (v7).
- Contract shapes unchanged in this completion pass.

### Scope control
- Narrow completion on existing REBUILD-033 branch/PR only; no architecture redesign or A/B/workspace/tooling expansion.


## REBUILD-034 propagation snapshot
### Changed
- `src/syntaris/orchestration/turn_interpret.py`: widened deterministic HU recognition for continuation/return prompts (`na folytassuk`, `vissza syntaris`, `hol tartottunk` variants) and added `miben segítesz nekem?` memory-query intake.
- `src/syntaris/orchestration/response_plan.py`: strengthened greeting + re-entry phrasing with active-context continuation cues; added conservative deterministic `HOW_HELP` response family.
- `src/syntaris/contracts/runtime.py`: additive `MemoryQueryKind.HOW_HELP` enum value for coherent identity/relationship/help follow-up surface.
- Added deterministic regressions: `tests/test_presence_entry.py`, `tests/test_continue_from_here.py`, `tests/test_presence_followups.py`, `tests/test_live_presence_parity.py`, `tests/test_return_thread_surface_trace.py`.

### Reviewed unchanged
- `src/syntaris/orchestration/turns.py`, `src/syntaris/orchestration/live_loop.py`, `src/syntaris/cli.py` (boundary/orchestration split preserved).
- `src/syntaris/persistence/*` and schema remained unchanged (v7), as existing retained-state substrate already supported truthful continuation and memory-query answers.
- Evidence/maintenance families stayed on existing deterministic routing/response contracts and were revalidated via targeted suites.

### Schema/contracts
- Schema unchanged (v7).
- Contracts changed minimally and additively (`MemoryQueryKind.HOW_HELP` only), no runtime contract breakage.

### Scope control
- Presence/conversation-surface baseline only; no execution orchestration, workspace-shell/tool bridge, or UI expansion scope added.


## REBUILD-034a narrow follow-up snapshot
### Changed
- `src/syntaris/cli.py`: hardened `talk --once-file` boundary with controlled `OSError` handling (deterministic non-zero exit + explicit JSON error payload) and emitted `once_file_read_failed` trace event for audit visibility.
- `src/syntaris/orchestration/turns.py`: tightened evidence-context reuse policy so implicit evidence follow-ups only continue a contiguous evidence thread; historical evidence reuse now requires explicit recall wording and can no longer silently substitute stale evidence after failed handoff attempts.
- Added deterministic regressions: `tests/test_once_file_boundary.py`, `tests/test_evidence_failed_ingest.py`, `tests/test_evidence_context_honesty.py`.

### Reviewed unchanged
- `src/syntaris/orchestration/response_plan.py`, `src/syntaris/orchestration/evidence_ingest.py`, `src/syntaris/orchestration/evidence_pack.py` (kept existing evidence rendering/ingest contracts).
- `src/syntaris/persistence/schema.py` and schema migration flow unchanged (v7).
- Presence/identity/maintenance suites preserved from REBUILD-034 and revalidated.

### Schema/contracts
- Schema unchanged (v7).
- Contracts unchanged in this narrow follow-up (behavioral routing fix + CLI boundary hardening only).

### Scope control
- Narrow truth-first correction on failed raw evidence handoff and stale-evidence substitution guard only; no broad presence/evidence redesign and no execution/UI expansion.

## REBUILD-035 artifact/source registry baseline snapshot
### Changed
- `src/syntaris/contracts/runtime.py`: additive artifact/source contracts (`ArtifactSourceKind`, `ArtifactRecord`, `SourceAuditRecord`) and evidence ingest traceability via `artifact_ids`; `ConversationConfig` now carries artifact read-only roots and max-read limit.
- `src/syntaris/persistence/schema.py`: schema v8 with additive `artifacts`, `turn_artifact_links`, and `source_audit_journal` tables.
- `src/syntaris/persistence/store.py`: additive persistence + query APIs for artifact upsert/list/show, turn↔artifact linkage, and source-audit journaling.
- `src/syntaris/orchestration/artifacts.py`: deterministic read-only local file bridge helpers (allowed-root guard, supported text extension gate, digest/id generation, lexical search).
- `src/syntaris/cli.py`: new read-only source commands (`artifact-find`, `artifact-read`, `artifact-list`, `artifact-show`, `audit-last`), plus once-file source-kind/origin propagation.
- `src/syntaris/orchestration/turns.py`: source artifact registration + linkage within existing turn orchestration; follow-up source-awareness can use retained artifact context without stale substitution.
- `src/syntaris/orchestration/evidence_ingest.py`, `src/syntaris/trace/events.py`: additive artifact provenance plumbing in ingest/trace payload.
- `src/syntaris/orchestration/response_plan.py`: explicit source-awareness response surface for "miből dolgozol most?" family with historical reuse disclosure.
- `src/syntaris/config/loader.py`, `config/syntaris.example.toml`: artifact bridge configuration load + example knobs.
- Added regressions: `tests/test_artifact_registry.py`, `tests/test_local_file_bridge.py`, `tests/test_source_context_visibility.py`, `tests/test_artifact_scope_guard.py`, `tests/test_artifact_audit.py`.
- Added capability truth doc: `docs/rebuild-035-capability-catalog.md`.

### Reviewed unchanged
- `src/syntaris/reply/*`: no adapter boundary expansion; deterministic reply backend split preserved.
- `src/syntaris/orchestration/live_loop.py`: no live loop behavior broadening.
- REBUILD-034/034a presence/evidence/maintenance families preserved through full-suite regression runs.

### Removed
- None.

### Deferred with reason
- PDF/Office/binary adapters and broad source parser framework: intentionally deferred to later adapter phase to keep REBUILD-035 read-only + deterministic baseline minimal.
- Any write-capable file operation, external app automation, permissioned execution/session orchestration, and shell/panel UI work: explicitly out of scope for this foundational source/artifact step.

## REBUILD-035a targeted acceptance follow-up snapshot
### Changed
- `src/syntaris/config/loader.py`: accepted runtime env aliases used by ops smoke (`SYNTARIS_DB` and `SYNTARIS_SANDBOX_ROOTS`) while preserving existing `SYNTARIS_DB_PATH` / `SYNTARIS_ARTIFACT_ALLOWED_ROOTS` precedence.
- `src/syntaris/orchestration/turns.py`: tightened current-source honesty so ordinary short conversational prompts no longer become dominant source artifacts; implicit evidence follow-ups respect continuity guard, source-awareness prompts still surface active source, once-file/local-file imports force evidence ingest linkage, and explicit historical wording can deterministically target earlier meaningful source artifacts.
- `src/syntaris/persistence/store.py`: added focused helpers for meaningful-source selection and artifact-backed turn text retrieval (`list_meaningful_source_artifacts`, `read_artifact_message_text`, `turn_has_meaningful_artifact`).
- `src/syntaris/orchestration/evidence_ingest.py`: added `force` ingest mode for trusted imported sources so once-file/local-file source follow-ups remain evidence-grounded even for short text inputs.
- Added deterministic follow-up regressions in `tests/test_rebuild035a_followup.py` (env alias runtime wiring, once-file evidence follow-up + explicit historical reuse, binary refusal inside allowed roots).
- Updated `tests/test_artifact_scope_guard.py` refusal assertions to verify outside-root vs unsupported/binary reason correctness.

### Reviewed unchanged
- `src/syntaris/cli.py` command surface kept stable (`artifact-find/read/list/show`, `audit-last`, `talk --once-file` failure handling).
- `src/syntaris/reply/*` adapter boundaries unchanged; no shell/UI/execution broadening.
- REBUILD-034/034a presence/identity/maintenance/evidence honesty suites preserved and rerun.

### Removed
- None.

### Deferred with reason
- No broad artifact parser expansion (PDF/Office/binary adapters) in this follow-up; limited to acceptance-blocking runtime wiring and source-selection honesty.
- No write-capable operations or shell/panel execution work; scope remains read-only source baseline.
