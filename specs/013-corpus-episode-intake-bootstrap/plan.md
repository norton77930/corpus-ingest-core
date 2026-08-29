# Implementation Plan: Corpus Episode Intake Bootstrap

**Branch**: `main` | **Date**: 2026-07-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-corpus-episode-intake-bootstrap/spec.md`

## Summary

Add a dry-run-first episode intake bootstrap feature for one podcast. The feature resolves `latest` or one explicit episode from the configured RSS feed, previews safe metadata without writes, and on confirmed execution writes only local episode seed metadata plus latest intake run JSON/Markdown reports. It then lets 008 discover the seeded episode, 009 plan audio remediation, 012 download audio, 011 transcribe local audio, and 010 run deterministic downstream remediation. It excludes direct download, transcription, downstream remediation, LLM, MCP changes, `.env`, cache rebuild, raw feed body output, full source URL output, and investment advice behavior.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing package only; use standard library plus existing `corpus_ingest_core` modules and existing feed reader. No new dependency.

**Storage**: Confirmed runs write one seed metadata artifact under `data/corpus/{podcast_id}/episode-seeds/` and latest derived reports under `data/corpus/{podcast_id}/corpus-episode-intake-run.json` and `.md`. Dry-runs write no artifacts.

**Testing**: `pytest>=8.0`; new targeted `tests/test_corpus_episode_intake.py`, existing corpus index/remediation/audio runner regression tests, feed reader regression tests, MCP registry guard, and docs/spec guard tests when docs are touched.

**Target Platform**: Local Windows-first Python package and CLI, with paths built through existing storage helpers.

**Project Type**: Single Python library package with thin CLI wrapper.

**Performance Goals**: Resolve one feed episode per run. Dry-run and confirmed runs are intentionally single-selector to bound RSS reads and local writes.

**Constraints**: Dry-run no-write; dry-run may read configured RSS; confirmed execution requires explicit `confirm=True` and writes seed/report only; no download; no transcription; no downstream remediation; no SQLite cache dependency or rebuild; no `.env` read; no live market API; no LLM call; no MCP surface change; no full source URL, query string, raw description, secret, traceback, or generation timestamp in written or printed output.

**Scale/Scope**: One podcast and one selector per run. v1 supports `latest` and one explicit episode reference. v1 excludes batch latest-N intake, automatic download, transcription, deterministic downstream remediation, semantic work, stock-lens, synthesis, MCP exposure, and cache rebuild.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI remains a thin wrapper that parses args, calls the core intake runner, and formats result metadata.
- Side effects are dry-run first. Dry-run resolves feed metadata but writes no artifacts. Confirmed execution is explicit and one-episode bounded.
- LLM work is excluded. The runner must not construct providers, read `.env`, print secrets, call LLM APIs, or execute semantic actions.
- Research outputs keep evidence separation by reporting metadata, paths, counts, statuses, warnings, and outcomes only; no transcript text, prompt text, LLM body text, raw feed descriptions, or full source URL is copied.
- External-data boundary entries remain availability/status markers. This feature adds no live market API and does not fabricate market facts.
- Investment safety is explicit: generated output must not include buy/sell/hold, target price, guaranteed return, personalized recommendation, or statements implying an investment action.
- Cache rebuild remains manual. Confirmed intake may warn that download, transcription, downstream remediation, and cache rebuild remain manual but must not call those operations.
- Verification will include targeted intake tests, corpus index/remediation/audio runner regression tests, feed reader regression tests, MCP registry guard, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

**Initial Gate Result**: PASS. The design is dry-run first, uses RSS only for selector resolution, keeps confirmed writes seed/report only, excludes LLM/MCP/cache rebuild behavior, and keeps source URLs and secrets out of outputs.

## Project Structure

### Documentation (this feature)

```text
specs/013-corpus-episode-intake-bootstrap/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-episode-intake.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_episode_intake.py
├── corpus_index.py
├── corpus_remediation_plan.py
├── corpus_audio_download_runner.py
├── feed_reader.py
├── storage.py
├── models.py
├── errors.py
└── __init__.py

scripts/
└── run_corpus_episode_intake.py

tests/
├── test_corpus_episode_intake.py
├── test_corpus_index.py
├── test_corpus_remediation_plan.py
├── test_corpus_audio_download_runner.py
├── test_feed_reader.py
└── test_mcp_tool_registry_contract.py
```

**Structure Decision**: Implement a single core intake module and thin CLI wrapper inside the existing package layout. Reuse existing feed resolution for selector lookup. Extend 008 discovery to include local seed metadata, and let 009/012 consume that refreshed local metadata. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). Key decisions:

- 013 is seed-only; confirmed execution does not call 012, downloader, transcriber, remediation runner, or cache rebuild.
- Dry-run may read RSS because selector resolution is the purpose of intake, but dry-run writes no artifacts.
- Seed metadata is local metadata only and omits full source URLs, audio URLs, raw description, and feed HTML body.
- 008 discovers seed metadata as an episode source without adding a new artifact family to corpus counts.
- 009 can mark seeded episodes with local audio missing and feed audio available as ready for audio download.
- CLI/core only in v1; no MCP registry or response envelope changes.

## Phase 1: Design Summary

See [data-model.md](data-model.md), [contracts/corpus-episode-intake.md](contracts/corpus-episode-intake.md), and [quickstart.md](quickstart.md).

- Public core function returns a typed result with mode, selector, resolved episode metadata, planned writes, report paths when written, counts, rows, and warnings.
- Dry-run stdout contains metadata-only result shape with null report paths and seed path as planned write only.
- Confirmed runs write one seed JSON artifact and latest JSON/Markdown reports after a selector is resolved or a confirmed attempt is rejected.
- Storage helpers return seed path and latest run report paths under the existing corpus directory.
- CLI prints JSON metadata with mode, selector, report paths when present, and selected/seeded/reused/skipped/failed/rejected counts.

## Constitution Check Post-Design

*GATE: Re-check after Phase 1 design.*

PASS. The design keeps runtime behavior in core, preserves a thin CLI, makes dry-run no-write, requires explicit confirmation for seed writes, excludes download/transcription/remediation/LLM/MCP/cache rebuild behavior, keeps secret values and full source URLs out of outputs, and keeps no-investment-advice boundaries explicit.

## Complexity Tracking

No constitution violations or unusual complexity are introduced.
