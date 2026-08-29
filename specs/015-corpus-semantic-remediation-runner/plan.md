# Implementation Plan: Corpus Semantic Remediation Runner

**Branch**: `015-corpus-semantic-remediation-runner` | **Date**: 2026-07-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-corpus-semantic-remediation-runner/spec.md`

## Summary

Add a standalone Core+CLI runner that evaluates one explicit episode from one fresh in-memory 008/009 snapshot and previews or executes one semantic summary or semantic review action. Dry-run is strict zero-file. Confirmed semantic summary requires exact acknowledgement before profile, local environment, credential, or provider resolution; confirmed review is deterministic and never touches LLM configuration. The runner writes a confirmed-only latest metadata report and never integrates with 010, 014, MCP, cache rebuild, batch, retry, scheduling, or full-chain automation.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Python standard library and existing `corpus_ingest_core` modules only. No new dependency.

**Storage**: Existing local transcript and semantic artifacts plus additive latest runner reports under `data/corpus/{podcast_id}/corpus-semantic-remediation-run.json` and `.md`. Existing semantic review reports remain timestamped under their established reports directory.

**Testing**: `pytest>=8.0`; TDD state-table, zero-file manifest, real 008/009 snapshot, confirmed summary/review, CLI, no-leak, acknowledgement-order, MCP/cache/provider-factory, and docs/governance suites.

**Target Platform**: Windows 11 PowerShell; core remains portable Python.

**Project Type**: Python library plus thin local CLI.

**Performance Goals**: Evaluate one podcast and one explicit episode per run, build one index snapshot and one plan snapshot, and dispatch at most one existing semantic executor.

**Constraints**: Strict zero-file dry-run; no `latest`; confirmed action must be explicit; no force or partial transcript; exact acknowledgement before any confirmed-summary configuration resolution; no raw transcript/semantic/prompt/provider bodies or secret values in outputs; no automatic index/plan/cache refresh; exact 12 MCP tools unchanged.

**Scale/Scope**: One episode and one action per invocation. Local artifact counts remain bounded by one podcast corpus scan.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Local Artifacts and Evidence Traceability — PASS**: decisions and reports retain safe source paths, status, warnings, reuse/execution outcome, and review metadata without copying content bodies.
- **II. Thin Interfaces over Thick Core — PASS**: all selection, execution, safety filtering, serialization, and report rendering live in `src/corpus_ingest_core`; CLI only parses, resolves confirmed-only configuration, calls core, and prints JSON.
- **III. Dry-Run First Side Effects — PASS**: dry-run builds one in-memory 008/009 snapshot, lists planned metadata and risks, writes zero files, and calls zero executors/providers/loaders.
- **IV. LLM Opt-In and Secret Boundary — PASS**: only confirmed `semantic_summary` may send transcript content; exact acknowledgement is validated before profile/env/provider resolution, with a second core-level guard.
- **V. Evidence, Inference, and External Status Separation — PASS**: feature reports artifact state only and does not produce market facts or merge evidence classes.
- **VI. No Investment Advice — PASS**: reports and errors exclude prohibited advice and retain the no-advice flag.
- **VII. No Live Market API Without Approval — PASS**: no external market integration is added.
- **VIII. Manual Cache Rebuild — PASS**: runner only emits stale/manual-follow-up warnings.
- **IX. TDD and Verification Gates — PASS**: tasks require RED/GREEN, targeted/full pytest, compileall, docs tests, and diff hygiene.

No constitution amendment or complexity exception is required.

## Project Structure

### Documentation (this feature)

```text
specs/015-corpus-semantic-remediation-runner/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-semantic-remediation.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_semantic_remediation_runner.py   # new state reducer, executor boundary, reports
├── corpus_index.py                         # additive semantic-summary readability metadata
├── models.py                               # additive 015 request/result row/count/warning models
├── storage.py                              # additive latest runner report paths
├── errors.py                               # additive runner error
└── __init__.py                             # additive public exports

scripts/
└── run_corpus_semantic_remediation.py      # new thin CLI

tests/
├── test_corpus_semantic_remediation_runner.py
├── test_corpus_index.py
├── test_contracts.py
├── test_llm_ack_guard_contracts.py
├── test_llm_cli_no_leak.py
├── test_mcp_tool_registry_contract.py
├── test_cache_rebuild_guard.py
├── test_repository_secret_boundary.py
└── test_architecture_spec_docs.py

README.md
AGENTS.md
docs/
├── architecture.md
├── verification-matrix.md
├── agent-handoff.md
└── roadmap.md
specs/README.md
```

**Structure Decision**: Follow the existing single-package runner pattern. Add one focused 015 core module and thin CLI; reuse private 008/009 build snapshots and existing public semantic summary/review executors. Do not add a generic workflow abstraction or change 010/014/MCP.

## Phase 0: Research Decisions

See [research.md](research.md). All technical unknowns are resolved:

- Standalone 015 is safer than extending deterministic 010 or no-LLM 014.
- Preview uses exactly one private 008 build and one private 009 build; no public generators or persisters.
- A dedicated pure semantic state reducer overrides 009's generic `missing|unreadable` action rules and filters to the canonical episode before classification.
- 008 gains additive 2 MiB-bounded UTF-8 `readable`/`readability_status` metadata while retaining the legacy `status=available`; 015 alone uses the new metadata to fail closed, so existing 008/009 behavior stays compatible.
- Confirmed summary and review call the existing public executors directly exactly once; no post-write rescan or chained action.
- CLI validates confirmed-summary acknowledgement before profile or local-env resolution; core repeats the guard for direct callers.
- Review timestamp allocation and pair writes remain owned by the existing review capability; 015 records bounded failure and does not redefine or repair that contract.
- Latest runner reports are confirmed-only metadata artifacts without a generation timestamp.
- No force, partial transcript, latest selector, batch, retry, scheduler, MCP, cache rebuild, or automatic review.

## Phase 1: Design Summary

### State flow

1. Normalize and validate podcast, explicit episode, action, positive chunk settings, and confirmation rules.
2. For confirmed summary, validate exact acknowledgement before snapshot, profile, local environment, credential, provider, or writer work. Dry-run and confirmed review bypass all profile/environment resolution.
3. Build one `_CorpusIndexSnapshot`.
4. Build one `_CorpusRemediationPlanSnapshot` from the same index result/payload.
5. Select the exact episode row before reading transcript, summary, review, blocker, or action state.
6. Reduce to `semantic_summary`, `semantic_review`, `completed`, or `blocked`.
7. Dry-run returns metadata immediately.
8. Confirmed explicit action must equal the recomputed selected action:
   - mismatch or terminal state → rejected/blocked report;
   - summary → call `semantic_summarize_episode` once;
   - review → call `review_semantic_summary_smoke` once.
9. Map the executor result or bounded exception into one runner row, write the latest runner report, stop, and emit manual stale warnings.

### Public interfaces

The exact Core and CLI contract is defined in [contracts/corpus-semantic-remediation.md](contracts/corpus-semantic-remediation.md). Public additions are additive; existing models, signatures, artifact formats, and MCP envelopes remain unchanged.

### Data model

The request, decision row, counts, warning, result, and report payload are defined in [data-model.md](data-model.md). Runner output contains only metadata and safe local paths. The existing `SummaryAsset` and `SemanticSummarySmokeReviewResult` remain executor-owned results.

### Post-design Constitution Check

PASS. The design retains a thick core, strict zero-file dry-run, exact acknowledgement before LLM configuration resolution, no secret/body leakage, manual cache refresh, no market-data scope, no investment advice, and TDD/full verification. No constitution amendment or justified violation is required.

## Complexity Tracking

No constitution violations or complexity exceptions.
