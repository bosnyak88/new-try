# Operations baseline (post-022)

## Required validation commands
- `python -m pytest -q`
- `python -m compileall -q src`
- `python -m syntaris.cli --config config/syntaris.example.toml init-db`

## Key runtime probes
- Owner intro / relationship: `én Árpi vagyok`, `én terveztem a rendszered`, `mi a kapcsolatunk?`
- Certainty split: `mit tudsz rólam biztosan?`, `mi csak feltételezés rólam?`, `ebből mi ideiglenes és mi biztos?`
- Continuity and recall: `hol tartottunk?`, `az előző szálon mi volt?`, `hasonlítsd össze a mostanit az előző szállal`
- State artifacts: `thread-snapshot --current|--previous`, `thread-focus --current|--previous`, `trace-last`


## Operational check (REBUILD-023)
Use `trace-last` to confirm `workframe_state_derived` is emitted after turns that ask for blocker/next-step/plan semantics.

- REBUILD-023 uncertainty audit: `trace-last` -> `workframe_state_derived` now includes `query_family` and `uncertainty_marked` to verify certainty-split and tentative proposal handling.

## Operational check (REBUILD-024)
Use `trace-last` and inspect `workframe_state_derived` for: `missing_info_status`, `open_question_status`, `assumption_status`, `decision_state`, `evidence_gap_status` plus count fields. This is the authoritative runtime audit surface for decision readiness.


## Operational check (REBUILD-025)
Use `trace-last` and inspect `thread_weave_state_derived` (`relation`, `conclusion_status`, `applicability_status`, `query_family`).
Also verify `thread-snapshot --current` and `thread-focus --current` include `thread_weave_state` payloads aligned with current workframe state.

- REBUILD-025 correction probe: after `közben kitértünk a live loop hibára` and `de a főszál továbbra is a rebuild-025`, check that `mi volt csak mellékszál?` returns the live-loop detour and `mi a főszál most?` returns rebuild-025 (not `unrelated_thread`).


## REBUILD-026 runtime probes (large text/evidence grounding)
- Expected on raw block turn: explicit ingest acknowledgement (`evidenciaként beemeltem`) before follow-up evidence questions.
- Deterministic multiline ingest (supported): `python -m syntaris.cli --config config/syntaris.example.toml talk --once-file ./sample.log`
- Deterministic multiline ingest from stdin (supported): `cat ./sample.log | python -m syntaris.cli --config config/syntaris.example.toml talk --once-stdin`
- If evidence was not ingested, evidence-query family now returns explicit no-evidence guidance (never generic filler).
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "bemásolok egy hosszabb konzolkimenetet"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "<többsoros log/traceback minta>"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "mi a lényeg ebből?"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "mi benne a valódi hiba?"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "mi biztosan látszik ebből?"`
- `python -m syntaris.cli --config config/syntaris.example.toml talk --once "mi csak következtetés?"`
- `python -m syntaris.cli --config config/syntaris.example.toml trace-last`

Expected: source-grounded lines are explicit, inferred/unresolved parts stay separated, and trace reports ingest/chunk/key-line counts.


## REBUILD-027 operations note
Operationally validate lifecycle semantics with Hungarian cues (`parkoljuk`, `vissza a főszálra`, `lezártuk`) and applicability prompts (`mi maradt érvényes`, `felülírja az új helyzet?`). Confirm `thread-snapshot`, `thread-focus`, and `trace-last` all show aligned maintenance status.


## REBUILD-029 live visibility smoke
- `python -m syntaris.cli --config "$CFG" init-db`
- `python -m syntaris.cli --config "$CFG" talk --once "szia syntaris én Árpi vagyok"`
- `printf "szia\nhol tartottunk?\n" | python -m syntaris.cli --config "$CFG" talk --live`
- `printf "szia syntaris\nszia syntaris én Árpi vagyok\nmit tudsz rólam biztosan?\n" | python -m syntaris.cli --config "$CFG" talk --live`
- Confirm each live turn emits visible text (no blank processed turn lines), and verify `python -m syntaris.cli --config "$CFG" trace-last` reflects any live-surface degradation via `live_surface_degraded` when triggered.


## REBUILD-030 live boundary smoke
- `python -m syntaris.cli --config "$CFG" init-db`
- `printf "szia\nhol tartottunk?\n" | python -m syntaris.cli --config "$CFG" talk --live`
- `printf "szia syntaris\nszia syntaris én Árpi vagyok\nmit tudsz rólam biztosan?\n" | python -m syntaris.cli --config "$CFG" talk --live`
- `python -m syntaris.cli --config "$CFG" trace-last`
- If constrained console encoding forces replacement, verify trace includes `live_output_sanitized`; if live turn fails pre-persist, verify `live_turn_failed` is present as bounded failure accounting.


## REBUILD-031 live stdin parity smoke
- `@'
szia syntaris én Árpi vagyok
'@ | python -m syntaris.cli --config "$CFG" talk --live`
- `python -m syntaris.cli --config "$CFG" trace-last`
- `@'
szia syntaris
szia syntaris én Árpi vagyok
mit tudsz rólam biztosan?
'@ | python -m syntaris.cli --config "$CFG" talk --live`
- Validate no mojibake in persisted prompt/trace and verify `live_input_repaired` appears when ingress decoding required repair.
