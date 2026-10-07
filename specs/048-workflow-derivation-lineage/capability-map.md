# Capability inventory and proposed next phase

Inspected2026-10-04. Current runtime registry:28 tools. Local uncommitted work includes044-048; this is not a deployment claim. Fresh048 full regression:2085 passed,26 native-symlink skips; all Git policy guards execute.

| Implemented capability | Scope and repository evidence |
| --- | --- |
| Ingestion and transcription | RSS podcasts, X/YouTube video and local audio/transcripts; specs002,036,039-041 |
| Summaries | Deterministic extraction and explicitly opted-in semantic finance/learning-notes profiles; specs006,015,037 |
| Search and corpus operations | SQLite metadata/transcript/mention search, artifact inventory, remediation and bounded stage/latest workflows; specs003,008-017 |
| Research reports | Research/stock lens, named/latest verified reports, catalog, revalidation, coverage and historical backlog; specs004-005,018-024,035 |
| Study guide | Tool26 creates/reuses00/03/04/07, supports cover-only, protects existing05/06; specs038,044 |
| Workflow derivation | Tool25 creates/reuses05/06 from lecture03/04/07 and configured tools; specs042-043 |
| Agent operation | Two separate preview/approval/confirm/stop learning Skills; spec045 |
| Publication safety | Byte preservation, unsafe/recovery refusal, bounded reads and finite errors; specs044,046 |
| Learning next step | Tool27 suggests one next action for one explicit episode without executing it; spec047 |
| Derivation lineage | Tool28 compares recorded derivation inputs/outputs; Tool25 declares separate metadata_writes for its generation receipt; spec048 |

Local stdio and loopback HTTP share the MCP registry. Costs require explicit acknowledgement; cache rebuild remains manual. No investment advice or live market API.

## Delivered phase and later candidates

SPEC048 delivers derivation lineage: record future generation inputs/outputs, inspect six explicit states, and disclose the additional metadata side effect. Its user-authorized implementation appends Tool28. It does not change Tool27's presence/reuse semantics. Legacy outputs are untracked, not automatically migrated.

Suggested later order, not approved or numbered: lecture-to-summary/transcript lineage; read-only recovery diagnostics; learning catalog/search; then consider UI and separately authorized multi-stage/batch scheduling. Vector search and live market APIs remain outside current scope.
