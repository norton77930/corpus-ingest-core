# Data Model: Historical Episode Verified Report Path

## HistoricalVerifiedReportNextStep

| Field | Type | Notes |
| --- | --- | --- |
| `podcast_id` | str | Exact |
| `episode_ref` | str | Exact; never latest/next |
| `suggestion` | str | `report_present` \| `publish_verified_report` \| `completion_action` \| `blocked` |
| `has_bundle` | bool | Eligible bundle exists |
| `source_digests` | list[str] | Bounded ≤10 |
| `publish_ready` | bool | 019 preview ready |
| `missing_roles` | list[str] | From 019 when blocked |
| `stale_roles` | list[str] | From 019 when blocked |
| `completion_action` | str \| null | 016 selected action when applicable |
| `recommended_mcp_tool` | str \| null | Tool name for next human-gated confirm |
| `requires_api_cost_ack` | bool | True only if completion_action is semantic_summary |
| `not_investment_advice` | bool | Always true |
