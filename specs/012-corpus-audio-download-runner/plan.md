# Implementation Plan: Corpus Audio Download Runner

**Branch**: `main` | **Date**: 2026-07-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-corpus-audio-download-runner/spec.md`

## Summary

Add a dry-run-first corpus audio download runner for one podcast. The feature refreshes the 009 remediation plan, selects only episodes whose audio artifact is missing and whose audio action is ready, previews eligible and skipped rows without RSS/network/download/report writes, and writes latest JSON/Markdown run reports only after confirmed single-episode download attempts or explicit rejection. It deliberately excludes transcription, deterministic downstream remediation, LLM work, MCP changes, `.env`, full source URL output, stock-lens, synthesis, and automatic cache rebuild.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library plus existing `corpus_ingest_core` modules. No new dependency.

**Storage**: Confirmed runs write latest derived artifacts under `data/corpus/{podcast_id}/corpus-audio-download-run.json` and `.md`. Dry-runs write no artifacts.

**Testing**: `pytest>=8.0`; new targeted `tests/test_corpus_audio_download_runner.py`, existing corpus index/remediation tests, downloader regression tests, local transcription runner regression tests, MCP registry guard, and docs/spec guard tests when docs are touched.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Preview fixture-sized corpus state deterministically without RSS or network access. Confirmed execution is intentionally one episode per run to bound bandwidth, remote side effects, and local artifact writes.

**Constraints**: Dry-run no-write; dry-run no RSS/network/downloader call; confirmed execution requires `confirm=True` and one non-empty episode reference; audio status must be `missing`; audio remediation action must be `ready`; no shelling out to scripts; no transcription; no downstream remediation; no SQLite cache dependency or rebuild; no `.env` read; no live market API; no LLM call; no MCP surface change; no full source URL output; no generation timestamp in run report content.

**Scale/Scope**: One podcast per run; v1 selects per-episode audio gaps only. v1 excludes batch download, retry/rate-limit policy, transcription, transcript repair, semantic summary, semantic review, deterministic downstream remediation, stock-lens, synthesis, and MCP exposure.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI remains a thin wrapper that parses args, calls the core runner, and formats result metadata.
- Side effects are dry-run first. Dry-run lists selected/skipped rows and planned metadata but writes no artifacts and does not read RSS or call network. Confirmed execution is explicit and single-episode bounded.
- LLM work is excluded. The runner must not construct providers, read `.env`, print secrets, call LLM APIs, or execute semantic actions.
- Research outputs keep evidence separation by reporting metadata, paths, counts, statuses, warnings, and outcomes only; no transcript text, prompt text, LLM body text, or full source URL is copied.
- External-data boundary entries remain availability/status markers. This feature adds no live market API and does not fabricate market facts.
- Investment safety is explicit: generated output must not include buy/sell/hold, target price, guaranteed return, personalized recommendation, or statements implying an investment action.
- Cache rebuild remains manual. Confirmed download may warn that transcription/downstream/cache steps remain manual but must not call `transcribe_episode`, `run_corpus_remediation`, or `rebuild_cache`.
- Verification will include targeted runner tests, corpus index/remediation/local transcription regression tests, downloader regression tests, MCP registry guard, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

**Initial Gate Result**: PASS. The design is dry-run first, allows network only in confirmed single-episode execution through existing downloader behavior, excludes LLM/MCP/cache rebuild behavior, and keeps source URLs and secrets out of outputs.

## Project Structure

### Documentation (this feature)

```text
specs/012-corpus-audio-download-runner/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-audio-download-runner.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_audio_download_runner.py
├── corpus_remediation_plan.py
├── downloader.py
├── storage.py
├── models.py
├── errors.py
└── __init__.py

scripts/
└── run_corpus_audio_download.py

tests/
├── test_corpus_audio_download_runner.py
├── test_corpus_remediation_plan.py
├── test_corpus_index.py
├── test_corpus_local_transcription_runner.py
├── test_downloader.py
└── test_mcp_tool_registry_contract.py
```

**Structure Decision**: Implement a single core runner module and thin CLI wrapper inside the existing package layout. Reuse 009 `generate_corpus_remediation_plan()` as refreshed source metadata and existing `download_audio()` for confirmed single-episode download. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- Dry-run writes no artifacts and does not read RSS, call network, or call `download_audio()`.
- Selection is limited to audio action ready and audio status exactly missing.
- Confirmed execution requires one non-empty `episode_ref`.
- Confirmed execution calls existing `download_audio(podcast_id, episode_ref)` directly.
- Full source URLs are omitted from every runner output.
- CLI/core only in v1; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-audio-download-runner.md](contracts/corpus-audio-download-runner.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with mode, source plan paths, report paths when written, selected counts, outcome counts, and row metadata.
- Dry-run stdout contains the same metadata shape but `report_json_path` and `report_markdown_path` are null.
- Confirmed runs write latest JSON/Markdown reports after an eligible episode is attempted or an explicitly requested episode is rejected by selection criteria.
- Storage helper returns `corpus-audio-download-run.json` and `.md` paths under the existing corpus directory.
- CLI prints JSON metadata with mode, report paths when present, and selected/downloaded/reused/skipped/failed counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, makes dry-run no-write/no-network, requires bounded confirmation for execution, excludes transcription/LLM/MCP/cache rebuild behavior, keeps secret values and full source URLs out of outputs, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.
