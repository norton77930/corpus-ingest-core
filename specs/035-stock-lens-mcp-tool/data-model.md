# Data Model: Stock Lens MCP Tool

## Input

Tool 22 accepts only bounded scalars: `podcast_id`, `stock_query`, `confirm`,
`force`, `allow_partial`, `max_evidence_items`. It accepts no local path, no
provider or credential selector, no network target, and no batch list.
`max_evidence_items` is clamped to `1..50` before Core is called.

## Dry-run Envelope

`confirm=false` returns the standard action plan: `tool`, `action`, `inputs`,
`writes` (`data/stock-lens/{podcast_id}/...`), and `risks`. It reads no report
body and performs no write. The risk list states that the run reads only local
artifacts and makes no live market API, network, or LLM call, and it repeats the
no-advice boundary.

## Confirmed Result

The confirmed call returns the existing `StockLensReportAsset` projection:
`podcast_id`, `stock_query`, `report_json_path`, `report_markdown_path`,
`report_status`, `match_count`, `warning_count`, `generated`, `already_exists`.
Warnings carry the stale-cache hint and the no-advice statement.

## Report Content Boundaries

The report separates direct podcast evidence (`evidence_status=podcast_explicit`,
timestamped) from inferred industry-chain leads (`evidence_status=
inferred_from_industry`, `verification_status=needs_verification`). External
status stays `not_requested`/`not_fetched` until a separate verification step
runs. Reuse is byte-stable: an existing report is returned with
`generated=false, already_exists=true` unless `force=true`.

## Registry

Tool 22 appends after unchanged Tools 1-21. Both the AST-derived projection in
`hermes_skill_protocol` and the Spec 029 descriptor snapshot resolve to 22
names; the snapshot is produced only by
`scripts/export_spec029_tool_descriptor_snapshot.py`.
