# Implementation Plan: Verified Research Report Catalog

**Branch**: `020-verified-research-report-catalog` | **Date**: 2026-07-26 | **Spec**: [spec.md](spec.md)

## Summary

Implemented one Core-owned, read-only/offline catalog over canonical local verified report bundles: deterministic bounded list, safe manifest-derived metadata search, and exact-locator bundle self-consistency inspect, with thin CLI subcommands and appended MCP Tool 17.

## Technical Context

- **Language**: Python 3.12; existing project stack only; no new dependency.
- **Storage**: Existing `data/research-reports` as untrusted read-only local input; no DB/FTS/vector/cache.
- **Core seams**: `list_verified_research_reports`, `search_verified_research_reports`, `inspect_verified_research_report`.
- **Interfaces**: `scripts/query_verified_research_report_catalog.py` with `list`, `search`, `inspect`; appended MCP Tool 17 `query_verified_research_report_catalog`.
- **Testing**: pytest filesystem fixtures, monkeypatched body-read guards, deterministic sort/limit tests, path-safety tests, CLI/MCP contract tests; no network.
- **Constraints**: bounded level-by-level traversal; canonical `v1-[a-f0-9]{64}` only; reject symlink/junction/out-of-root; no raw manifest/absolute paths; inspect currentness is not evaluated.

## Constitution Check

| Principle | How 020 complies |
| --- | --- |
| Local artifacts / traceability | Reads canonical local bundle metadata and gives an explicit self-consistency scope |
| Thin interfaces | Core owns traversal and validation; CLI/MCP only parse, call, and serialize |
| Dry-run first side effects | No side effects exist; all operations are read-only/offline |
| LLM opt-in / secrets | No LLM, provider, `.env`, report body, or secret-like output |
| Evidence separation | Does not reinterpret report evidence; currentness is explicitly `not_evaluated` |
| No investment advice | Metadata only; preserve notice without advice generation |
| Manual cache rebuild | No cache exists or is rebuilt |
| TDD / verification | Focused RED tests precede each vertical slice; docs contract test protects this package |

**Gate**: PASS — no constitution amendment required.

## Project Structure

```text
specs/020-verified-research-report-catalog/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── contracts/verified-research-report-catalog.md
└── checklists/{requirements,safety}.md

src/corpus_ingest_core/
├── verified_research_report_catalog.py       # NEW Core ownership
├── models.py / errors.py / __init__.py        # exports/result models as needed
└── mcp_server.py                              # append Tool 17 only

scripts/query_verified_research_report_catalog.py  # NEW thin CLI
tests/test_verified_research_report_catalog.py
tests/test_verified_research_report_catalog_cli.py
tests/test_mcp_tool_registry_contract.py
```

## Design Decisions

1. Use a new Core module, not 018/019 workflow runners: catalog never publishes or performs readiness/remediation.
2. Treat every directory entry as hostile until non-reparse, contained, canonical, and regular-file checks pass.
3. Separate eligibility (safe parseable manifest projection) from inspect integrity; list/search never open report files.
4. Inspect validates only local bundle self-consistency, never source currentness or lineage validity.
5. Preserve append-only MCP registry: Tool 17 follows all existing 1–16 tools.

## Verification

```powershell
python -m pytest tests/test_spec_020_verified_research_report_catalog_docs.py -q
python -m pytest tests/test_verified_research_report_catalog.py tests/test_verified_research_report_catalog_cli.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest
python -m compileall src scripts
git diff --check
```

Completion evidence is recorded in `tasks.md`: the full suite passed with 1084 tests, 3 platform-capability skips, successful `compileall`, and clean `git diff --check`.
