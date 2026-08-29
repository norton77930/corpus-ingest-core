# Implementation Plan: Latest Episode Deterministic Workflow

**Branch**: `017-corpus-latest-episode-deterministic-workflow` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`/specs/017-corpus-latest-episode-deterministic-workflow/spec.md`

## Summary

Add a core-owned, dry-run-first workflow that resolves one configured podcast's
latest episode once and advances it through local intake, download,
transcription, and all required deterministic remediation actions. A dedicated
MCP tool, thin CLI, and portable Skill expose the same workflow without
allowing LLM, secret, retry, batch, scheduler, or cache-rebuild behavior. The
workflow ends at `ready_for_semantic_summary`; 016 remains a separate,
human-approved one-action workflow.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Standard library, existing project runners, FastMCP,
and faster-whisper only through the existing local-transcription runner

**Storage**: Existing local `data/` artifacts and per-podcast metadata-only JSON
and Markdown reports; SQLite cache remains stale until manually rebuilt

**Testing**: pytest with monkeypatched local storage and runner dependencies

**Target Platform**: Local Windows PowerShell execution and stdio MCP clients

**Project Type**: Python library with thin CLI and MCP surfaces

**Performance Goals**: One selected episode per invocation; no concurrency,
batching, background task, or scheduler behavior

**Constraints**: Dry-run writes zero files; confirmed latest selector is resolved
once; no `.env`/provider/LLM access; output is metadata-only; no automatic retry
or cache rebuild

**Scale/Scope**: One configured podcast profile and one latest episode per run;
at most the existing five deterministic remediation families are advanced

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

- Core logic stays in `src/corpus_ingest_core`; CLI and MCP remain thin.
- Every side effect is behind `confirm=True`; dry-run returns safe planned
  metadata and writes zero files.
- No LLM, provider, `.env`, acknowledgement, or secret handling path is added.
- The workflow only creates existing categories of local deterministic artifacts
  and excludes semantic/external work.
- No live market provider or investment-advice content is added.
- Cache rebuild is never called; confirmed output warns that cache may be stale.
- Targeted tests, full pytest, compileall, docs guards, and diff checks are
  required before completion.

## Project Structure

### Documentation (this feature)

```text
specs/017-corpus-latest-episode-deterministic-workflow/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── latest-episode-deterministic-workflow.md
├── checklists/
└── tasks.md
```

### Source Code (repository root)

```text
src/corpus_ingest_core/
├── corpus_latest_episode_deterministic_workflow_runner.py
├── models.py
├── storage.py
├── errors.py
├── __init__.py
└── mcp_server.py

scripts/
└── run_corpus_latest_episode_deterministic_workflow.py

.agents/skills/
└── corpus-latest-episode-processing/SKILL.md

tests/
├── test_corpus_latest_episode_deterministic_workflow_runner.py
├── test_mcp_server.py
├── test_mcp_tool_registry_contract.py
├── test_mcp_setup_validation.py
└── test_corpus_latest_episode_processing_skill.py
```

**Structure Decision**: Add one focused runner and reuse existing public intake,
audio, transcription, deterministic-remediation, storage, model, error, MCP,
CLI, and Skill patterns. No dependency or service layer is added.

## Design Decisions

1. Resolve `latest` once with an intake dry-run and retain only the canonical
   episode reference for all later stage probes and executions.
2. Use the private `_select_next_stage(..., allow_semantic_handoff=True)`
   selector only to choose the next deterministic stage for the pinned canonical
   episode. Dispatch public stage runners, not 016's confirmed one-action
   runner; the 014 public workflow contract remains unchanged.
3. Run deterministic remediation with `max_actions=1`, re-evaluate after each
   successful action, and stop on its first non-success outcome. This avoids the
   existing all-actions runner advancing an independent family after failure.
4. Bound the remediation loop to the five existing deterministic families and
   fail closed on repeated action identity or impossible progress.
5. Add `run_corpus_latest_episode_deterministic_workflow` with only local
   transcription options. No semantic/provider/credential/force/partial input
   is exposed.
6. Add a `confirm=False` MCP wrapper and a Skill that sends `confirm=True` only
   for an unambiguous natural-language request. The Skill never loops or falls
   back to the terminal.
7. Raise the reviewed MCP registry to exactly 14 tools and update all registry,
   docs, setup, and secret-boundary guards in the same change.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All constitution gates pass | N/A |
