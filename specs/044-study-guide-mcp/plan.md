# Implementation Plan: Safe Study-guide MCP Access

**Branch**: existing `main`; no branch created | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Input**: `specs/044-study-guide-mcp/spec.md` | **Baseline**: `b42b5a2`
**Status**: Development design; implementation tasks remain unchecked.

## Summary

Deliver one append-only MCP tool over Spec 038's existing study-guide runner. First protect the shared directory: preserve non-owned bytes, refuse upstream generation when derivations exist, reject unsafe paths/recovery remnants, and report publication failures honestly. Then expose preview/confirm with metadata-only errors. No other tool behavior, result schema, provider boundary or artifact family changes.

## Technical Context

**Language/Version**: Python >=3.11; PowerShell for repo tooling.
**Primary Dependencies**: existing `mcp[cli]>=1.27,<2`, standard library and current Core modules; no dependency changes.
**Storage**: existing study-guide directory and JSON/Markdown run reports; no schema migration or SQLite work.
**Testing**: pytest, `tmp_data_dirs`, fake provider, no-network/no-env sentinels, byte snapshots and injected filesystem failures.
**Target Platform**: Windows and Linux; native link tests where available plus portable mocked reparse tests.
**Project Type**: Python Core library with thin CLI/MCP adapters.
**Performance Goals**: one episode per call; preservation I/O proportional to the selected directory; no corpus-wide scan beyond existing canonical identity selection. No new latency SLA or benchmark suite.
**Constraints**: preview writes/network/provider calls = 0; exact ack before generation; serialized callers; no real corpus/provider operations in verification. Keep existing 64 MiB identity and 2 MiB summary/readability caps.
**Scale/Scope**: one new tool, one Core preservation seam, one typed error; no model/config changes. Safe directory enumeration reuses the existing 4,096-entry maximum and fails closed if exceeded.

## Constitution Check

| Principle | Before research | Post-design mechanism |
| --- | --- | --- |
| I — artifacts/evidence | Pass | Preserve bytes and identity; existing timestamps/validation stay; no currentness claim |
| II — thin interfaces | Pass | Selection, preservation, metadata projection and failure classification in Core; wrapper formats/delegates |
| III — dry-run first | Pass | Same preflight; no preview recovery, mkdir, report, provider or network |
| IV — opt-in/secrets | Pass | Core exact ack for generation only; fixed MCP errors; no `.env` or transcript text in new provider input |
| V — evidence separation | Pass | Lecture and derivation remain separate; no invented lineage |
| VI — no investment advice | Pass | Existing output validation/notices retained; no prompt edits |
| VII — no live market API | Pass | No new API/provider path |
| VIII — manual cache | Pass | Existing warnings forwarded; no index/cache rebuild |
| IX — TDD/verification | Pass | Per-slice RED/GREEN, safety/regression/full checks, docs consistency and two review axes |

No constitution amendment/exception. The reviewed registry intentionally changes from 25 to 26 during implementation; baseline remains 25 throughout this planning turn.

## Project Structure

### Documentation (this feature)

`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/study-guide-mcp.md`, `quickstart.md`, `tasks.md`, `checklists/requirements.md`, `checklists/safety-contract.md`, `handoff.md`, `workflow-record.md`, and initial `repo-assessment.md` live under `specs/044-study-guide-mcp/`.

### Source Code (repository root)

| File | Planned responsibility |
| --- | --- |
| `src/corpus_ingest_core/study_guide_bundle.py` | Local secure identity/source adapter, preflight, byte preservation, stage errors, pure plan projector |
| `src/corpus_ingest_core/errors.py` | New `StudyGuideBundleStateError(StudyGuideBundleError)` with finite reason codes |
| `src/corpus_ingest_core/mcp_tools_study_guide.py` | New thin tool and fixed error mapping |
| `src/corpus_ingest_core/mcp_server.py` | Append group import/re-export; preserve import-order fence |
| `scripts/validate_mcp_setup.py` | Registry count/name validation |
| `tests/test_study_guide_bundle.py` | Public Core preservation, branches, source safety, failure tests |
| `tests/test_mcp_study_guide_bundle.py` | New wrapper tests and real-Core seam tests |

**Structure Decision**: Extend existing modules, not a new storage system. Keep `models.py`, `storage.py`, CLI signatures, shared canonical/path-safety/snapshot helpers, `mcp_runtime.py`, workflow_derivation and existing result/report schemas unchanged. Reuse helpers through existing interfaces. Do not duplicate `tmp_data_dirs`.

## Phase 0 — Research Outcomes

See [research.md](research.md), R1–R8. Two read-only research roles inspected publication/recovery and MCP contracts; the main writer reconciled findings. Technical decisions needed for task generation are resolved. No product preference question is pending.

## Phase 1 — Design

### Core entry and planning

1. Validate explicit identity before profile/filesystem access. Use `storage.is_safe_episode_ref` and existing pure storage path construction for slug validation. Reject case-insensitive reserved `latest`/`next`, without stripping or fallback. No new regex.
2. Load profile and enforce learning-notes. A private local adapter reuses canonical transcript path selection, securely snapshots/validates selected JSON's podcast/episode/title, then calls `canonical_semantic_summary_path_for_title`. Preserve ambiguity rejection; no title glob fallback. Identity JSON is local-only and never provider input.
3. Compute source/bundle paths. Before summary/owned body reads, validate lexical containment and no-follow filesystem metadata (including root ancestors), all four recovery sibling names and immediate bundle entries. Missing normal output directories can be planned without creation. Links/reparse points, nested directories, special files and unsafe sources fail closed. No resolve-then-trust shortcut.
4. Read source summary securely with its existing size cap; keep content validation. Determine owned-file readability after metadata checks. Keep complete/cover-only/partial behavior; cover-only includes safe regular `00` failing the UTF-8 readability check. A filesystem/permission error is a refusal, not deletion authority.
5. If the action generates `03/04/07`, any derivation entry blocks before provider/report/writer, regardless of force. Existing result keys remain. Add the selected transcript JSON to `planned_reads` as an identity dependency; this list is not a syscall audit. Any optional seed read for the cover must be safe/no-follow; audio inspection stays metadata-only.
6. Preview returns the existing result. Add pure `describe_study_guide_plan(result)`: `requires_llm` is the intersection of full `planned_writes` paths with canonical `03/04/07` paths; `report_writes` comes from the existing storage helper. No model field or public runner signature change.

### Publication and preservation

- Callers serialize both lecture and derivation writers. Recheck relevant metadata/remnants before staging; do not claim adversarial race or cross-process safety.
- Reuse never invokes the publisher, preserves all bytes and still writes a run report on confirm.
- Cover-only stages only a new `00` over byte copies of safe existing files. Allowed generation overlays only four owned files. Preserve extra regular binary files with streaming copy; do not decode/re-encode reuses or load a whole directory into memory.
- Validate every entry before provider/staging; reject links/reparse points, directories and special files rather than following/skipping them. Recheck before reading preserved files. Reuse existing no-follow/stat patterns; do not change shared safety helpers.
- Keep the existing directory-swap mechanism. Successful staging→destination rename commits. Pre-commit failure restores old bytes if rollback works; rollback failure retains recoverable old/staging. Post-commit cleanup failure retains the complete new destination. Cleanup only this invocation's known safe staging/backup, never pre-existing remnants.
- Existing `write_part_staged_report_pair` runs after publication or reuse. Its weak two-file protocol remains: report failure may leave one report changed. Do not roll back the bundle or claim one transaction. Distinguish report failure after publication from report failure after reuse.

### New-tool contract and safe failures

See [contracts/study-guide-mcp.md](contracts/study-guide-mcp.md). Preview formats one Core result plus its pure projector. Confirm calls Core once without a preceding internal preview. Core keeps conditional ack semantics.

New state/publication failures raise `StudyGuideBundleStateError` with a known reason. The wrapper maps reason/base type to literal messages and a fixed error type. Never append exception text, provider body, arbitrary values or traceback. Shared `_tool_call` is unsuitable for this new error boundary; reuse `tool_success` / `tool_error` directly. Unknown codes/types use a generic fixed response. No change to Tool 1–25 handlers.

### Registry and documentation inventory

Update live pins together during implementation, not now:

- Runtime: `mcp_server.py`, `scripts/validate_mcp_setup.py`.
- Tests: `test_mcp_tool_registry_contract.py`, `test_mcp_setup_validation.py`, `test_console_entry_points.py`, `test_mcp_workflow_derivation.py`, `test_ai_governance_docs.py`, `test_architecture_spec_docs.py`, `test_spec_020_verified_research_report_catalog_docs.py`; facade-test comment only if necessary. Tool25 must be pinned at index 24, not the last index.
- Docs: `docs/agent-handoff.md`, `docs/ai-development-framework.md`, `docs/api.md`, `docs/architecture.md`, `docs/claude-mcp-setup.md`, `docs/codex-mcp-setup.md`, `docs/install-and-porting.md`, `docs/mcp-readiness.md`, `docs/mcp-usage.md`, `docs/usage.md`, `docs/roadmap.md`, `docs/verification-matrix.md`, `specs/README.md`.
- `pyproject.toml`: descriptive registry comments only if needed; no dependency/entrypoint change. No new README tool lists; canonical lists stay in docs/api.
- Preserve historical package counts; do not weaken the dynamic docs-count checker.

### Validation and delivery sequence

US3 safety/preservation → US1 preview → US2 confirm → integration/docs → full verification, review and converge. All three P1 stories are required; preview-only is not the MVP. Every behavior slice records focused RED before GREEN, then regression. See [quickstart.md](quickstart.md).

## Agent Context Update

Update only the SPECKIT-marked plan link in `AGENTS.md` to 044, retaining explicit feature selection and no-global-pin wording. No update-agent-context script exists in the installed script directory, so follow the skill's marker-update instruction directly. Do not alter engineering rules.

## Complexity Tracking

No constitution violation, dependency, broad refactor, runtime subsystem or data migration. The typed error and pure plan projector are the only new support interfaces. Further lineage/recovery/concurrency work requires separate scope.
