# Contract: Verified Research Report Catalog

## Core

```python
def list_verified_research_reports(
    *,
    podcast_id: str | None = None,
    episode_ref: str | None = None,
    limit: int = 50,
) -> VerifiedResearchReportCatalogPage: ...


def search_verified_research_reports(
    query: str,
    *,
    podcast_id: str | None = None,
    episode_ref: str | None = None,
    limit: int = 50,
) -> VerifiedResearchReportCatalogPage: ...


def inspect_verified_research_report(
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> VerifiedResearchReportCatalogInspection: ...
```

All seams are read-only/offline. `podcast_id` and `episode_ref` filters are exact only. `limit` is integer `1..100`, default 50. Search requires a nonblank normalized query. There is no latest selector, output path, export, copy, zip, republish, force, retry, batch, cache, DB/FTS/vector, RSS/HTTP/LLM/.env/download/transcription/remediation behavior.

Traversal is bounded one level at a time under the canonical root and accepts versions only matching `v1-[a-f0-9]{64}`. Symlink, junction, nonregular, special, and resolved out-of-root entries are rejected/skipped before parse. A missing root is an empty successful page with zero writes.

List/search return only safe manifest-derived scalar metadata. They MUST NOT read report, transcript, or source-artifact bodies. Results omit raw manifest, paths (including absolute paths), unsafe URIs, secrets, and traceback bodies.

Inspect requires the exact locator. It validates directory and manifest identity, `schema_version == REPORT_SCHEMA_VERSION == "latest-episode-verified-research-report-v1"` from `src/podcast_ingest_core/verified_research_report.py`, exactly `report.json`, `report.md`, and `manifest.json`, and manifest-recorded SHA-256/size for report JSON and Markdown. `manifest.json` is capped at 1 MiB and each report snapshot at 16 MiB; a size-bound failure is invalid. A success means bundle self-consistency only and always includes `source_currentness_status=not_evaluated`; it does not revalidate sources or lineage.

## CLI

`scripts/query_verified_research_report_catalog.py` has subcommands:

- `list [--podcast-id ID] [--episode-ref REF] [--limit 1..100]`
- `search QUERY [--podcast-id ID] [--episode-ref REF] [--limit 1..100]`
- `inspect PODCAST_ID EPISODE_REF SOURCE_DIGEST`

The CLI parses bounded input, calls exactly one Core seam, and prints only JSON-safe sanitized Core output. It creates no files and has no output/export switch.

## MCP

- Tool name: `query_verified_research_report_catalog`
- Position: **Tool 17**, appended after reviewed Tools 1–16
- Operations: `list`, `search`, `inspect`, with the Core parameters above
- Envelope: existing MCP `ok` / `data` / error conventions
- Compatibility: Tool 17 changes neither Tool 1–16 order nor their public contracts

The MCP adapter performs only input-envelope validation and Core delegation. It does not reproduce traversal, read report bodies, expose a raw manifest, or accept a path/output/export/latest/network/provider parameter.

## Result shapes

`VerifiedResearchReportCatalogPage` has `items`, `limit`, `returned_count`, `catalog_root_status`, and `traversal_status`. Items use the safe metadata projection in [data-model.md](../data-model.md).

`VerifiedResearchReportCatalogInspection` has exact public locator, bounded `bundle_self_consistency_status`, named checks, safe metadata when validly derived, and mandatory `source_currentness_status=not_evaluated`. Neither shape contains raw manifest or absolute paths.
