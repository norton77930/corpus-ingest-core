# Research Workflow Orchestration Quickstart

**Status: Backfilled / As-built**

## Dry-run

```powershell
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --stock 台積電 --include-external-data-verification --include-stock-lens-synthesis
```

## Confirmed deterministic flow

```powershell
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --include-external-data-verification --force
```

## Confirmed optional LLM flow

```powershell
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --include-stock-lens-synthesis --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

Expected boundaries: dry-run writes nothing, optional LLM requires exact
`api_cost_ack`, no live market API, no investment advice, and manual cache rebuild.
