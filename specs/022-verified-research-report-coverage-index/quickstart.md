# Quickstart: Verified Research Report Coverage Index

## Core

```python
from podcast_ingest_core import list_verified_research_report_coverage

page = list_verified_research_report_coverage("gooaye", has_bundle=False, limit=50)
for row in page.items:
    print(row.episode_ref, row.has_bundle, row.source_digests)
```

## CLI

```powershell
python scripts/query_verified_research_report_coverage.py gooaye
python scripts/query_verified_research_report_coverage.py gooaye --has-bundle false --limit 20
```

## MCP

Tool 19 `query_verified_research_report_coverage` with `podcast_id`, optional `has_bundle`, optional `limit`.

## Notes

- Offline read-only; does not write corpus index or reports.
- Does not revalidate sources (use Tool 18 / 021 for exact locator currentness).
- Not investment advice.
