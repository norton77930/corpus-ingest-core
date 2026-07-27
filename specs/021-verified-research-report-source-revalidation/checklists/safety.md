# Safety Checklist: SPEC 021 Source Revalidation

**Purpose**: Review containment and data boundaries before implementation.
**Feature**: [spec.md](../spec.md)

- [x] Exact locator validation precedes every filesystem operation; no latest or implicit selection exists.
- [x] Bundle/currentness separation is fail-closed: invalid/missing bundle makes external checks `not_evaluated`.
- [x] Hostile paths never dereferenced; canonical safe paths are validated before read and hostile strings are comparison-only.
- [x] Public results contain no raw manifest, report/transcript/source bodies, paths, absolute paths, URI, stock query, secret-like data, or traceback details.
- [x] Status/check vocabulary and failed roles are closed and bounded.
- [x] Workflow is read-only/offline/zero-write, with no publish, staging, claim, cache rebuild, DB/FTS/vector/cache, or dependency.
- [x] RSS/HTTP/LLM/.env/download/transcription/remediation, provider, live market API, and investment advice are excluded.
- [x] Tool 18 is append-only and Tools 1–17 unchanged.

Checklist completion is a specification safety review, not a claim of runtime behavior.
