# Operations baseline

## Doctor command

`syntaris doctor` validates:

- external LLM server binary path is present and exists,
- external model path is present and exists,
- configured LLM port is valid.

Configuration values used by `doctor` follow bootstrap precedence (shell env > `.env` > TOML), and `.env` is auto-loaded from the working directory at CLI startup.

Exit code is `0` when healthy, `1` when any check fails.

## Trace boot command

`syntaris trace-boot` emits a minimal JSON event for bootstrap observability.
