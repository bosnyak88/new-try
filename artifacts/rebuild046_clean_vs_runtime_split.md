# REBUILD-046 clean vs runtime split

## Isolation setup
- Clean suite env: SYNTARIS runtime override variables are unset.
- Runtime smoke env: temp DB/sandbox set via SYNTARIS_DB_PATH and SYNTARIS_ARTIFACT_ALLOWED_ROOTS.
- Compat aliases intentionally poisoned: SYNTARIS_DB / SYNTARIS_SANDBOX_ROOTS point to wrong paths.

## Results
- Clean suite initial exit: 0
- Targeted/compile failures: 0
- Runtime smoke failures: 0
- Clean suite post-runtime exit: 0

## Conclusion
- Canonical full suite runs in a dedicated clean environment.
- Runtime smoke runs in a separate temporary runtime environment.
- Post-runtime clean suite check confirms no harness contamination leaked back.