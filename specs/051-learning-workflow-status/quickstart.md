# Offline verification
Use repo .venv and temporary fixtures; no real provider/.env/corpus/cache setup.
```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/051-learning-workflow-status'
.\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest -q tests/test_learning_workflow_status.py tests/test_mcp_learning_workflow_status.py
.\.venv\Scripts\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/51f
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```
Full Git guards may require process-local safe.directory; do not persist config changes. Query example:inspect_learning_workflow_status(podcast_id='x-raytar',episode_ref='2071290493581840707'). It reads diagnostic metadata only; preview/approval execution remains through existing tools/Skills. Restart an already running MCP process manually to expose appended Tool31. No restart/deployment performed in this phase.
