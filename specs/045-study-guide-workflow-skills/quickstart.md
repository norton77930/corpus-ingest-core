# Quickstart: Implement and Validate 045 Offline

## Prerequisites

Use the current working tree containing the reviewed 044 implementation. Do not discard its uncommitted changes. The repository `.venv` must already work; PATH python may point at another repository. No .env read, live provider, download, transcription, real source-body inspection, cache rebuild or Skill installation is needed.

Select the package explicitly:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/045-study-guide-workflow-skills"
.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

The ignored feature.json is local selection metadata, not a repository-wide feature pin.

## Development order

Follow [tasks.md](tasks.md). Show focused RED for missing instruction clauses before adding the Skills, then GREEN. Use existing tmp_data_dirs fixtures for any Core characterization. Use the [protocol](contracts/skill-protocol.md) as the single planning reference for P01-P10 and C01-C20.

## Targeted verification after implementation

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_study_guide_bundle_skill.py tests/test_workflow_derivation_bundle_skill.py tests/test_learning_workflow_skill_contracts.py tests/test_youtube_video_ingest_skill.py tests/test_x_video_ingest_skill.py tests/test_mcp_study_guide_bundle.py tests/test_mcp_workflow_derivation.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_server_facade_boundary.py tests/test_mcp_setup_validation.py --basetemp=.pytest-tmp/45i -rs
.\.venv\Scripts\python.exe -m pytest -q tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py tests/test_ai_governance_docs.py tests/test_docs_registry_count_consistency.py tests/test_llm_ack_guard_contracts.py tests/test_repository_secret_boundary.py --basetemp=.pytest-tmp/45d -rs
```

The three test files were absent at the original planning handoff and now exist. Current implementation results are recorded in implementation-log.md; do not reuse historical planning counts. Choose a different short basetemp if one above already holds evidence; preserve earlier scratch.

## Standard verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp/45f -rs
.\.venv\Scripts\python.exe -m compileall -q src scripts
git -c safe.directory=D:/SourceCode/CORP/FASBD/NewProd/GitHub/podcast-ingest-core diff --check
```

Avoid long basetemp names on Windows. Report skips and reasons separately. Full tests are offline fixtures; do not infer live Skills work from their count. Do not change global Git configuration for ownership warnings.

## Acceptance review

- Walk through all C01-C20 with both Skill texts, recording expected tool names/arguments and stop points.
- Check actual preview shapes for generation/reuse/cover-only and reuse report effects against existing wrappers.
- Review requested behavior separately from AGENTS/constitution boundaries.
- Inspect the final diff: no production Python, registry/signature/dependency changes or historical artifact edits.
- Run converge after implementation, append real remaining tasks, then rerun relevant checks if fixes changed anything.
- An actual host dialogue evaluation is optional, unperformed and not authorized by this plan. Do not substitute a mock agent for this evidence.
