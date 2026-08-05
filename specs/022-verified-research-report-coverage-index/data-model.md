# Data Model: Verified Research Report Coverage Index

## VerifiedResearchReportCoverageRow

| Field | Type | Notes |
| --- | --- | --- |
| `podcast_id` | str | Exact podcast |
| `episode_ref` | str | Canonical local ref; never `latest`/`next` |
| `inventory_present` | bool | In local inventory discovery |
| `has_bundle` | bool | `bundle_count > 0` |
| `bundle_count` | int | Eligible canonical summaries for this episode |
| `source_digests` | list[str] | Sorted lowercase 64-hex; max 10 entries |

## VerifiedResearchReportCoveragePage

| Field | Type | Notes |
| --- | --- | --- |
| `podcast_id` | str | |
| `items` | list[CoverageRow] | After filter + limit |
| `limit` | int | Requested bound |
| `returned_count` | int | `len(items)` |
| `inventory_episode_count` | int | Full inventory size |
| `bundle_episode_count` | int | Unique episodes with ≥1 eligible bundle |
| `with_bundle_count` | int | Inventory episodes with ≥1 bundle |
| `without_bundle_count` | int | Inventory episodes with 0 bundles |
| `orphan_bundle_episode_count` | int | Bundle-only episodes |
| `coverage_status` | str | `complete` \| `incomplete_entry_cap` \| `incomplete_directory_read` |
| `catalog_root_status` | str | `ok` \| `missing` \| `invalid` (aligned with 020) |
| `not_investment_advice` | bool | Always `true` |

## Constants

- Default limit `50`, max `100`
- Max digests listed per row `10`
- Entry cap per directory level `1000` (via 020 discovery)

## Non-fields

No absolute paths, raw manifests, report bodies, lineage status, or `source_currentness_status` (not evaluated here).
