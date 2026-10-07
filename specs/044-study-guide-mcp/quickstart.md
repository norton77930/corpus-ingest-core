# Quickstart: Implement and Verify 044 Offline

This guide validates the planned feature after implementation. It does not authorize real-provider or real-corpus operations. Start with [handoff.md](handoff.md), [plan.md](plan.md), [tasks.md](tasks.md) and the [contract](contracts/study-guide-mcp.md).

## Prerequisites

- Repository baseline `b42b5a2` or a reconciled successor; preserve the supplied uncommitted planning documents.
- Existing development environment with dependencies. On this workstation the correct interpreter is `.venv/Scripts/python.exe`, not PATH's neighboring-project interpreter.
- Set the feature explicitly in each shell. Keep `.specify/feature.json` ignored; do not create commits, branches or worktrees.
- No data-root environment override for pytest: use `tmp_data_dirs` fixtures, not real data. Never dump environment values or read `.env`.
- Keep the basetemp name short. This checkout's long absolute path plus a 64-character digest can exceed Windows path limits: the planning run with `044-planning-full` reached 262 characters and failed staging; `44r` reduced the same shape to 248 and the affected group reran without failures. Do not lengthen the full-suite scratch name below.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = "specs/044-study-guide-mcp"
.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

The prerequisites response must select 044 and include research, data-model, contracts, quickstart and tasks. It verifies structure, not feature completion.

## First RED: Preservation at the Public Core Seam

In `tests/test_study_guide_bundle.py`, use existing `_ready_episode`/`tmp_data_dirs` and fake provider fixtures to create an available lecture. Add `05/06`, a binary extra file, CRLF/BOM lecture bytes, then remove only the cover in the isolated fixture. Invoke the public `run_study_guide_bundle(confirm=True)` without ack. Assert all original non-cover bytes survive and the provider was never constructed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_study_guide_bundle.py -k cover_only_preserves -q --basetemp=.pytest-tmp/044-red
```

Record the assertion failure before changing runtime. A dependency/import error is not valid RED evidence. The code remains unmodified by this planning session; this test is to be written by the implementer.

## Focused Checks (after their tasks add the tests)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_study_guide_bundle.py tests/test_workflow_derivation.py tests/test_corpus_index.py tests/test_contracts.py -q --basetemp=.pytest-tmp/044-core
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_study_guide_bundle.py tests/test_mcp_workflow_derivation.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_server_facade_boundary.py tests/test_mcp_setup_validation.py tests/test_console_entry_points.py -q --basetemp=.pytest-tmp/044-mcp
.\.venv\Scripts\python.exe -m pytest tests/test_cache_rebuild_guard.py tests/test_llm_ack_guard_contracts.py tests/test_llm_provider_factory_boundary.py tests/test_llm_cli_no_leak.py tests/test_repository_secret_boundary.py tests/test_path_safety_boundary.py tests/test_path_safety_characterization.py tests/test_run_report_io_boundary.py -q --basetemp=.pytest-tmp/044-safety
.\.venv\Scripts\python.exe -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_docs_registry_count_consistency.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_020_verified_research_report_catalog_docs.py -q --basetemp=.pytest-tmp/044-docs
```

`test_mcp_study_guide_bundle.py` is planned, not present in the baseline. A focused test run proves only its slice. Do not run these suites concurrently or reuse another session's basetemp.

## End-to-end Synthetic Acceptance

| Scenario | How the test exercises it | Required result |
| --- | --- | --- |
| new lecture | real Core through tool, synthetic summary/identity, fake provider | preview zero mutation; confirm with exact existing ack creates four files/reports |
| reuse | same fixture with complete lecture and 05/06 | no ack/provider; lecture/derivation hashes unchanged; reports may change |
| cover-only | missing or safely invalid-UTF8 cover, other roles intact | only cover changes; non-cover bytes unchanged; no provider |
| protected regeneration | one/both derivation entries, force true | preview/confirm refuse before provider, writer or report |
| unsafe/recovery | links/reparse/nested entry or each recovery suffix | all modes refuse; destination/outside/recovery sentinels unchanged |
| failure phases | inject staging/publish/rollback/cleanup/report errors | correct fixed stage error; old recoverable or new complete, never false rollback |
| secrecy | fake exceptions with summary/prompt/credential markers | entire JSON response contains none of those markers |
| registry | facade and installed entrypoints | exactly 26; old 25 prefix and signatures intact |

Real native link tests may skip if platform privileges prevent setup; mocked reparse checks must still run. Report skip counts and reasons; skips are not passed native coverage.

## Full Checks / Completion Evidence

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp/44f
.\.venv\Scripts\python.exe -m compileall src scripts
git diff --check
git status --short
```

If this sandbox's ownership differs, use the invocation-local `git -c safe.directory=D:/SourceCode/CORP/FASBD/NewProd/GitHub/podcast-ingest-core ...`; do not change global config. Capture commands, return codes, counts, RED/GREEN evidence and limitations in `implementation-log.md` within this feature package. That file is created during implementation, not a pre-filled success record.

After code/standard reviews, run converge against spec/plan/tasks. Repeat checks only for intervening changes or unresolved failures. Do not mark tasks done based on a prior authoring session's test results. No real LLM, manual smoke, download, translation, index rebuild, publication or commit is required to accept this feature's offline contracts.
