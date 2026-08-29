# Implementation Plan: Corpus Local Transcription Runner

**Branch**: `main` | **Date**: 2026-07-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-corpus-local-transcription-runner/spec.md`

## Summary

Add a dry-run-first local transcription runner for one podcast. The feature refreshes the 009 remediation plan, selects only episodes where local audio is available and transcript outputs are fully missing, previews eligible and skipped rows without side effects, and writes latest JSON/Markdown run reports only after confirmed single-episode runs. It deliberately excludes download, RSS/network, corrupt/partial transcript repair, LLM work, MCP changes, `.env`, stock-lens, downstream remediation, and automatic cache rebuild.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library plus existing `corpus_ingest_core` modules. No new dependency.

**Storage**: Confirmed runs write latest derived artifacts under `data/corpus/{podcast_id}/corpus-local-transcription-run.json` and `.md`. Dry-runs write no artifacts.

**Testing**: `pytest>=8.0`; new targeted `tests/test_corpus_local_transcription_runner.py`, existing corpus index/remediation tests, MCP registry guard, downloader/transcriber regression guard where needed, and docs/spec guard tests when docs are touched.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Preview fixture-sized corpus state deterministically without loading transcription models. Confirmed execution is intentionally one episode per run to bound local runtime and hardware resource impact.

**Constraints**: Dry-run no-write; confirmed execution requires `confirm=True` and one episode reference; local audio path must exist; transcript status must be exactly missing; no download; no shelling out to scripts; no RSS/network; no SQLite cache dependency or rebuild; no `.env` read; no live market API; no LLM call; no MCP surface change; no generation timestamp in run report content.

**Scale/Scope**: One podcast per run; v1 selects per-episode transcript gaps only where audio is already local. v1 excludes audio download, corrupt/partial transcript repair, semantic summary, semantic review, deterministic downstream remediation, stock-lens, synthesis, and batch transcription.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI remains a thin wrapper that parses args, calls the core runner, and formats result metadata.
- Side effects are dry-run first. Dry-run lists selected/skipped rows and planned reads/writes but writes no artifacts and does not load transcription models. Confirmed execution is explicit and single-episode bounded.
- LLM work is excluded. The runner must not construct providers, read `.env`, print secrets, call LLM APIs, or execute semantic actions.
- Research outputs keep evidence separation by reporting metadata, paths, counts, statuses, warnings, and outcomes only; no transcript text or model body text is copied.
- External-data boundary entries remain availability/status markers. This feature adds no live market API and does not fabricate market facts.
- Investment safety is explicit: generated output must not include buy/sell/hold, target price, guaranteed return, personalized recommendation, or statements implying an investment action.
- Cache rebuild remains manual. Confirmed transcription may warn that cache metadata can be stale but must not call `rebuild_cache`.
- Verification will include targeted runner tests, corpus index/remediation regression tests, MCP registry guard, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

**Initial Gate Result**: PASS. The design is dry-run first, local-only except for confirmed transcription using an existing local audio path, excludes LLM/network/MCP/cache rebuild behavior, and keeps transcript text and secrets out of outputs.

## Project Structure

### Documentation (this feature)

```text
specs/011-corpus-local-transcription-runner/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-local-transcription-runner.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_local_transcription_runner.py
├── corpus_remediation_plan.py
├── transcriber.py
├── storage.py
├── models.py
├── errors.py
└── __init__.py

scripts/
└── run_corpus_local_transcription.py

tests/
├── test_corpus_local_transcription_runner.py
├── test_corpus_remediation_plan.py
├── test_corpus_index.py
├── test_transcriber.py
└── test_mcp_tool_registry_contract.py
```

**Structure Decision**: Implement a single core runner module and thin CLI wrapper inside the existing package layout. Reuse 009 `generate_corpus_remediation_plan()` as refreshed source metadata and existing `transcribe_episode()` for confirmed single-episode transcription with an explicit local `audio_path`. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- Dry-run writes no artifacts and does not load transcription models.
- Selection is limited to local audio available, local audio path exists, transcript action ready, and transcript status exactly missing.
- Confirmed execution requires one `episode_ref`.
- Confirmed execution passes explicit local `audio_path` to the existing transcription core to avoid download.
- Unsafe transcript states are skipped in v1 rather than overwritten.
- CLI/core only in v1; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-local-transcription-runner.md](contracts/corpus-local-transcription-runner.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with mode, source plan paths, report paths when written, selected counts, outcome counts, and row metadata.
- Dry-run stdout contains the same metadata shape but `report_json_path` and `report_markdown_path` are null.
- Confirmed runs write latest JSON/Markdown reports after an eligible episode is attempted or an explicitly requested episode is rejected by local selection criteria.
- Storage helper returns `corpus-local-transcription-run.json` and `.md` paths under the existing corpus directory.
- CLI prints JSON metadata with mode, report paths when present, and selected/executed/skipped/failed counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, makes dry-run no-write, requires bounded confirmation for execution, excludes download/LLM/network/MCP/cache rebuild behavior, keeps secret values and raw transcript text out of outputs, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.
