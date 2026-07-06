# Metadata Search MCP Core Data Model

**Status: Backfilled / As-built**

## Entities

- Mention artifact: deterministic company, ticker, industry, macro topic,
  crypto, person, location, or related evidence extracted from transcript text.
- Cache record: derived SQLite metadata row for episodes, transcripts, mentions,
  summaries, and research artifacts.
- Search result: query match with source type, episode reference, snippet, and
  optional context segments.
- MCP response envelope: success, dry-run, or error object returned over stdio.
- Eval report: manually captured audit record for MCP tool-use behavior.

## Boundaries

- Cache records are derived from local artifacts.
- Search results help locate podcast evidence but do not create market facts.
- MCP side-effect tools must not rebuild cache automatically.
