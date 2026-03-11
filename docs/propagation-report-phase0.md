## REBUILD-007 propagation

- Contracts extended with first-class pending-route proposal/status/resolution types.
- Orchestration now runs a shared pre-turn route/pending resolver across once/live/script paths.
- Persistence now stores pending-route state explicitly in `app_meta.pending_route`.
- CLI `session-status` and scripted live output expose pending metadata.
- Trace payloads include pending proposal/resolution metadata.

# Propagation report — REBUILD-006 deterministic topic-shift + previous-thread foundation

## Direct changes

- Extended active conversation contracts/state with explicit `previous_thread_id` / `previous_thread_key`.
- Extended route contracts with `SWITCH_PREVIOUS` and before/after transition metadata.
- Expanded deterministic Hungarian-first routing with previous-thread return phrases and topic-shift aliases.
- Kept one shared route/state resolution path in turn orchestration used by once/live/script execution for normal talk turns.
- Extended session/thread inspection CLI outputs for current + previous thread visibility.
- Extended trace payloads with route decision transition fields (before/after + previous-thread context).

## Supported deterministic phrases

- Return/switch existing thread: `vissza a <thread_key> szálra`, `menjünk vissza a <thread_key> szálra`, `váltsunk a <thread_key> szálra`
- Return to previous thread: `vissza az előző szálra`, `folytassuk az előzőt`, `térjünk vissza az előző témára`
- Create/switch thread: `új szál: <thread_key>`, `legyen új szál: <thread_key>`, `nyiss új szálat: <thread_key>`
- Topic-shift aliases: `más téma: <thread_key>`, `új téma: <thread_key>`, `egy másik dolog: <thread_key>`

## Precedence

1. explicit CLI overrides (`--thread`, `--mode`)
2. explicit live slash commands
3. deterministic named thread-routing phrases
4. deterministic previous-thread/topic-shift phrases
5. continue active thread

## Structural self-check

- No monolithic central pipeline was introduced.
- Routing, turn execution, live controls, persistence, trace, and CLI boundary remain separated.
- No fuzzy semantic routing, embeddings, or LLM intent routing was added.

## Deferred intentionally

- semantic/LLM routing
- embeddings or fuzzy intent classification
- broad thread history stack beyond current+previous
- summarization or memory graph
