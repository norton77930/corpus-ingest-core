# Spec Kit Governance Quickstart

**Status: Backfilled / As-built**

## Inspect governance artifacts

```powershell
Get-Content .specify\memory\constitution.md
Get-ChildItem .agents\skills
Get-Content AGENTS.md
Get-Content specs\README.md
```

## Validate governance docs

```powershell
python -m pytest tests/test_spec_kit_bootstrap.py
python -m pytest tests/test_spec_kit_constitution.py
python -m pytest tests/test_spec_kit_backfill_docs.py
python -m pytest tests/test_architecture_spec_docs.py
```

Expected boundaries: docs/spec/tests only, no `.env` read, no LLM call, no live
market API, no runtime behavior change, no MCP behavior change, and no
investment advice.
