# Safety Checklist: Hermes MCP Integration

- [x] No `.env`, credentials, tokens, private endpoints, provider values, or session dumps may be read or emitted.
- [x] No confirmed content-processing action is permitted in live validation.
- [x] HTTP is loopback-only under host networking, with transport security retained.
- [x] No legacy SSE, public port mapping, automatic port fallback, or second FastMCP instance.
- [x] Existing MCP entries and unknown config keys must survive merge.
- [x] Local Skill shadow collision fails closed.
- [x] Apply is backup-first and rollback is manifest-bound.
- [x] The v2 validator compares metadata and opaque in-memory content tokens but emits only equality booleans; protected digest/path/content never leaves memory, and `.env`/reparse/special entries fail closed. Both reviewers and the single live run passed; C6 is PASS-current and the run is not repeated.
- [x] Hermes trace insufficiency blocks completion instead of triggering session-dump inspection. v0.20.0 tag `v2026.8.3` hooks remain an uninstalled, unvalidated candidate and do not satisfy C7.
- [x] No investment advice, live market API, cache rebuild, commit, push, deployment publication, or secret propagation.
