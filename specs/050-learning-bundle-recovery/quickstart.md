# Offline validation
Use existing repo .venv and tmp_data_dirs fixtures; no provider/.env setup.
```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/050-learning-bundle-recovery'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest -q tests/test_learning_bundle_recovery.py tests/test_mcp_learning_bundle_recovery.py
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```
Expect clear for empty/no remnants, recovery_present plus manual_review_required for any safe sibling, blocked for unsafe/unreadable or partial public state. Valid matching receipt is a byte consistency observation only. Native symlink tests may skip where unavailable; synthetic reparse refusal must execute. Existing MCP process may need manual restart to load appended Tool30; no restart/deployment is part of this phase.
