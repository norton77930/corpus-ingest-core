# Quickstart Validation: Verified Research Report Catalog

## Preconditions

- A temporary local `data/research-reports` fixture root is available; no production data, network, `.env`, provider, or cache is required.
- Use a known valid 018/019-shaped bundle and malformed variants. Tests are preferred over manual operation.

## Scenarios

1. **Missing root**: list and search return `items=[]`, `catalog_root_status="missing"`, and make zero writes.
2. **List filters/order/limit**: construct multiple canonical bundles; apply exact podcast/episode filters; assert ascending `(podcast_id, episode_ref, report_version)` order and `1..100` limit.
3. **Safe search**: monkeypatch report/transcript body reads to fail; search a safe projection term and assert a match without those reads. Blank query rejects.
4. **Traversal containment**: add symlink/junction, out-of-root target, extra nesting, noncanonical `v2-*`, and >1,000 entries; assert skip/fail-closed bounded results, never link following.
5. **Inspect valid**: inspect exact locator; assert exactly `report.json`, `report.md`, and `manifest.json` are verified and `source_currentness_status=not_evaluated`.
6. **Inspect tampering**: alter identity, schema, file hash/size, version/digest, or file set; assert `invalid`, category-only checks, no raw manifest, and no absolute paths.
7. **Surfaces**: CLI `list/search/inspect` serialize Core results; MCP registry contains unchanged Tools 1–16 plus Tool 17 `query_verified_research_report_catalog`.

## Commands (after implementation)

```powershell
python -m pytest tests/test_verified_research_report_catalog.py tests/test_verified_research_report_catalog_cli.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest tests/test_spec_020_verified_research_report_catalog_docs.py -q
python -m pytest
python -m compileall src scripts
git diff --check
```

Implemented CLI examples:

```powershell
python scripts/query_verified_research_report_catalog.py list --podcast-id gooaye --limit 50
python scripts/query_verified_research_report_catalog.py search "EP650" --podcast-id gooaye --limit 50
python scripts/query_verified_research_report_catalog.py inspect gooaye EP650 <source_digest>
```

No command accepts an output path, export option, latest selector, force/retry, network setting, or provider setting.
