# Contract: Live Smoke Evidence

## Protected surfaces

- Podcast persistent data tree.
- Hermes config file.
- Managed podcast Skills tree.

The historical v1 evidence used SHA-256 metadata manifests only and therefore proved metadata stability, not content equality. The authorized `hermes-direct-smoke-v2` path additionally computes domain-separated SHA-256 content tokens in memory for all three surfaces. Protected bytes remain opaque: they are never decoded, parsed, emitted, or persisted; evidence contains only per-surface `metadata_unchanged` and `content_unchanged` booleans. Content traversal is POSIX descriptor-only with `O_NOFOLLOW`; native Windows and any platform missing the required descriptor primitives fail before protected path access. `.env`/`.env.*`, symlink/reparse, missing, malformed, and special entries fail closed. Both required reviewers and exactly one live v2 run passed; FR-010/C6 is PASS-current and the validator must not be rerun under this closure.

## Direct MCP evidence

- Streamable HTTP initialize succeeds.
- Ordered tools/list matches the frozen 21-tool registry.
- Exactly one read-only call succeeds.
- Exactly one `confirm=false` preview succeeds.

## Hermes natural-language evidence

One fresh-session bounded request must produce safe filtered evidence of:

- exactly one `podcast-ingest-core:*` tool call;
- no `confirm=true`;
- no second MCP action;
- no shell/terminal fallback.

If Hermes cannot expose this without reading sensitive session dumps, the claim is blocked and the feature cannot be marked Implemented.

Persisted evidence contains only versions, tool names/count/order digest, exit status, fixed call counts, and boolean safety/equality results. Protected-surface metadata/content digests, paths, tokens, raw responses, prompts, config values, endpoints, and session data are prohibited.

## 2026-08-09 outcome

- Historical `hermes-direct-smoke-v1` readiness evidence passed: exact 21 tools, one read-only call, one `confirm=false` preview, `dry_run=true`, `requires_confirmation=true`, and all protected-surface metadata manifests unchanged. It is not promoted to C6 proof.
- The tested `hermes-direct-smoke-v2` implementation requires protocol plus application `ok=true`, exact boolean safety flags, deterministic framed content tokens, and metadata/content conjunction while emitting equality booleans only. After both reviewers passed, the one authorized live invocation exited 0 with exact 21 tools, one read-only call, one `confirm=false` preview, all safety booleans true, and all three endpoint equality pairs true. C6 is `PASS-current`; invocation count is 1 and no rerun is allowed.
- Hermes v0.19.0 safe CLI output exposed repeated presentation markers rather than a structured tool-call record and did not expose actual `confirm` arguments. Official v0.20.0 tag `v2026.8.3` hooks document per-call events with tool names and arguments, but provide no canonical fallback indicator and may expose sensitive raw arguments/results. Without an approved projection collector and runtime validation, the four natural-language facts remain unproved.
- C7 is `BLOCKED/FAIL`; candidate capability is promising but insufficient and runtime validation is `not_evaluated`. No session dump, raw prompt/response, config value, endpoint, or credential was read or persisted, and the inference was not repeated.
