# Implementation Plan: Stock Lens MCP Tool

**Date**: 2026-08-15 | **Spec**: [spec.md](spec.md)

## Summary

Expose the existing deterministic stock lens over MCP as append-only Tool 22.
Exposure only: `stock_lens.generate_stock_lens_report` is untouched and the tool
is a thin dry-run-first wrapper. Completes Spec 001 User Story 3 for agents.

## Constitution Check

Local artifacts only; thin MCP over an existing Core seam; dry-run-first with a
`confirm` gate; no LLM, no `.env`, no secrets, no live market API; no automatic
cache rebuild; no investment advice; TDD. **No constitution amendment.**

## Design Decisions

1. **New group module, imported last** — registration order is import order, so
   `mcp_tools_stock_lens.py` after the existing four keeps Tools 1-21 in place.
   Appending to `mcp_tools_side_effect.py` would have inserted the tool at slot
   13 and renumbered everything after it.
2. **Side-effect, not read-query** — the report is written, so it follows the
   Tools 7-12 dry-run/confirm shape rather than the Tools 17-21 read shape.
3. **No `api_cost_ack`** — the seam reads local artifacts only; requiring the
   LLM acknowledgement would misrepresent the risk.
4. **Regenerate, never hand-edit, the Spec 029 descriptor snapshot** — the
   official export script is the only sanctioned writer.
5. **Synthesis report deferred** — different input contract; not v1.

## Registry Impact

`exact 21` is not a scattered literal but a chain: the AST projection in
`hermes_skill_protocol._registry_tool_names_from_source` returns `None` on a
size mismatch, which cascades into the Spec 029 interposer and its tests. The
chain must be updated at its source, not patched literal by literal. Two
digest-pinned surfaces move as a result and are recorded for re-baseline in
`docs/install-and-porting.md`.

## Project Structure

```text
specs/035-stock-lens-mcp-tool/
src/podcast_ingest_core/mcp_tools_stock_lens.py
src/podcast_ingest_core/mcp_server.py                     (facade wiring)
src/podcast_ingest_core/hermes_skill_protocol.py          (AST source list + size)
deploy/hermes/spec029/spec029_mcp_deny_adapter.py         (exact-22)
deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json  (regenerated)
scripts/validate_mcp_setup.py                             (registry check)
docs/mcp-usage.md, README.md, docs/agent-handoff.md,
docs/ai-development-framework.md, specs/README.md, docs/roadmap.md
tests/test_mcp_tool_registry_contract.py, tests/test_mcp_setup_validation.py,
tests/test_spec_029_offline.py, tests/test_hermes_skill_protocol.py,
tests/test_mcp_server_facade_boundary.py, tests/test_cache_rebuild_guard.py,
tests/test_ai_governance_docs.py,
tests/test_spec_020_verified_research_report_catalog_docs.py
```

## Verification

```powershell
python -m pytest tests/test_mcp_tool_registry_contract.py tests/test_mcp_setup_validation.py tests/test_docs_registry_count_consistency.py -q
python -m pytest -q --tb=no -ra
python -m compileall src scripts
```
