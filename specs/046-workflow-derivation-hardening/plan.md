# Implementation Plan: Workflow Derivation Publication Hardening

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
**Status**: Implemented; see implementation-log.md for verification and limitations
**Branch**: existing working tree; no branch/worktree created

## Summary

Harden Tool 25 locally using the tested publication-state pattern from 044, without extracting a shared publisher or changing Tool 26. Keep business behavior in Core, and use a local fixed-error mapper in the thin MCP wrapper. The proposal deliberately changes recovery/error behavior, not successful schemas.

## Technical Context

**Language/Version**: existing Python >=3.11; Markdown Skill/docs.
**Dependencies**: stdlib plus existing PyYAML/pytest; no additions.
**Storage**: existing lecture directory, 05/06 pair, .wfderive staging/backup and existing run reports.
**Testing**: isolated tmp_data_dirs, fake providers, fault injection, byte snapshots, wrapper contracts.
**Platform**: Windows PowerShell development; POSIX/native-link and simulated Windows-reparse cases.
**Performance**: stream ordinary extra files in bounded chunks; no new latency SLA or artifact-size cap for preserved extras.
**Scale**: one explicitly named episode, externally serialized writers.
**Limits**: no durability/concurrent-writer guarantee; no artifact/report combined transaction.

## Constitution Check

Reviewed constitution 1.0.1: no amendment proposed. Pre/post-design gates pass in design, with the subsequent explicit implementation approval for the safety-related changes.

| Principle | Design evidence |
| --- | --- |
| I Local artifacts | Canonical metadata binds the existing lecture; reports retain identity/paths |
| II Thick Core | Path and publication state in workflow_derivation.py; MCP maps results/errors only |
| III Dry-run | Validation-only preview, no temporary files or provider |
| IV LLM/secret | Existing exact acknowledgement before provider; fixed MCP errors, no live eval |
| V Evidence | Distinct precommit/postcommit/unknown states; no false rollback claims |
| VI No advice | Existing generated-content guard unchanged |
| VII External boundary | No new provider or live market API |
| VIII Cache | Existing warning/manual rebuild unchanged |
| IX Verification | RED/GREEN by slice, fault injection, targeted/full checks, converge |

## Project Structure and Allowlist

Implementation may change:
- src/corpus_ingest_core/workflow_derivation.py
- src/corpus_ingest_core/errors.py (add derivation-specific types/constants only)
- src/corpus_ingest_core/mcp_tools_workflow_derivation.py
- tests/test_workflow_derivation.py, tests/test_mcp_workflow_derivation.py
- tests/test_workflow_derivation_safety.py (new focused test file)
- .agents/skills/workflow-derivation-bundle/SKILL.md
- tests/test_workflow_derivation_bundle_skill.py, tests/test_learning_workflow_skill_contracts.py, tests/fixtures/learning_workflow_skill_cases.json (only affected derivation cases)
- .agents/skills/README.md, docs/mcp-usage.md, docs/agent-handoff.md, docs/verification-matrix.md, specs/README.md and this package's progress/evidence files.

Do not modify study_guide_bundle.py, Tool 26, shared mcp_runtime.py, shared path/identity/report helpers, registry, models/signatures, CLI flags, dependencies, provider prompts/profiles, 044/045 historical records or real artifacts. Consult existing helpers through public contracts; do not import Tool 26 private functions. No new global filesystem framework.

## Phase 0 - Research

See [research.md](research.md). One read-only research agent compared present Tool 25 with 044 and mapped concrete fault seams. No tests/live operations were run by that role. Product choice remains this proposal; technical defaults are explicitly recorded rather than attributed to the user.

## Phase 1 - Design

### Validation and identity

At entry validate types/nonempty identifiers, whitespace, separators and latest/next before profile/context/source access using existing storage validators. Resolve canonical transcript paths, securely read Core-derived JSON with a 64 MiB cap, validate matching podcast/episode and nonempty title, then use canonical_semantic_summary_path_for_title. Do not call the current helper that directly reads transcript JSON. No stale-title glob fallback or title normalization beyond existing storage behavior.

Check managed roots and ancestors downward without following links. Use lstat and treat only FileNotFoundError as absent. Check canonical summary as a required regular file; its body is not a new derivation input. Check all direct bundle entries as regular files; reject nested directories/special files/reparse entries, including 05/06 under force. Require 00/03/04/07 as before, bounded UTF-8 at 2 MiB each. Core-derived lecture bytes may use secure_read_bytes. Context validation is described in the contract; arbitrary overrides cannot be passed to secure_read_bytes with a caller-selected root.

Recovery gate covers all four exact siblings before returning any preview/reuse and before provider construction. Recheck immediately before staging. Resolve default report paths and check existing ancestors/final files/.part targets as normal nonlinked paths; do not convert the report writer into a new recovery protocol. Existing ordinary report .part files retain the shared writer's overwrite behavior; this is separate from bundle recovery siblings.

### Pair publisher

Snapshot direct filenames after validation. Stage in exclusively created .wfderive.part; stream all non-pair files as bytes (e.g. 1 MiB chunks), then write validated generated 05/06. Track created_staging, moved and committed using successful operations, not later exists() guesses. Move live directory to this attempt's .wfderive.old, then stage to live. That second rename is the commit point. A brief absent-directory window remains.

On precommit failure restore this attempt's moved backup if possible. If rollback fails, retain both backup and staging and emit rollback_failed. Clean only positively identified attempt-owned normal staging; if cleanup cannot be proved safe retain it. After commit, cleanup only the backup created by this attempt; failures report published_cleanup_failed and never revert the new pair. No removal/restoration of pre-existing remnants.

### Errors and reports

Add WorkflowDerivationStateError as a subclass of WorkflowDerivationError with finite reason_code -> fixed message mapping. Preserve generic Core prerequisite/content errors where existing tests rely on diagnostics. Use typed states for new refusals and transaction failures. Map run-report errors according to whether artifacts were generated or reused at the existing _write_run_report catch, or catch its wrapped WorkflowDerivationError at the caller. An outer OSError-only catch is insufficient because _write_run_report already wraps OSError. Fault tests must fail the actual write_part_staged_report_pair path. Report writer protocol stays unchanged. See [contract](contracts/derivation-safety.md) for exact public strings and failure taxonomy.

Both MCP branches delegate once and catch through one module-local mapper. Keep tool_success and top-level warnings. Map unknown class names to InternalError, known base classes to fixed names. Never use str(exc), shared raw-error _tool_call, or exception-derived fields in the public response. No new response keys and no requires_llm/report_writes addition. Correct the existing unconditional LLM risk prose to conditional generation/reuse wording; roles remain cost authority.

### Skill and compatibility

Update derivation Skill P08/P10 only as needed: known fixed state messages can be recognized by type plus exact text; unknown results stay uncertain. Explain pre-existing recovery refusal versus attempt-local rollback/cleanup. Preserve consent and stop rules. Replace current doc legacy-limit claims with scoped guarantees; retain historical 045 logs unchanged. Adjust only affected derivation fixture cases. Lecture Skill remains untouched.

### Tests and independent slices

US1: refusal matrix + provider/report tripwires; US2: byte preservation and transaction failures; US3: exact public messages/no leak and updated instruction contracts. New regression file uses tmp_data_dirs and existing fixture helpers, never duplicate directory monkeypatch scaffolds. Preserve existing semantic/prompt guards and Tool 26 tests. Native symlink unavailable is a recorded skip, not a substitute for reparse/special/stat simulations.

## Phase 2 - Execution Handoff

Follow [tasks.md](tasks.md): preflight -> foundational contracts -> US1 -> US2 -> US3 -> docs -> targeted/full regression -> separate behavior/engineering review -> converge. One writer. Read-only review can proceed after a stable slice; no parallel writers. User subsequently authorized execution; see implementation-log.md for completion evidence.

## Complexity Tracking

No shared publisher extraction, report-protocol upgrade or concurrency lock. Such changes increase cross-tool scope and belong to a later proposal.
