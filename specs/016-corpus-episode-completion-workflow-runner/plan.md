# Implementation Plan: Corpus Episode Completion Workflow Runner

**Branch**: `016-corpus-episode-completion-workflow-runner` | **Date**:
2026-07-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from
`specs/016-corpus-episode-completion-workflow-runner/spec.md`

## Summary

Add one additive Core coordinator and thin CLI that preview or execute at most
one safe action across the existing 013–015 episode-completion ladder. A
dry-run resolves one episode, uses one fresh in-memory 008/009 snapshot pair,
and returns deterministic bounded metadata with strict zero-file behavior.
Confirmed execution requires the canonical episode reference and exact
selected action, dispatches one existing stage runner, writes one latest 016
report pair, and stops. Expose the coordinator as the thirteenth reviewed stdio
MCP tool and add one portable Agent Skill that enforces preview, explanation,
human approval, exact confirmation, report, and stop.

## Technical Context

**Language/Version**: Python 3.11+; repository verification environment uses
Python 3.12.

**Primary Dependencies**: Existing `podcast_ingest_core` modules, Python
standard library, FastMCP from `mcp[cli]>=1.27,<2`, feedparser, PyYAML, and
requests. No new dependency.

**Storage**: Existing RSS/local corpus/audio/transcript/deterministic/semantic
artifacts plus confirmed-only latest reports at
`data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json` and
`.md`. Dry-run writes no files.

**Testing**: `pytest>=8.0`; RED→GREEN state-table, zero-file manifest,
single-snapshot, one-dispatch, acknowledgement-order, CLI, MCP envelope/registry,
Skill protocol, no-leak, cache, existing-contract, docs, and governance tests.

**Target Platform**: Windows 11 PowerShell for repository development; portable
Python Core and local stdio MCP server.

**Project Type**: Python library with thin local CLI and stdio MCP interfaces,
plus a repository Agent Skill.

**Performance Goals**: Resolve one podcast episode, build at most one
coordinator-owned index/plan snapshot pair, and attempt at most one existing
stage runner per call. Unchanged confirmed 010-012 runners may perform their
established internal pre-execution refresh.

**Constraints**: Strict zero-file dry-run; confirmed requests reject `next`
and `latest`; exact action equality after fresh state recomputation; exact LLM
acknowledgement before any confirmed-summary read/config/provider work; bounded
metadata-only output; no fallback, retry, loop, batch, scheduler, cache rebuild,
or remote MCP; exact 13-tool registry.

**Scale/Scope**: One podcast, one episode, and zero or one action per invocation.
Corpus scanning remains bounded by the existing one-podcast 008/009 builders.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **I. Local Artifacts and Evidence Traceability — PASS**: State is derived
  from the approved feed and local artifacts; reports retain only bounded safe
  paths, states, counts, warnings, and execution outcome.
- **II. Thin Interfaces over Thick Core — PASS**: Selection, validation,
  dispatch, filtering, serialization, and report rendering live in
  `src/podcast_ingest_core`; CLI and MCP only map inputs and envelopes.
- **III. Dry-Run First Side Effects — PASS**: Dry-run exposes planned
  reads/writes, confirmation, blockers, and risks while writing zero files and
  calling zero executors/providers/loaders.
- **IV. LLM Opt-In and Secret Boundary — PASS**: Only confirmed
  `semantic_summary` may transfer transcript content; exact acknowledgement
  precedes feed/snapshot/profile/environment/provider/executor/writer work.
- **V. Evidence, Inference, and External Status Separation — PASS**: The runner
  reports artifact workflow state only and does not merge evidence classes or
  convert availability markers into market facts.
- **VI. No Investment Advice — PASS**: Results retain
  `not_investment_advice=true` and all unsafe advice/body text is excluded.
- **VII. No Live Market API Without Approval — PASS**: No market provider or
  live external-data feature is added.
- **VIII. Manual Cache Rebuild — PASS**: The runner never rebuilds SQLite cache
  and emits only bounded manual-refresh warnings after confirmed writes.
- **IX. TDD and Verification Gates — PASS**: Tasks require RED→GREEN targeted
  tests, safety/governance guards, full pytest, compileall, and diff hygiene.

No constitution amendment or complexity exception is required.

## Project Structure

### Documentation (this feature)

```text
specs/016-corpus-episode-completion-workflow-runner/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corpus-episode-completion-workflow.md
├── checklists/
│   ├── requirements.md
│   └── safety.md
└── tasks.md
```

### Source Code (repository root)

```text
src/podcast_ingest_core/
├── corpus_episode_completion_workflow_runner.py  # new coordinator and reports
├── corpus_episode_workflow_runner.py             # package-private snapshot preview seam
├── corpus_semantic_remediation_runner.py         # package-private snapshot preview seam
├── models.py                                     # additive 016 result models
├── storage.py                                    # additive latest report paths
├── errors.py                                     # additive dedicated error
├── mcp_server.py                                 # additive thirteenth thin tool
└── __init__.py                                   # additive public Core exports

scripts/
├── run_corpus_episode_completion_workflow.py     # new thin CLI
└── validate_mcp_setup.py                         # registry/setup validation update

.agents/skills/corpus-episode-completion/
└── SKILL.md                                      # portable human-control protocol

tests/
├── test_corpus_episode_completion_workflow_runner.py
├── test_corpus_episode_completion_skill.py
├── test_mcp_server.py
├── test_mcp_tool_registry_contract.py
├── test_mcp_setup_validation.py
├── test_contracts.py
├── test_llm_ack_guard_contracts.py
├── test_llm_cli_no_leak.py
├── test_cache_rebuild_guard.py
├── test_repository_secret_boundary.py
└── test_architecture_spec_docs.py

README.md
AGENTS.md
docs/
├── agent-handoff.md
├── architecture.md
├── codex-mcp-setup.md
├── mcp-usage.md
├── roadmap.md
└── verification-matrix.md
specs/README.md
```

**Structure Decision**: Follow the existing single-package runner pattern.
Create one focused 016 Core module and thin wrappers. Extract only the minimum
package-private preview seams from 014 and 015 so 016 can reuse one in-memory
snapshot; do not introduce a generic workflow framework or alter existing
public runner signatures.

## Phase 0: Research Decisions

See [research.md](research.md). All technical unknowns are resolved:

- Keep 016 as an additive coordinator instead of expanding 014 or 015 public
  contracts.
- Permit `latest` only for preview; require its returned canonical episode
  reference for confirmation.
- Resolve intake through the existing 013 dry-run path, then build exactly one
  008/009 snapshot pair for seeded episodes.
- Extract package-private snapshot preview seams from 014 and 015; 016 passes
  the same snapshot to both.
- Recompute the state before confirmed dispatch and reject drift without
  executing an alternate stage.
- Validate confirmed semantic-summary acknowledgement before every read,
  configuration, provider, progress, executor, or writer surface.
- Dispatch one existing public 013/012/011/010/015 runner exactly once and stop.
- Keep 016 latest reports metadata-only, confirmed-only, and atomic per file.
- Add one dedicated safe MCP wrapper and change only the exact registry count
  from 12 to 13.
- Add a client-neutral Agent Skill; validate Codex locally, while client-specific
  Hermes Agent/OpenClaw setup and live tests remain excluded.

## Phase 1: Design Summary

### State flow

1. Normalize podcast id, selector, action, confirmation, safe identifiers, and
   positive numeric options.
2. Reject confirmed `next`, confirmed `latest`, and invalid confirmed-summary
   acknowledgement before any read or write.
3. Call the existing 013 runner with `confirm=False` to resolve one canonical
   episode and classify an unseeded episode as `intake`.
4. For a seeded episode, build one private 008 snapshot and one private 009 plan
   snapshot from it.
5. Call the package-private 014 preview seam in strict semantic-handoff mode
   with the shared snapshot. After audio/transcription preview, reject any
   transcript state other than exact `valid`; select at most one deterministic
   remediation row; and ignore only semantic-family excluded/blocked rows after
   all non-semantic work is complete. Public 014 keeps its existing behavior.
6. Only after deterministic completion, call the package-private 015 preview
   seam with the same snapshot to select semantic summary, semantic review,
   completed, or blocked.
7. Dry-run returns one bounded result and performs no writer, provider,
   environment loader, executor, or progress callback.
8. Confirmed mode requires exact equality between the explicit request and
   fresh selection, then calls the matching existing public runner once.
9. Map the stage result or safe exception category into one outcome, write the
   latest 016 JSON/Markdown report, and stop without rescan, fallback, retry,
   cleanup, extra/post-stage index/plan refresh, or cache rebuild. Unchanged
   confirmed 010-012 runners retain their established pre-execution 008/009
   refresh.

### Public interfaces

The exact Core, CLI, MCP, Skill, report, and envelope contracts are defined in
[contracts/corpus-episode-completion-workflow.md](contracts/corpus-episode-completion-workflow.md).
All public additions are additive. Existing 013–015 APIs, CLIs, reports, and
standalone behavior remain unchanged.

### Data model

[data-model.md](data-model.md) defines request filters, one-row outcome,
aggregate counts, bounded warnings, public result, report paths, and state
transitions. No model field can carry transcript, semantic, prompt, provider,
endpoint, credential, feed URL, raw exception, traceback, or investment-advice
content.

### MCP and Skill boundary

The MCP tool mirrors bounded Core inputs, omits progress callbacks, never loads
`.env`, returns the established JSON envelopes, and converts only uncontained
016 command errors into a fixed safe error envelope. The portable Skill owns
the conversation sequence, but Core remains the enforcement boundary for
zero-file preview, explicit confirmation, acknowledgement, state equality,
single dispatch, and bounded output.

### Post-design Constitution Check

PASS. Phase 1 preserves all nine principles: thick Core, strict zero-file
preview, exact opt-in acknowledgement, safe evidence/status reporting, no live
market API, no investment advice, manual cache rebuild, and complete TDD/full
verification gates. No amendment or justified violation is required.

## Complexity Tracking

No constitution violations or complexity exceptions.
