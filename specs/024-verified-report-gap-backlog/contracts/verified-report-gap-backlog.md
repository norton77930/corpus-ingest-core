# Contract: Verified Report Gap Backlog

## Core

```text
list_verified_report_gap_backlog(
    podcast_id: str,
    *,
    limit: int = 50,
) -> VerifiedReportGapBacklogPage
```

- Zero-write; delegates coverage with `has_bundle=False`.

## CLI

```text
python scripts/list_verified_report_gap_backlog.py PODCAST_ID [--limit N]
```

## MCP Tool 21

- Name: `list_verified_report_gap_backlog`
- Inputs: `podcast_id`, `limit=50`
- Read-query; append after Tools 1–20
