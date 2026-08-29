# Implementation Plan: Latest Episode Verified Research Report Workflow

**Branch**: `018-latest-episode-verified-research-report-workflow` | **Date**: 2026-07-21 | **Spec**: [spec.md](spec.md)

## Summary

Add one Core-owned latest-episode workflow that previews strictly without writes, validates exact `expected_episode_ref` and exact `api_cost_ack` before protected work, pins latest once via 017, gates semantic and deterministic research work, and atomically publishes a deterministic verified research report. It has a metadata-only checkpoint, thin CLI, appended fifteenth MCP tool, and portable human-approval Skill.

## Technical Context

- **Language**: Python 3.12; standard library and existing FastMCP/project runners.
- **Storage**: Existing local artifacts plus checkpoint under `data/corpus/` and versioned report bundle under `data/research-reports/`; cache rebuild remains manual.
- **Testing**: pytest fixtures and monkeypatches only. No real confirmation, download, transcription, LLM/API call, or live external-market call.
- **Platform**: Local Windows PowerShell and stdio MCP clients.
- **Constraints**: strict zero-write preview; exact acknowledgement and canonical reference before RSS/environment/provider/writer; no live market API, retry, scheduler, batch, force, output override, or investment advice.

## Constitution Check

- Core implementation belongs in `src/corpus_ingest_core`; CLI and MCP are thin wrappers.
- `confirm=False` writes zero files; confirmation is explicit and episode-scoped with `expected_episode_ref` and exact `api_cost_ack`.
- Semantic transfer happens only through existing acknowledged functionality; no `.env` is read by preview or invalid confirmation.
- Research options are fixed safe values and optional verification is a local fixture only; no live market API.
- Atomic bundle publication and checkpoint metadata must not leak raw transcript, credentials, URI query/fragment data, traceback text, or investment advice; the workflow provides no investment advice.

## Project Structure

```text
specs/018-latest-episode-verified-research-report-workflow/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── design.md
├── quickstart.md
├── tasks.md
├── contracts/latest-episode-verified-research-report-workflow.md
└── checklists/{requirements,safety}.md

src/corpus_ingest_core/
├── latest_episode_verified_research_report_workflow_runner.py
├── verified_research_report.py
├── corpus_latest_episode_deterministic_workflow_runner.py
├── models.py
├── errors.py
├── storage.py
├── mcp_server.py
└── __init__.py

scripts/run_latest_episode_verified_research_report_workflow.py
.agents/skills/latest-episode-verified-research-report/SKILL.md
tests/test_latest_episode_verified_research_report_workflow_runner.py
tests/test_latest_episode_verified_research_report_skill.py
```

## Design Decisions

1. Validate `expected_episode_ref` and exact `api_cost_ack` at the top of confirmed Core and MCP wrapper before resolving RSS or accessing a protected dependency.
2. Preview resolves latest once for its plan and returns no checkpoint/path writer side effect. Confirmed mode resolves latest once, compares it to the expected reference, then calls 017 `_run_pinned_deterministic_workflow(..., write_report=False)`.
3. Inspect local artifacts through the neutral `semantic_review_artifact` domain shared by the 015 writer, corpus index, and 018. Generate only missing summary or safely re-review missing/stale/spoofed review; require canonical timestamp or timestamp-plus-collision filename, fixed mode/boundary, expected check matrix/counts, identity, and an additive `semantic_summary_sha256` bound to current summary bytes.
4. Invoke research with fixed safe options: no force, no partial work, no nested semantic summary or stock-lens synthesis; only explicit local fixture verification can be enabled.
5. Acquire every report input once as an immutable byte snapshot; parse, safety-scan, review-bind, render, and digest only those bytes. Assemble a source digest from schema/version, identity, normalized stock query, `include_fixture_verification`, verification scope, and source roles/hashes/sizes. Adoption first requires valid transcript TXT/SRT/JSON and identity. Checkpoint history retains validated digest/version/bundle references through intermediate merges; a common finalizer records every canonical confirmed terminal outcome except the explicit zero-write approval-boundary drift rejection. Successful checkpoint writes carry sortable invocation-start tokens, so the locked merge preserves a newer successful bundle while an old writer adds only history.
6. Stage byte-canonical bundle files on the final parent filesystem, validate the exact three-file staged set, reread all sources immediately before rename, then atomically rename the directory. Reuse and destination-race success also reread all sources before returning. Bundle and checkpoint claims are process-lifetime OS locks with persistent lockfiles (Windows byte-range lock, POSIX advisory lock); crash release comes from descriptor/process teardown, never unconditional stale-file deletion. A destination race is reused only after deterministic JSON/Markdown bytes and full expected manifest independently match; every other mismatch fails closed.
7. Put disclaimer normalization in low-level `report_safety`; semantic review and stock-lens synthesis depend downward on it, while the neutral review artifact cannot import a provider, LLM, or stock-lens implementation.
8. Append the MCP tool after 017, retain the prior fourteen order/contracts, and update setup validation to exact 15 tools plus Skill/early-guard checks.

## Verification

Run focused RED then GREEN tests for core/report publication, interface/Skill/MCP registry, setup validation, and docs package. Run 015/016/017/research regressions, safety guards, full pytest, `python -m compileall src scripts`, and `git diff --check` before completion. No real confirmed run is part of verification.
