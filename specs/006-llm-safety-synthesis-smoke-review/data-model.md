# LLM Safety Synthesis Smoke Review Data Model

**Status: Backfilled / As-built**

## Entities

- Semantic summary asset: optional LLM summary created after exact `api_cost_ack`.
- LLM profile: provider, model, base URL, and API key environment variable name.
- Local env result: loaded env var names without secret values.
- Stock lens synthesis: narrative output from `phase-6f-stock-lens-json-only` by default, or `phase-6f-stock-lens-json-plus-reviewed-semantic-summary` when reviewed semantic context is explicitly enabled.
- Raw debug output: opt-in LLM response saved outside formal artifacts.
- Smoke review report: deterministic review JSON and Markdown.

## Boundaries

- `.env` values are never printed or committed.
- `not_fetched`, `not_requested`, and `data_date=null` remain external status.
- Review reports are eval/review only and do not call an LLM.
- Phase 6V.1 review reports enforce boundary/context consistency without rewriting historical reports.
