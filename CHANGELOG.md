# Changelog

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
