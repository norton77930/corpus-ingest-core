# Implementation Plan: Corpus Remediation Runner

**Branch**: `main` | **Date**: 2026-07-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-corpus-remediation-runner/spec.md`

## Summary

Add a deterministic-only corpus remediation runner for one podcast. The feature refreshes the 009 remediation plan, selects ready local deterministic actions, previews them in dry-run mode without writing artifacts, and writes latest JSON/Markdown run reports only after confirmed bounded execution. It deliberately excludes download, transcription, semantic/LLM work, MCP changes, network, RSS, `.env`, stock-lens query inventory, stock-lens synthesis, and automatic cache rebuild.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library plus existing `corpus_ingest_core` modules. No new dependency.

**Storage**: Confirmed runs write latest derived artifacts under `data/corpus/{podcast_id}/corpus-remediation-run.json` and `.md`. Dry-runs write no artifacts.

**Testing**: `pytest>=8.0`; new targeted `tests/test_corpus_remediation_runner.py`, existing corpus index/remediation tests, MCP registry guard, and docs/spec guard tests when docs are touched.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Select and run fixture-sized local corpus actions deterministically without loading raw transcript text, evidence snippets, semantic summary bodies, prompt text, or raw LLM output into runner outputs.

**Constraints**: Dry-run no-write; confirmed execution requires `confirm=True` and an episode or action-family filter; deterministic families only; no shelling out to scripts; no RSS/network; no SQLite cache dependency or rebuild; no `.env` read; no live market API; no LLM call; no MCP surface change; no generation timestamp in run report content.

**Scale/Scope**: One podcast per run; selected per-episode deterministic remediation actions only; v1 excludes audio download, transcription, semantic summary, semantic review, stock-lens, and synthesis.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI remains a thin wrapper that parses args, calls the core runner, and formats result metadata.
- Side effects are dry-run first. Dry-run lists selected/skipped/excluded actions and planned reads/writes but writes no artifacts. Confirmed execution is explicit and filter-bounded.
- LLM work is excluded. The runner must not construct providers, read `.env`, print secrets, call LLM APIs, or execute semantic actions.
- Research outputs keep evidence separation by reporting metadata, paths, counts, statuses, warnings, and outcomes only; no podcast evidence text or model body text is copied.
- External-data boundary entries remain availability/status markers. This feature adds no live market API and does not fabricate market facts.
- Investment safety is explicit: generated output must not include buy/sell/hold, target price, guaranteed return, personalized recommendation, or statements implying an investment action.
- Cache rebuild remains manual. Confirmed execution may warn that cache metadata can be stale but must not call `rebuild_cache`.
- Verification will include targeted runner tests, corpus index/remediation regression tests, MCP registry guard, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

**Initial Gate Result**: PASS. Dry-run report writing was explicitly changed to stdout-only to avoid a constitution dry-run no-write violation.

## Project Structure

### Documentation (this feature)

```text
specs/010-corpus-remediation-runner/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-remediation-runner.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_remediation_runner.py
├── corpus_remediation_plan.py
├── storage.py
├── models.py
├── errors.py
└── __init__.py

scripts/
└── run_corpus_remediation.py

tests/
├── test_corpus_remediation_runner.py
├── test_corpus_remediation_plan.py
├── test_corpus_index.py
└── test_mcp_tool_registry_contract.py
```

**Structure Decision**: Implement a single core runner module and thin CLI wrapper inside the existing package layout. Reuse 009 `generate_corpus_remediation_plan()` as the refreshed source of truth and existing deterministic artifact generators for confirmed execution. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- Dry-run writes no artifacts; confirmed execution writes latest run report artifacts.
- Deterministic allowlist is `extractive_summary`, `mentions`, `episode_intelligence`, `industry_mapping`, and `external_boundary`.
- Confirmed execution requires `episode_ref` or `action_family`.
- Execution calls existing core functions directly and never shells out to scripts.
- Single-action failure is contained; unrelated actions continue and same-run downstream dependents are skipped.
- CLI/core only in v1; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-remediation-runner.md](contracts/corpus-remediation-runner.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with mode, filters, source plan paths, report paths when written, selected counts, outcome counts, and row metadata.
- Dry-run stdout contains the same metadata shape but `report_json_path` and `report_markdown_path` are null.
- Confirmed run JSON/Markdown contain deterministic summary counts and per-action outcome rows.
- Storage helper returns `corpus-remediation-run.json` and `.md` paths under the existing corpus directory.
- CLI prints JSON metadata with mode, report paths when present, and selected/executed/skipped counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, makes dry-run no-write, requires bounded confirmation for execution, excludes LLM/network/MCP/cache rebuild behavior, keeps secret values and raw evidence out of outputs, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.
