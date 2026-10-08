# Validation guide

Use synthetic fixtures only; no download, provider, .env or host settings required.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/059-source-learning-reliability'
.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest tests/test_source_learning_reliability.py tests/test_spec_059_source_learning_docs.py tests/test_source_content_query.py tests/test_mcp_source_content_query.py tests/test_source_content_qa_skill.py tests/test_source_learning_entry_skill.py tests/test_learning_mcp_acceptance.py tests/test_mcp_study_guide_bundle.py -q -rs
.\.venv\Scripts\python.exe -m pytest -rs
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```

Expect malformed cursor/version to recover once at unread position; second error/source drift/unsafe reply stops partial; preparation/side-effect tools never retry. Inspect extra-argument message names only accepted IDs; version/cursor format and binding have safe diagnoses. Over60000 synthetic characters fit defaults; lower explicit budgets still stop. Native/POSIX paths detect planned LLM writes.

## Actual Hermes acceptance (separate, pending)

Install complete source-learning-entry, source-preparation and source-content-qa folders including references; expose their discovery metadata and mount existing local learning tools. No host configuration is shipped.

In a fresh conversation without preloading Skill body, give one supported prepared URL and request notes. Verify Skill loaded and local preview/query precede third-party transcript retrieval. Blocked/unavailable preparation explains why and asks user choice. Observe sequential exact cursor/version copying and cumulative budgets. If a controlled host test can inject a parameter mistake, verify one recovery and second-error partial stop; do not weaken the server to induce it.

Review notes against original source: neutral unidentified speaker, concrete key metaphor with reasoning, no unsolicited audience/project section, separately labeled AI additions. Pytest/read-only pressure agents do not prove Hermes compliance. Never commit actual source/host settings/session traces.

## Long-source verifier

SPEC059 default --max-total-chars120000; --max-calls20 and --timeout60 remain separate bounds. For longer sources select explicit bounded options/time range using [SPEC058 guide](../058-learning-mcp-acceptance/quickstart.md). Budget exhaustion stays partial; verifier does not retry.