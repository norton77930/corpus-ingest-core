# Offline verification and client flow
Use repo .venv and owned temporary fixture providers only. No real episode/provider setup.
```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/052-learning-workflow-advance'
.\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest tests/test_learning_workflow_advance.py tests/test_mcp_learning_workflow_advance.py -q
.\.venv\Scripts\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/52f
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```
Preview Tool32 with explicit IDs and confirm=false. Show action,requires_llm/ack,artifact+metadata+report writes and warnings to operator. After explicit approval return exact next_action and plan_id as expected_action/expected_plan_id with confirm=true; generation requires existing exact cost acknowledgement. Execute once,report,stop. Drift/failure requires new human-reviewed preview; no automatic retry. Complete means existing previews reusable; blocked/stale/legacy/custom requires manual review. Restart existing MCP manually to expose32; no restart/deployment performed here. Full Git-ignore tests may require process-local safe.directory,never persisted config.
