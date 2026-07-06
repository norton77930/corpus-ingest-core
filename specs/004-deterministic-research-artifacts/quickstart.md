# Deterministic Research Artifacts Quickstart

**Status: Backfilled / As-built**

## Manual Validation

```powershell
python scripts/generate_episode_intelligence_report.py --podcast gooaye --episode EP672 --force
python scripts/generate_industry_chain_mapping.py --podcast gooaye --episode EP672 --force
python scripts/generate_external_data_boundary.py --podcast gooaye --episode EP672 --force
python scripts/verify_external_data_boundary.py --podcast gooaye --episode EP672 --confirm --force
python scripts/inspect_gooaye_lens.py
python scripts/generate_stock_lens_report.py --podcast gooaye --stock 台積電 --force
```

## Expected Boundaries

- No LLM call.
- no live market API.
- Fixture data preserves external status and does not become podcast evidence.
- Reports preserve evidence separation and no investment advice.
- Cache rebuild remains manual cache rebuild.
