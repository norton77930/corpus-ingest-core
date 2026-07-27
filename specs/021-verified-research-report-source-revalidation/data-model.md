# Data Model: Verified Research Report Source Revalidation

## Locator

`locator: dict[str, str]` contains only exact safe `podcast_id`, `episode_ref`, and lowercase-64-hex `source_digest`. It contains no filesystem path.

## Public result

```python
@dataclass(frozen=True)
class VerifiedResearchReportSourceRevalidation:
    locator: dict[str, str]
    bundle_self_consistency_status: str
    lineage_revalidation_status: str
    source_currentness_status: str
    checks: dict[str, str]
    failed_roles: list[str]
    safe_metadata: VerifiedResearchReportCatalogItem | None
    not_investment_advice: bool | None
```

`bundle_self_consistency_status` is `valid|invalid|not_found`. `lineage_revalidation_status` is `current|missing|stale_or_invalid|mismatch|not_evaluated`. `source_currentness_status` is `current|stale_or_invalid|not_evaluated`.

## Fixed checks and disclosure boundary

`checks` has exactly: `bundle_self_consistency`, `assembly_options`, `current_lineage`, `published_lineage_match`, `source_artifact_metadata_match`, and `source_digest_match`. `failed_roles` uses only the closed role set, never exception text, hostile path, manifest value, or stock query.

Public values contain no raw manifest, report/transcript/source body, source path, absolute paths, URI, or secret-like value. The result is not investment advice.

## Evaluation rule

`source_currentness_status=current` requires all gates. Bundle failure forces downstream lineage/currentness checks to `not_evaluated`; this preserves bundle/currentness separation. Hostile paths never dereferenced.
