# Offline validation
Use repo .venv on Windows, no .env or real provider setup. Tests use tmp_data_dirs and fake providers.
```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/049-study-guide-lineage'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest -q tests/test_study_guide_lineage.py tests/test_mcp_study_guide_lineage.py tests/test_study_guide_bundle_skill.py
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```
Expected fixture outcomes: generation->current; summary mutation->stale; old complete lecture->untracked; reuse/cover-only no metadata writes; malformed reserved receipt generation refusal. On this machine native symlink cases may skip; synthetic reparse/subdirectory cases still execute. Restart long-running MCP manually after implementation to load appended Tool29; no deployment is part of validation.
