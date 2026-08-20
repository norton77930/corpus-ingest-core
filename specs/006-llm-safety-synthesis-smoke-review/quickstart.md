# LLM Safety Synthesis Smoke Review Quickstart

**Status: Backfilled / As-built**

## Dry-run smoke

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500
```

## Confirmed synthesis smoke

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500 --confirm --force --debug-llm-output --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

## Review gate

```powershell
python scripts/review_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電
```

## Phase 6U Semantic Summary Smoke Validation

```powershell
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile pro4500
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile pro4500 --confirm --force --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
python scripts/review_semantic_summary_smoke.py --podcast gooaye --episode EP672
```

This path validates transcript transfer risk directly. It requires exact `api_cost_ack`, keeps no raw transcript stdout, makes no MCP tool changes, uses no live market API, and provides no investment advice.

Phase 6U.1 adds stderr progress during confirmed runs and narrows the semantic review guard false positive behavior for transcript-derived buy/hold descriptions. Direct trade advice, target price, and guaranteed return language remain failures.

Expected boundaries: dry-run writes nothing, confirmed LLM paths require exact
`api_cost_ack`, stock lens synthesis defaults to `phase-6f-stock-lens-json-only`,
Phase 6V opt-in synthesis may use
`phase-6f-stock-lens-json-plus-reviewed-semantic-summary`, no live market API,
no investment advice, and manual cache rebuild.

## Phase 6V Reviewed Semantic Context

Default stock lens synthesis remains `phase-6f-stock-lens-json-only`. After a semantic summary has passed review, opt in to reviewed semantic context:

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500 --confirm --force --include-semantic-context --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

The enabled boundary is `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`. The context excludes `## Chunk Summaries`, uses no raw transcript, no live market API, no MCP tool changes, and no investment advice.

## Phase 6V.1 Review Gate Boundary Alignment

The deterministic review gate enforces boundary/context consistency. A JSON-only artifact must not include `source_semantic_context`. A reviewed semantic artifact must include non-empty `source_semantic_context`, and every entry must have `review_status=passed` plus content. This review step does not call an LLM, read `.env`, fetch live market data, change MCP tools, or rewrite historical review reports.
