# Validation Guide: 047

Status: implemented and offline-verified; see implementation-log.md for current full regression evidence. Do not run live artifact operations to validate this plan. Use the repository venv and tmp_data_dirs; never read .env or call real providers. Existing dirty 044-046 work is protected. No branch/worktree/commit/deployment is authorized by planning.

## Implementation validation

Set `$env:SPECIFY_FEATURE_DIRECTORY="specs/047-learning-workflow-next-step"`, run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`, and follow tasks.md using one writer.

Focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_learning_workflow_next_step.py tests/test_mcp_learning_workflow_next_step.py --basetemp=.pytest-tmp/47a
```

Fixtures must demonstrate contract C01-C12: four normal decisions; generic and typed blockers; false modes/identity/plan combinations; private sentinel errors; zero tree-byte changes and zero forbidden calls. Native symlink skips must be named separately from simulated reparse/stat refusal checks. Use fixture trees, not repository artifacts.

Regression: existing study-guide/derivation Core/MCP/safety suites, both 045 Skill suites and shared learning oracle, registry/facade/setup/console tests, cache/secret/ack boundaries and docs tests. Fresh basetemp for each run; keep Windows paths short.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp/47f -rs --tb=short
.\.venv\Scripts\python.exe -m compileall -q src scripts
git -c safe.directory=D:/SourceCode/CORP/FASBD/NewProd/GitHub/podcast-ingest-core diff --check
```

If Git ownership affects policy tests, supply only process-scoped safe.directory as used in 046; do not alter global configuration. Record baseline versus new failures, skip reasons and exact commands. Run Spec Kit converge against current code; only mark tasks complete with current evidence.

## Planning-only checks

`tests/test_spec_047_learning_next_step_docs.py` locks proposal status, read-only/freshness boundaries, design files and requirement/task coverage. The initial docs/registry tests confirmed the planning baseline of26 tools. The user subsequently authorized implementation; current runtime regression results are recorded in implementation-log.md.
