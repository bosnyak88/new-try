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
