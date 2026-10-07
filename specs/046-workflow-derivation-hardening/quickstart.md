# Quickstart: Validate 046

Implementation requires approval of this proposed safety/error scope. Use the existing dirty working tree; preserve 044/045. One writer, repo .venv, offline fixtures only. No .env read, real provider, raw corpus inspection, artifact cleanup, branch, commit or deployment.

## Select package

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/046-workflow-derivation-hardening"
.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

## Baseline and targeted checks

Before creating the new safety test file, omit it from baseline. Choose unique short basetemp values; preserve old scratch.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_workflow_derivation.py tests/test_workflow_derivation_profiles.py tests/test_mcp_workflow_derivation.py tests/test_workflow_derivation_safety.py tests/test_workflow_derivation_bundle_skill.py tests/test_learning_workflow_skill_contracts.py --basetemp=.pytest-tmp/46i -rs
.\.venv\Scripts\python.exe -m pytest -q tests/test_study_guide_bundle.py tests/test_mcp_study_guide_bundle.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_server_facade_boundary.py tests/test_mcp_setup_validation.py tests/test_run_report_io_boundary.py tests/test_path_safety_boundary.py tests/test_llm_ack_guard_contracts.py tests/test_cache_rebuild_guard.py tests/test_repository_secret_boundary.py tests/test_docs_registry_count_consistency.py --basetemp=.pytest-tmp/46g -rs
```

Demonstrate focused RED -> minimal change -> GREEN per tasks, including actual byte comparisons and provider/report tripwires. Test C01-C18 from the contract. Keep existing semantic constraints and original rollback byte assertions when updating the deliberate exception contract.

## Full checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp/46f -rs
.\.venv\Scripts\python.exe -m compileall -q src scripts
git -c safe.directory=D:/SourceCode/CORP/FASBD/NewProd/GitHub/podcast-ingest-core diff --check
```

If ownership warnings prevent Git-based tests, append safe.directory using process-only GIT_CONFIG_COUNT/KEY/VALUE for this repository and rerun affected tests; never change persistent config. Report symlink skips separately. Do not claim fixture verification is live provider/agent verification.

## Review and converge

Review requirements and engineering constraints separately. Require fault evidence for every commit/rollback/report state and the fixed MCP error map. Inspect only approved changes against the captured starting tree, not against a clean-tree assumption. Run speckit-converge after implementation; append only real remaining tasks. Record results in implementation-log.md when implementation begins; current planning evidence belongs in workflow-record.md.
