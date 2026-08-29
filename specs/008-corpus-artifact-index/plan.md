# Implementation Plan: Corpus Artifact Index

**Branch**: `008-corpus-artifact-index` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-corpus-artifact-index/spec.md`

## Summary

Add a deterministic, offline corpus status index for one podcast. The feature scans only local per-episode artifacts, writes JSON and Markdown status artifacts under `data/corpus/{podcast_id}/`, and exposes the capability through core code plus a thin CLI. It deliberately excludes RSS, network calls, SQLite cache reads, stock-lens/query-level inventory, MCP tool changes, LLM calls, raw transcript/evidence text, and investment advice.

## Technical Context

**Language/Version**: Python >=3.11

**Primary Dependencies**: Existing standard-library file/JSON handling plus existing project modules; no new package dependency.

**Storage**: Local derived artifacts under `data/corpus/{podcast_id}/corpus-index.json` and `.md`.

**Testing**: `pytest>=8.0`; targeted corpus index tests plus existing MCP registry guard.

**Target Platform**: Local Windows/PowerShell development and any Python environment supported by the package.

**Project Type**: Python package with thin CLI wrapper.

**Performance Goals**: Scan fixture-sized local corpora deterministically without loading raw transcript text, summary bodies, or semantic summary bodies.

**Constraints**: Offline-only; no RSS/network; no SQLite cache dependency; no `.env` read; no live market API; no LLM call; no MCP surface change; no generation timestamp in artifact content.

**Scale/Scope**: v1 covers one podcast per invocation and per-episode artifact families only: audio, transcript, extractive summary, semantic summary, semantic summary review, mentions, episode intelligence report, industry mapping, and external boundary.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; the CLI will parse options, call core, and print a compact JSON result.
- Dry-run is not required because the only write is a deterministic derived status artifact with no provider call, download, transcription, workflow execution, or cache rebuild. The feature still reports planned output paths through CLI result metadata.
- No LLM step is possible; `api_cost_ack`, `.env`, provider settings, API keys, and tokens are not involved.
- Research status remains separated: podcast artifact presence, transcript validation status, external boundary status, and semantic review status are represented as metadata only.
- External data remains local boundary/status metadata only; no live provider, HTTP call, API key, price, financial, or news fact is introduced.
- Investment safety remains explicit through Markdown notice and absence of recommendation fields.
- Cache rebuild remains manual; this feature does not read from or rebuild SQLite cache.
- Verification will include targeted tests for corpus index behavior, `tests/test_mcp_tool_registry_contract.py`, relevant docs/spec tests if touched, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`.

## Project Structure

### Documentation (this feature)

```text
specs/008-corpus-artifact-index/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-and-artifact-contract.md
├── checklists/
│   ├── requirements.md
│   └── artifact-index.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── __init__.py
├── corpus_index.py
├── errors.py
├── models.py
└── storage.py

scripts/
└── generate_corpus_index.py

tests/
├── test_corpus_index.py
└── test_mcp_tool_registry_contract.py

docs/
├── architecture.md
└── verification-matrix.md

README.md
specs/README.md
```

**Structure Decision**: Implement a single core module and thin CLI wrapper inside the existing package layout. Reuse existing `models.py`, `storage.py`, and error hierarchy for public contracts and path conventions. Do not add MCP server code.

## Phase 0: Research Summary

See [research.md](research.md). All technical unknowns are resolved:

- Source of truth: local artifact scanner, not RSS or SQLite cache.
- Regeneration: always overwrite derived corpus index with deterministic content.
- Payload depth: status/counts/paths only, no text snippets or body content.
- Scope boundary: per-episode artifacts only; query-level stock-lens inventory deferred.
- Semantic review: latest timestamped semantic review report selected deterministically.
- Interface: core + CLI only; MCP exposure deferred.

## Phase 1: Design Summary

See [data-model.md](data-model.md) and [contracts/cli-and-artifact-contract.md](contracts/cli-and-artifact-contract.md).

- Primary entities: Corpus Index, Episode Corpus Row, Artifact Family Status, Semantic Review Status.
- Public function returns a typed result with output paths, episode count, warning count, and artifact-family counts.
- JSON artifact is automation-facing and stable for unchanged local artifacts.
- Markdown artifact is human-facing and table-based, with no raw transcript/evidence/LLM body text.
- CLI prints metadata-only JSON to stdout and reports domain errors to stderr.

## Complexity Tracking

No constitution violations or additional complexity exceptions are required.
