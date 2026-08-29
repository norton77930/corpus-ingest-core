# Implementation Plan: Corpus Remediation Plan

**Branch**: `main` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-corpus-remediation-plan/spec.md`

## Summary

Add a deterministic, offline corpus remediation plan for one podcast. The feature refreshes the 008 corpus artifact index, derives ordered full-ladder remediation actions from local per-episode artifact status, and writes JSON and Markdown plan artifacts under `data/corpus/{podcast_id}/`. It deliberately does not execute remediation, downloads, transcription, summaries, workflow steps, LLM calls, MCP tools, SQLite cache rebuilds, RSS, network reads, live market data, or stock-lens query inventory.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library plus existing `corpus_ingest_core` modules. No new dependency.

**Storage**: Local derived artifacts under `data/corpus/{podcast_id}/corpus-remediation-plan.json` and `.md`, plus refreshed 008 corpus index artifacts under the same corpus directory.

**Testing**: `pytest>=8.0`; new targeted `tests/test_corpus_remediation_plan.py` plus existing MCP registry guard and docs/spec guard tests when documentation is touched.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Scan fixture-sized local corpora deterministically without loading raw transcript text, evidence snippets, semantic summary bodies, prompt text, or raw LLM output.

**Constraints**: Offline-only; local artifacts only; refresh corpus index first; no RSS/network; no SQLite cache dependency; no `.env` read; no live market API; no LLM call; no MCP surface change; no automatic cache rebuild; no generation timestamp in artifact content.

**Scale/Scope**: One podcast per run; per-episode artifact families only; v1 excludes stock-lens and stock-lens synthesis because they are query-level artifacts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI remains a thin wrapper that parses `--podcast`, calls the core function, and formats result metadata.
- Remediation actions are plan-only and non-executing. The generator writes only derived plan artifacts; listed actions that would perform side effects are marked manual, dry-run-style, optional, or gated.
- LLM semantic actions are opt-in future work only. The plan may mark exact `api_cost_ack` as required for later execution, but this feature must not construct providers, read `.env`, print secrets, or call LLM APIs.
- Research outputs keep evidence separation by reporting status, paths, blockers, warnings, and action metadata only; no podcast evidence text or model body text is copied.
- External-data boundary entries remain availability/status markers. This feature adds no live market API and does not fabricate market facts.
- Investment safety is explicit: generated artifacts must not include buy/sell/hold, target price, guaranteed return, personalized recommendation, or statements implying an investment action.
- Cache rebuild remains manual. This feature must not call `rebuild_cache`; it may report that repair actions outside this feature can leave cache metadata stale.
- Verification will include targeted remediation plan tests, `tests/test_mcp_tool_registry_contract.py`, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

**Initial Gate Result**: PASS. No constitution violation is required for this planning package.

## Project Structure

### Documentation (this feature)

```text
specs/009-corpus-remediation-plan/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-remediation-plan.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_remediation_plan.py
├── corpus_index.py
├── storage.py
├── models.py
├── errors.py
└── __init__.py

scripts/
└── generate_corpus_remediation_plan.py

tests/
├── test_corpus_remediation_plan.py
└── test_mcp_tool_registry_contract.py
```

**Structure Decision**: Implement a single core module and thin CLI wrapper inside the existing package layout. Reuse existing `models.py`, `storage.py`, `errors.py`, and the 008 `generate_corpus_index()` public contract. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- Source of truth: refresh and read the 008 corpus index, then derive remediation actions from local status metadata.
- Action model: full-ladder per-episode actions ordered by artifact dependency.
- Safety: action text is advisory only; no remediation operation is executed by this feature.
- Semantic work: optional and gated; no provider construction, `.env` read, prompt text, semantic body, or raw LLM output.
- Interface: core + CLI only; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-remediation-plan.md](contracts/corpus-remediation-plan.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with output paths and summary counts.
- JSON artifact contains top-level summary counts plus deterministic episode rows and action rows.
- Markdown artifact is table-oriented and factual: paths, counts, blockers, warnings, and next actions.
- Storage helper returns `corpus-remediation-plan.json` and `.md` paths under the existing corpus directory.
- CLI prints JSON metadata with output paths and summary counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, performs no repair side effects, performs no LLM or network calls, keeps secret values out of outputs, does not add MCP tools, keeps cache rebuild manual, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.
