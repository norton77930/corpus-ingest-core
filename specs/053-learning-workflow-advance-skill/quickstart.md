# Offline checks and manual use
Use repo .venv,owned temporary fixtures and fake providers only. No.env/provider/corpus setup.
```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/053-learning-workflow-advance-skill'
.\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest tests/test_learning_workflow_advance_skill.py tests/test_spec_053_learning_skill_docs.py -q
.\.venv\Scripts\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/53f --tb=short
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```
Agent host must mount Tool32 and load the portable Skill with its response-contract reference; manual host-specific loading only,no installation performed. Request one explicit podcast/episode learning step; inspect displayed plan;approve thiscycle and provide exactcosttext for generation. Skill confirms once,reports,stops. Test examples are offline oracles,not proof of host compliance. MissingTool32 stops withoutfallback;MCPcount remains32.
