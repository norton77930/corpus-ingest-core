# Research decisions
- Decision: compose existing public Core queries, not MCP wrappers. Rationale: thickCore boundary, single-query client UX, unchanged scopes. Alternative raw envelope nesting rejected for private-data/contract drift risk.
- Decision: recovery-first gate. Rationale: other queries already refuse remnants; gate avoids redundant reads and ambiguous readiness. Detail remains Tool30; compact summary exposes only status/reason/manual flag.
- Decision: no suggested_call/execution authorization. Rationale: overview is diagnosis; Tool27 keeps its separate preview guidance and Skills keep their approval protocol.
- Decision: legacy/custom/stale distinct attention reasons; not_generated is ordinary pending. Rationale: metadata absence is not a proven current chain. No transcript-vs-summary freshness claim.
- Decision: per-child exception and malformed-response normalization; validate identity/flags/finite fields before projection. Rationale: fail closed without paths/bodies/arbitrary error text; no private imports.
- Decision: keep independent sequential observations and warn non_atomic. Alternative snapshot/refactor deferred because it would materially alter existing query contracts.
- All choices grounded in existing047-050 source/contracts; no external API/docs needed.
