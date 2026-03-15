# Canonical Contracts and Schemas

- Dokumentum státusz: **kanonikus semantikai contract-spec**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 06, 07, 10, 13, 14**

## Dokumentum célja

Ez a dokumentum nem a kódbeli pontos mezőneveket akarja leképezni, hanem a Syntaris kötelező semantikai contractjait.
Ha a kódban más mezőnevek vannak, azokhoz kötelező mappingot fenntartani.

## 1. Általános contract-szabály

- A semantikai jelentés kanonikus, a technikai mezőnév cserélhető.
- Ha egy contract-elemet a kód átnevez vagy áthelyez, a mappingot dokumentálni kell.
- A PR nem kész, ha contract-változás történt, de ez itt nincs szinkronba hozva.

## 2. Canonical Runtime Config Precedence Contract

A runtime/config izoláció szemantikailag kötelező része a rendszernek.

Kanonikus szabályok:
- **primary env override**: `SYNTARIS_DB_PATH`, `SYNTARIS_ARTIFACT_ALLOWED_ROOTS`
- **compat env alias**: `SYNTARIS_DB`, `SYNTARIS_SANDBOX_ROOTS`
- explicit temp config / per-test config **nem** írható felül ambient compat aliasokkal
- compat alias csak a default/example config útvonal mellett értelmezhető
- a test isolationt és a temp validationt a runtime-nak meg kell őriznie, nem elég „tiszta shellben” működnie

Követelmény:
A runtime által ténylegesen használt DB path és allowed roots visszaellenőrizhető legyen.

## 3. Canonical Turn Input Contract

A rendszerbe belépő turn minimálisan ezekből az elemekből áll:
- `turn_id`
- `timestamp`
- `raw_input`
- `normalized_input`
- `input_channel` (text, later voice, file, etc.)
- `style_constraints_explicit`
- `context_hint` (ha van)

Követelmény:
A raw input nem veszhet el, a normalized input pedig nem torzíthatja el a fő szándékot.

## 4. Canonical Interpret Pack Contract

A belső interpretációs csomagnak minimálisan tartalmaznia kell:
- `utterance_units`
- `candidate_intents`
- `workframe_candidates`
- `thread_candidates`
- `style_constraints_effective`
- `evidence_need`
- `memory_need`
- `risk_flags`
- `unknown_points`

## 5. Canonical Workframe Contract

A workframe egy semantikai döntés arról, milyen fajta interakció zajlik.
Kötelezően támogatandó canonical workframe-ek:
- `casual_chat`
- `focused_work`
- `planning`
- `recall`
- `compare`
- `evidence_intake`
- `source_query`
- `identity_relationship`
- `maintenance`
- `decision_support`
- `mode_control`
- `execution_request` (later)

Mezők:
- `workframe_current`
- `workframe_confidence`
- `workframe_lock`
- `workframe_reason`

## 6. Canonical Thread Contract

Kötelező thread-elemek:
- `active_thread_id`
- `thread_relation` (`current`, `previous`, `new`, `uncertain`, `historical_requested`)
- `thread_reason`
- `thread_before`
- `thread_after`

## 7. Canonical Source / Artifact Contract

Minden current vagy historical source azonosítható artifact- vagy source-azonosítóhoz kell kötődjön.

Minimum mezők:
- `artifact_id`
- `source_kind` (`raw_paste`, `once_file_import`, `local_text_file`, later others)
- `source_origin`
- `content_type`
- `size_bytes`
- `digest`
- `created_at`
- `last_read_at`
- `status`
- `thread_link`
- `turn_link`
- `source_role` (`current_primary`, `historical_candidate`, `trace_only`)
- `meaningful_source`
- `selection_reason`

Követelmény:
A current-source és historical-source megkülönböztetése explicit kell legyen.
A conversational `raw_paste` traceability célra fennmaradhat, de nem uralhatja a current-source választ, ha meaningful source létezik.

## 8. Canonical Evidence Context Contract

Minimum mezők:
- `current_evidence_context_id`
- `artifact_links`
- `active_source_artifact`
- `historical_source_candidates`
- `grounded_claims`
- `inferred_claims`
- `unknown_points`
- `current_source_valid`
- `historical_source_allowed`

Követelmény:
- sikeres `once_file_import` és `local_text_file` aktív, evidence-bearing source lehet;
- failed new read/import nem cserélheti le silent módon a prior active source-t;
- explicit historical wording esetén a historical source feloldása trace-elhető legyen.

## 9. Canonical Identity / Relationship Contract

Minimum mezők:
- `owner_identity_claims`
- `system_identity_claims`
- `relationship_frame`
- `relationship_confidence`
- `relationship_source`
- `relationship_applicability`

Követelmény:
A system és owner claim-ek nem moshatók össze.

## 10. Canonical Response Plan Contract

Minimum mezők:
- `target_workframe`
- `direct_answer_core`
- `followup_question_needed`
- `surface_mode` (`natural`, `structured`, `evidence`, `brief`, etc.)
- `style_constraints_honored`
- `thinking_indicator_allowed`
- `must_not_use_menu_surface`
- `must_not_ack_collapse`
- `source_honesty_mode`
- `source_resolution_mode`

## 11. Canonical Snapshot Contract

Minimum mezők:
- `active_thread_id`
- `current_workframe`
- `current_source_artifact`
- `current_source_kind`
- `historical_source_candidates`
- `recent_artifacts`
- `current_objective`
- `current_blocker`
- `next_step`
- `identity_frame`
- `relationship_frame`
- `open_questions`
- `decision_state`

## 12. Canonical Trace Event Contract

Minden lényeges trace-eseményhez minimálisan kell:
- `trace_event_id`
- `turn_id`
- `event_type`
- `event_time`
- `inputs_summary`
- `decision_summary`
- `source_links`
- `state_effects`
- `outcome`

Különösen Gate 1 / Gate 2 szempontból trace-elhető legyen:
- source selection,
- historical source resolution,
- failed read/import,
- style-constraint sérülés,
- ack-collapse jellegű fallback.

## 13. Canonical Audit Event Contract

Különösen source és execution irányban kötelező:
- `audit_event_id`
- `timestamp`
- `action`
- `target`
- `outcome`
- `reason`
- `thread_id`
- `turn_id`
- `artifact_id` (ha van)

## 14. Canonical Capability Record Contract

Minden capability rekordhoz kell:
- `capability_name`
- `status`
- `gate`
- `notes`
- `last_verified`
- `evidence_reference`

## 15. Canonical Validation Record Contract

Minden komolyabb validációhoz kell:
- `validation_run_id`
- `date`
- `scope`
- `commands`
- `environment`
- `logs`
- `result`
- `red_flags_found`
- `merge_recommendation`
- `file_update_report`

## 16. Semantikai invariánsok

1. current source nem lehet historical source-nak álcázva és fordítva.
2. explicit style-constraint sértés trace-elhető hibának számít.
3. owner és system identity külön mezőlogikát használ.
4. ack-collapse nem számíthat sikeres direct answernek.
5. modelljavaslat nem írhatja felül a központi truth-state-et.
6. reply és snapshot nem mondhat egymásnak ellent.
7. conversational `raw_paste` artifact nem válhat hallgatólagosan elsődleges current source-szá, ha van meaningful source.
8. failed once-file/read nem szennyezheti silent módon a current source állapotot.
9. explicit historical wording esetén a forrásválasztásnak szemantikusan relevánsnak kell lennie, nem tetszőleges „régi artifactnak”.

## 17. Rövid végső összefoglalás

A contractok célja, hogy a csapat ugyanazt értse state, trace, source, response plan és memória alatt.
Ha a kód ezt más nevekkel valósítja meg, a semantikai megfelelést akkor is fenn kell tartani.
