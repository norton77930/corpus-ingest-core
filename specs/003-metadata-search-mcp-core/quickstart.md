# Metadata Search MCP Core Quickstart

**Status: Backfilled / As-built**

## Manual Validation

```powershell
python scripts/extract_mentions.py --podcast gooaye --episode EP672
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/search_transcripts.py --podcast gooaye --query 台積電
python scripts/search_mentions.py --podcast gooaye --query 台積電
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
python scripts/run_mcp_server.py
```

## Expected Boundaries

- Side-effect MCP tools are dry-run first.
- Search returns local evidence and not investment advice.
- Cache rebuild is manual cache rebuild.
- no live market API is used.
