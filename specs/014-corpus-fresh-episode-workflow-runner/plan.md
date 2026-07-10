# Implementation Plan: Corpus Fresh Episode Workflow Runner

**Branch**: `main` | **Date**: 2026-07-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-corpus-fresh-episode-workflow-runner/spec.md`

## Summary

Add a dry-run-first fresh episode workflow runner for one podcast and one episode selector. The runner evaluates the next safe corpus stage across existing 013 intake, 012 audio download, 011 local transcription, and 010 deterministic remediation runners. Dry-run reports the next stage without writes. Confirmed execution requires `stage=next`, executes exactly one selected stage, writes a deterministic workflow report, and keeps semantic/LLM/MCP/cache/stock-lens/batch work manual-only.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library and existing `podcast_ingest_core` corpus runners. No new dependency.

**Storage**: Confirmed workflow attempts write latest reports under `data/corpus/{podcast_id}/corpus-episode-workflow-run.json` and `.md`. Dry-runs write no workflow artifacts.

**Testing**: `pytest>=8.0`; new targeted `tests/test_corpus_episode_workflow_runner.py`, existing 010-013 corpus runner regression tests, corpus index/remediation plan regression tests, MCP registry guard, docs/spec guard tests when docs are touched.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Evaluate one podcast and one episode selector per run. Confirmed execution dispatches at most one existing stage runner.

**Constraints**: Dry-run no-write; confirmed execution requires `confirm=True` and `stage=next`; no full-chain automation; no semantic/LLM execution; no MCP registry changes; no `.env` reads; no automatic SQLite cache rebuild; no stock-lens/synthesis; no batch latest-N; no unsafe output leakage or generation timestamp.

**Scale/Scope**: One podcast and one selector per run. v1 supports `latest` and one explicit episode reference. v1 executes only the next safe stage and stops.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/podcast_ingest_core`; CLI remains a thin wrapper that parses args, calls the core workflow runner, and formats result metadata.
- Side effects are dry-run first. Dry-run evaluates one next stage and writes no workflow or stage artifacts. Confirmed execution is explicit and one-stage bounded.
- LLM work is excluded. The runner must not construct providers, read `.env`, print secrets, call LLM APIs, or execute semantic actions.
- Research outputs keep evidence separation by reporting metadata, paths, counts, statuses, warnings, and outcomes only; no transcript text, evidence snippets, prompt text, LLM body text, semantic body text, or full source URL is copied.
- External-data boundary entries remain availability/status markers. This feature adds no live market API and does not fabricate market facts.
- Investment safety is explicit: generated output must not include buy/sell/hold, target price, guaranteed return, personalized recommendation, or statements implying an investment action.
- Cache rebuild remains manual. Confirmed workflow may warn that cache metadata may be stale but must not call cache rebuild.
- Verification will include targeted workflow tests, corpus runner regression tests, corpus index/remediation plan regression tests, MCP registry guard, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

**Initial Gate Result**: PASS. The design is dry-run first, core-only, stage-bounded, excludes LLM/MCP/cache rebuild behavior, and keeps source URLs, transcript bodies, prompt bodies, secrets, and investment advice out of outputs.

## Project Structure

### Documentation (this feature)

```text
specs/014-corpus-fresh-episode-workflow-runner/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-episode-workflow-runner.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/podcast_ingest_core/
├── corpus_episode_workflow_runner.py
├── corpus_episode_intake.py
├── corpus_audio_download_runner.py
├── corpus_local_transcription_runner.py
├── corpus_remediation_runner.py
├── storage.py
├── models.py
├── errors.py
└── __init__.py

scripts/
└── run_corpus_episode_workflow.py

tests/
├── test_corpus_episode_workflow_runner.py
├── test_corpus_episode_intake.py
├── test_corpus_audio_download_runner.py
├── test_corpus_local_transcription_runner.py
├── test_corpus_remediation_runner.py
├── test_corpus_index.py
├── test_corpus_remediation_plan.py
└── test_mcp_tool_registry_contract.py
```

**Structure Decision**: Implement a single core workflow runner and thin CLI wrapper. Reuse the existing 013, 012, 011, and 010 runners for stage behavior instead of duplicating artifact execution. Add only workflow result/report models, storage helper, error type, and exports. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- 014 is an orchestrator over existing corpus runners, not a replacement for them.
- `stage=next` is the only v1 stage interface.
- Confirmed execution attempts exactly one selected stage and stops.
- Dry-run writes no workflow report and executes no stage.
- Workflow reports are latest deterministic artifacts without generation timestamps.
- CLI/core only in v1; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-episode-workflow-runner.md](contracts/corpus-episode-workflow-runner.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with mode, selector, canonical episode ref, selected stage, report paths when written, counts, rows, warnings, and no-investment-advice marker.
- Dry-run stdout contains metadata-only result shape with null report paths.
- Confirmed runs call exactly one existing core runner and then write workflow JSON/Markdown reports.
- Storage helpers return latest workflow report paths under the existing corpus directory.
- CLI prints JSON metadata with mode, selector, selected stage, report paths when present, and selected/executed/skipped/blocked/rejected/failed counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, makes dry-run no-write, requires explicit confirmation for exactly one next stage, excludes semantic/LLM/MCP/cache/stock-lens/batch behavior, keeps secret values and unsafe source content out of outputs, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.