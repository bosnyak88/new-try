# REBUILD-035 Capability Catalog

## Supported source kinds (baseline)
- `raw_paste`
- `once_file_import`
- `local_text_file`

## Supported read-only local file operations
- `artifact-find <pattern>`
- `artifact-read <path>`
- `artifact-list [--current]`
- `artifact-show (--last | --id <artifact_id>)`
- `audit-last`

## Supported file types for `artifact-read`
`.txt`, `.md`, `.log`, `.json`, `.toml`, `.yaml`, `.yml`, `.ini`, `.csv`, and common code/config text files (`.py`, `.ts`, `.js`, `.go`, `.java`, `.rs`, `.c`, `.cpp`, `.h`, `.hpp`, `.env`, `.conf`).

## Intentional non-goals in this ticket
- No write/delete/move/rename file operations.
- No PDF/Office parsing.
- No binary adapters.
- No external app automation.
- No shell/panel UX broadening.

## Safety model
- Reads are restricted to configured `artifact_allowed_roots`.
- Outside-root and unsupported/binary reads are explicitly refused.
- Refused reads are journaled in `source_audit_journal` and do not become active source context.


## Environment overrides accepted by runtime
- DB path: `SYNTARIS_DB_PATH` (primary, always honored).
- Allowed roots: `SYNTARIS_ARTIFACT_ALLOWED_ROOTS` (primary, always honored).
- Compat aliases `SYNTARIS_DB` / `SYNTARIS_SANDBOX_ROOTS` are only honored with default/example config path (`config/syntaris.example.toml`) to prevent ambient env leakage over explicit temp test configs.
