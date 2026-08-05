# Contract: Verified Research Report Coverage

## Core

```text
list_verified_research_report_coverage(
    podcast_id: str,
    *,
    has_bundle: bool | None = None,
    limit: int = 50,
) -> VerifiedResearchReportCoveragePage
```

- Required exact `podcast_id`.
- Optional `has_bundle` filter; optional `limit` in `1..100`.
- Read-only/offline/zero-write.
- Serialization via `result_to_dict` → JSON-safe scalars/lists only.

## CLI

```text
python scripts/query_verified_research_report_coverage.py PODCAST_ID
    [--has-bundle true|false]
    [--limit N]
```

- Exactly one Core call.
- Stdout: JSON only; no absolute paths or bodies.

## MCP Tool 19

- Name: `query_verified_research_report_coverage`
- Inputs: `podcast_id: str`, `has_bundle: bool | None = None`, `limit: int = 50`
- Read-query (no `confirm`, no ack).
- Append after Tool 18; Tools 1–18 unchanged.
- Envelope: `{"ok": true, "data": ...}` / `{"ok": false, "error_type": ..., "message": ...}`.

## Boundaries

- No DB/FTS/vector/cache/RSS/HTTP/LLM/.env/download/transcription/remediation.
- No latest/next selectors.
- No raw manifest / absolute paths / investment advice.
