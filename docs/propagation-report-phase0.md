# Propagation report — Phase-0 foundation

## Direct changes

- Created package and module boundaries for contracts/config/bootstrap/core/orchestration/trace/cli.
- Added configuration templates for external LLM bin/model path support.
- Added baseline doctor and trace commands.
- Added bootstrap `.env` autoload so CLI commands consume repository-local runtime env without manual shell exports.

## Propagated layers

- Contracts: runtime dataclasses created first to anchor interfaces.
- Config: TOML + env override loader wired to contract models.
- Bootstrap: runtime context assembler now auto-loads `.env` before config resolution.
- Orchestration: doctor flow delegates checks to core utilities.
- Trace: explicit bootstrap event projection added.
- CLI: command surface added for doctor + trace-boot.
- Docs: architecture/bootstrap/operations docs synced to code and precedence policy made explicit.
- Tests: config override, doctor behavior, and `.env` autoload precedence covered.
- Versioning: initial `CHANGELOG.md` entry added.

## Deferred intentionally

- Persistence schema and migrations are deferred to future phases (no data store in Phase-0 scope).
- Adapter integrations are deferred until real providers are introduced.

## Structural self-check

- No single file contains full business logic.
- Runtime state contracts are explicit in `contracts/runtime.py`.
- CLI/orchestration/docs/tests/config are synchronized for the current feature surface.
