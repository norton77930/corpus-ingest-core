# Contract: Verified Research Report Source Revalidation

## Core

```python
def revalidate_verified_research_report_sources(
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> VerifiedResearchReportSourceRevalidation: ...
```

Inputs are the exact `(podcast_id, episode_ref, lowercase-64-hex source_digest)` locator. The seam is read-only/offline/zero-write and does not accept latest, next, path, output, glob, prefix, batch, provider, or network input.

It checks exact bundle self-consistency, supported assembly options, current lineage, published/current lineage equality, exact source role/hash/size/canonical-path metadata equality, and shared digest equality. Missing/invalid bundle makes downstream checks `not_evaluated`. Hostile paths never dereferenced; published values are comparison-only and public output has no raw manifest, body, stock query, source paths, or absolute paths.

## CLI

`scripts/revalidate_verified_research_report_sources.py PODCAST_ID EPISODE_REF SOURCE_DIGEST` parses three bounded positional inputs, calls Core exactly once, and prints a sanitized generic JSON envelope. It has no writes or output/export option.

## MCP

Tool 18 is `revalidate_verified_research_report_sources(podcast_id, episode_ref, source_digest)`. It is append-only; Tools 1–17 unchanged in name, order, signature, action matrix, and envelope. The adapter validates bounded input, delegates once, and returns safe category-only output.
