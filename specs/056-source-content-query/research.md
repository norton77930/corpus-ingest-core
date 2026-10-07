# Research decisions

- Existing mcp_tools_read/search require a cache and have no episode-scoped body paging. New reader is independent of SQLite.
- canonical_transcript.py validates title-derived names but reads candidates through a snapshot helper without a hardlink-count guard. New reader enforces that guard before candidate bytes; ambiguity fails rather than allowing a new seed/manifest authority.
- validator.py is offline but uses unbounded ordinary reads and permissive coercion. New strict snapshot normalization must not alter its legacy behavior.
- secure_local_snapshot.py already protects roots, ancestors, reparse points and opened-handle containment. Opt-in unique-link/content-stability checks preserve existing callers and avoid duplicating platform-specific handle logic.
- source_preparation metadata records actual transcription; preparation_transcription.actual reads evidence. Legacy omissions must stay unknown, not derived from current profile settings.
- JSON SHA256 provides version pinning without SQLite state; cursor binds scope and exact version. Host tracking of consecutive pages supplies full-note coverage without storing session state in the repo.
- Constitution IV provider acknowledgement remains intact; existing read MCP responses already expose transcript evidence to host clients. The new Skill makes host model data exposure and billing explicit and does not label host generation free/offline.
- Medium X pilot already exists at .pytest-tmp/54m/data. Reuse read-only, preserve hashes, no preparation or model run. Synthetic dialogue tests and SDK transport are not real Hermes acceptance.

Read-only repository research supplied by research_056_contract; no network used, files changed or tests run by researcher. All implementation remains with the root writer.
