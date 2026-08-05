# Data Model: Verified Report Gap Backlog

## VerifiedReportGapBacklogRow

| Field | Type | Notes |
| --- | --- | --- |
| `podcast_id` | str | |
| `episode_ref` | str | Inventory gap |
| `inventory_present` | bool | Always true for pure gaps from coverage filter |

## VerifiedReportGapBacklogPage

| Field | Type | Notes |
| --- | --- | --- |
| `podcast_id` | str | |
| `items` | list[Row] | After limit |
| `limit` | int | |
| `returned_count` | int | |
| `gap_count` | int | Full-join `without_bundle_count` |
| `inventory_episode_count` | int | From coverage page |
| `coverage_status` | str | Passthrough |
| `catalog_root_status` | str | Passthrough |
| `not_investment_advice` | bool | true |
