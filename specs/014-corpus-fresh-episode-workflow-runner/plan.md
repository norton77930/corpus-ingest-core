# Implementation Plan: Corpus Fresh Episode Workflow Runner

**Branch**: `main` | **Date**: 2026-07-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-corpus-fresh-episode-workflow-runner/spec.md`

## Summary

Add a dry-run-first fresh episode workflow runner for one podcast and one episode selector. Unseeded selection may read the configured podcast RSS feed; seeded selection builds one fresh in-memory corpus snapshot and reuses it across 012/011/010 previews. Dry-run is zero-file. Confirmed execution requires `stage=next`, dispatches exactly one existing public runner, writes a deterministic workflow report, and keeps semantic/LLM/MCP/cache/stock-lens/batch work manual-only.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library and existing `corpus_ingest_core` corpus runners. No new dependency.

**Storage**: Confirmed workflow attempts write the selected public runner's existing artifacts plus latest workflow reports under `data/corpus/{podcast_id}/corpus-episode-workflow-run.json` and `.md`. A 014 dry-run creates, modifies, or deletes zero files, including index, plan, reports, stage artifacts, and `.part`.

**Testing**: `pytest>=8.0`; real six-state zero-write integration coverage, deep 008/009 failure/no-leak cases, standalone 010-012 compatibility coverage, existing 010-013 regressions, exact 12-tool MCP registry guard, cache/secret/LLM/no-advice guards, and docs/spec/governance tests.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Evaluate one podcast and one episode selector per run. Confirmed execution dispatches at most one existing stage runner.

**Constraints**: 014 dry-run is strict zero-file while standalone 010-012 dry-runs retain persisted 008/009 refresh; confirmed execution requires `confirm=True` and `stage=next`; no public API/schema/CLI/MCP changes; no full-chain, semantic/LLM, `.env`, cache rebuild, stock-lens/synthesis, batch, unsafe leakage, or generation timestamp.

**Scale/Scope**: One podcast and one selector per run. v1 supports `latest` and one explicit episode reference. v1 executes only the next safe stage and stops.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI remains a thin wrapper that parses args, calls the core workflow runner, and formats result metadata.
- Side effects are dry-run first. 014 dry-run leaves the entire local file tree unchanged; confirmed execution is explicit and one-stage bounded.
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
src/corpus_ingest_core/
├── corpus_episode_workflow_runner.py
├── corpus_index.py
├── corpus_remediation_plan.py
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

**Structure Decision**: Keep the public workflow runner and thin CLI unchanged. Split 008/009 into package-private build/persist snapshots, add package-private 010-012 preview seams, and let 014 pass one shared snapshot with `source_persisted=False`. Public 008-012 signatures, write order, result models, atomic `.part` replacement, CLI JSON, exports, and MCP registry remain unchanged. Confirmed 014 dispatch still calls exactly one existing public runner.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- 014 is an orchestrator over existing corpus runners, not a replacement for them.
- `stage=next` is the only v1 stage interface.
- Confirmed execution attempts exactly one selected stage and stops.
- 014 dry-run is zero-file and executes no stage; standalone 010-012 dry-runs still persist fresh 008/009 but no own stage report.
- Workflow reports are latest deterministic artifacts without generation timestamps.
- CLI/core only in v1; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-episode-workflow-runner.md](contracts/corpus-episode-workflow-runner.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with mode, selector, canonical episode ref, selected stage, report paths when written, counts, rows, warnings, and no-investment-advice marker.
- Dry-run stdout contains metadata-only result shape with null report paths; planned reads accept safe local dependency paths plus only the two exact non-path labels, and seeded previews reuse the same in-memory index/plan payload.
- Confirmed runs call exactly one existing public core runner, accept its refreshed state outcome, stop, and then write workflow JSON/Markdown reports.
- Storage helpers return latest workflow report paths under the existing corpus directory.
- CLI prints JSON metadata with mode, selector, selected stage, report paths when present, and selected/executed/skipped/blocked/rejected/failed counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, makes 014 dry-run zero-file, preserves standalone compatibility, requires explicit confirmation for exactly one next stage, excludes semantic/LLM/MCP/cache/stock-lens/batch behavior, keeps secret values and unsafe source content out of outputs, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.