# SPEC056 implementation evidence

Implementation, full verification and requirement/code convergence are complete in the working tree. The earlier entries below preserve failed/intermediate evidence; the final closeout is authoritative. No branch, commit, deployment, installation, cache rebuild or provider/media run was performed for056.

## Delivered behavior / boundaries

One appended Tool35 query_source_content delegates to offline Core: inspect metadata, version-pinned bounded read, literal keyword search and optional overlap time range. Prepared RSS/YouTube/X identity only; not all video platforms. No SQLite prerequisite, URL resolver, provider, network, preparation, side-effect chain or formal lecture publisher. Old34 slots/signatures preserved by registry/SDK guards. Source-content-qa portable Skill supplies timed answers, same-version complete/partial notes, language limits, hostile-content handling and host budget/privacy/billing disclosure.

Constitution1.0.1 unchanged: repository provider api_cost_ack gates remain. New reader follows existing user-requested MCP evidence delivery; host AI processing can expose content and incur cost under Hermes settings. Missing old actual model metadata stays null. Structural validation does not verify ASR accuracy. File checks are fail-closed snapshots, not an OS-atomic filesystem transaction or a promise against arbitrary continuous concurrent mutation; repository writer serialization still applies.

## Changed paths for056 (other dirty044-055 work preserved)

- Core: src/corpus_ingest_core/source_content_query.py; opt-in require_single_link/content stability and pre-read pathname guards in secure_local_snapshot.py.
- MCP: src/corpus_ingest_core/mcp_tools_source_content.py; append import/export in mcp_server.py.
- Tests: test_source_content_query.py, test_mcp_source_content_query.py, test_source_content_qa_skill.py, test_spec_056_source_content_docs.py, fixtures/source_content_qa_dialogues.json; registry/facade/setup/console/preparation transport/governance count guards.
- Skill: .agents/skills/source-content-qa/SKILL.md, references/response-contract.md, .agents/skills/README.md.
- Setup/docs: scripts/validate_mcp_setup.py, pyproject.toml comments, AGENTS.md SpecKit marker, README.md/README.zh-TW.md, docs/{api,mcp-usage,agent-handoff,ai-development-framework,architecture,claude-mcp-setup,codex-mcp-setup,install-and-porting,mcp-readiness,roadmap,verification-matrix}.md, specs/README.md and this056 package.
- Owned ignored evidence: .pytest-tmp/56p/pilot-{report.md,result.json},56-full-pytest.log; staged Skill/delivery helpers remain ignored and must not be rerun (delivery appends docs).

## Spec Kit workflow

Constitution reviewed without amendment; specify14FR/5SC and3user stories; clarify resolved by approved scope/local evidence; plan/research/data model/MCP+Skill contracts/quickstart created. Requirement-quality checklists6/6 and7/7 completed (quality gates, not runtime claims). Tasks14 dependency-ordered, sole root writer. Analyze checked all19requirement mappings with no blocking inconsistency. Official setup-plan/check-prerequisites selected SPECIFY_FEATURE_DIRECTORY=specs/056-source-content-query; no branch script executed. Implement used focused RED/GREEN. Converge pending final verification. No extensions.yml hooks present.

## Focused evidence

| Slice | RED | GREEN / evidence |
|---|---|---|
| Design package |2missing package/contracts failures56dr|2pass56dg|
| Offline Core |42missing reader/guard failures56cr|Core+snapshot50pass3native-symlink skips56cg2|
| Windows stat semantics |17valid-file refusals56cg|Path ctime and handle ctime differ on Python3.11/Windows; compare mtime across APIs, ctime within same API;50pass3skip56cg2|
| MCP |15missing facade failures56mr|15pass including actual stdio SDK56mg|
| Skill/current docs |6missing/stale failures14pass56sr|Staged Skill/ref/oracles and current35-tool claims; covered by141pass3skip56t2|
| Huge integer request/timestamp |2OverflowError failures56nr|finite invalid_request/source_invalid, aggregate69pass3skip56rg|
| Cursor exact integer window |1accepted changed scope56br|preserve exact numeric binding;69pass3skip56rg|
| Parent redirect before bytes |1descriptor read before refusal56pr|opt-in parent check before bytes;69pass3skip56rg|
| Leaf substitution before bytes |1descriptor read before refusal56lr|opt-in lstat regular/reparse/identity/nlink/stamp recheck before bytes;141pass3skip56t2|
| Hostile evidence/budget guidance |1missing distinction56sbr|explicit safe-evidence handling and host/user remaining budgets;141pass3skip56t2|

Latest targeted command used repo venv pytest -q with source-content Core/MCP/Skill/docs, secure snapshots, registry/facade/setup/console/count/governance/constitution/status guards, --basetemp=.pytest-tmp/56t2 --tb=short: **141 passed,3 skipped**, exit0,56.43s. Three skips are existing native symlink creation OSError; simulated reparse, hardlinks, parent/leaf substitution, content mutation, caps and cursor cases ran.

Optional `python -m ruff check` on new files could not run because ruff is not installed in repo venv. No dependency install performed; this is not substituted with a claim of lint success.

## Owned actual MCP SDK medium X pilot

Executed .venv/Scripts/python.exe .pytest-tmp/pilot_056.py with existing .pytest-tmp/54m/data only, exit0. Source x-natewiki/2106893534980685927, JSON SHA256 ddfc97d0ada4c1b90bd3f327f98293eac9a75961b96d7921700af40e266026af. Actual stdio SDK advertised35tools; Tool35 reconstructed **1088segments/60834characters exactly in14pages**. Range17:30-20:30 returned46timed segments; literal verification search17matches across1088segments. All existing data file hashes preserved; no SQLite existed or was created. No download, ASR, provider or Hermes model execution. ASR accuracy itself not reassessed.

## Fresh independent review

research_056_contract: repository-only research, no writes/tests/network. review_056_behavior: three concrete numerical/parent-check issues, root added RED and fixed, recheck no remaining material Core/MCP issue. review_056_engineering: leaf substitution gap, root added RED and fixed; final recheck found no remaining material conformance gaps. pressure_056_skill: eight synthetic reasoning cases, baseline had no violations (no claimed RED agent failure/improvement); two documentation ambiguities fixed after focused static RED, recheck confirmed both addressed; two minor wording corrections were applied and documented/static tests rechecked. All other roles stayed read-only; root sole writer. Synthetic decisions and SDK transport are not actual Hermes host acceptance.

## Acceptance mapping

| Intent | Executable evidence |
|---|---|
|FR-001/002/003;SC-001/002;US1|prepared RSS/YouTube/X no-index reads, metadata/IDs/original ordinal and segment_id; range/extent tests|
|FR-004;US2|literal casefold search, zero Chinese hits over English scope and explicit non-semantic metadata|
|FR-005/006/007;SC-002/003;US2/US3|exact long-text reconstruction/offsets, version change, cursor scope/position, limits, final-page complete=false|
|FR-008/009;SC-003|hardlinks before body, mocked reparse/nonregular/parent/leaf race, mutation, malformed/empty/partial/ambiguous/recovery/legacy cases|
|FR-010/013;SC-001|no network/SQLite/provider/cache/media monkeypatch sentinels and byte preservation; host cost/privacy/no advice Skill/docs|
|FR-011;SC-004|append-only35-tool registry/facade/schema/setup/console/actual stdio SDK and first34slot guards|
|FR-012/013;SC-005;US3|Skill/ref static checks,11labelled dialogue oracles, backend coverage examples, synthetic pressure rechecks|
|FR-014;SC-001/002/003|actual medium X SDK pilot, exact reconstruction/all hashes preserved/no cache|

## Remaining operational limits

Actual mounted Hermes model/Skill acceptance was not executed; operator must mount/reload updated MCP and Skill in its own host. No settings/credentials were read to discover or change that host. New tool does not prepare arbitrary videos or generate formal study-guide documents. Optional ruff unavailable as above. Full pytest/compileall/diff and final converge results will be recorded in closeout below.
## Final verification continuation

First full run56f exposed stale architecture/history and older MCP count guards and was interrupted after focused diagnosis; it is not a passed full-suite result. Restored the preserved historical019plan reference in AGENTS SpecKit marker and updated only current count assertions34->35 while retaining original tool-index/schema assertions. Focused architecture/history RED4+1failures ->22passed56ag; five legacy registry/slot RED failures ->5passed85deselected56gg. Closing docs/Skill/governance37passed56dg2,3.77s. Final whole suite now runs independently with --basetemp=.pytest-tmp/56g, log56-full-pytest-2.log.

Compileall -q src scripts exit0. git diff --check exit0 (line-ending normalization warnings across existing dirty files). Python3.11/Windows stopped owned failed pytest using verified exact56f basetemp process IDs; initial Stop-Process raised NullReferenceException, the .NET termination ended it. No other process/caches/source artifacts were targeted.

Protected .agents directory initially refused sandbox writes. Skill/reference/registry were staged under owned scratch, then copied with approved scoped escalation. No automatic approval-review rejection occurred; no plugin/provider settings changed. Subsequent focused guidance corrections copied only the same two Skill files.

Second complete run56g:1failed,2849passed,26skipped,821.41s,exit1. The sole failure was preserved historical054plan link absent from AGENTS marker; no runtime failure occurred. Restored054/055historical references, retaining explicit056selection; focused docs/governance30passed56srg,0.49s. Final complete run56h now verifies corrected state; do not count the56gresult as a passing full suite.

## Final closeout (2026-10-07)

**Full suite:2850passed,26skipped,exit0,834.41s(13:54)**. Command: .venv/Scripts/python.exe -m pytest -q -rs --basetemp=.pytest-tmp/56h --tb=short; process-only exact-repo safe.directory configured for git guards. Authoritative output: .pytest-tmp/56-full-pytest-final.log. Earlier56f/56g failures remain historical evidence only. All26skips are native symlink creation OSError (snapshot3;study-guide10;verified catalog3;source revalidation1;derivation safety9). Simulated reparse, hardlinks, handle/parent/leaf races, mutation/cursor/bounds and SDK cases ran.

Converge intent audit:14FR+5SC+3user stories, Core/MCP/Skill/design/doc touch-points and constitution boundaries all satisfied by present code and the evidence table; fresh behavior and engineering rechecks found no material gaps. **0 findings,0 appended tasks**; no empty convergence phase. T001-T014 complete. Official selected-package prerequisites and task-file stability check accompany closeout. Source bodies/metadata, host inference and external verification remain distinct. No live Hermes/provider integration claimed.

Current verification: full suite above; targeted141passed3skipped56t2; follow-up registry5passed56gg; docs/Skill/governance37passed56dg2 and historical-source-reference30passed56srg. Source/SDK pilot14pages1088segments exact equality and all data hashes preserved. compileall src scripts and diff-check already exit0; repeated closing commands and document-only status checks are recorded below.

Runtime/code did not change during the last full-suite run. Closing edits only synchronize evidence/status/tasks. No branch/commit/worktree/deployment or automatic installation/cache rebuild/provider/ASR occurred. Repo venv lacks optional ruff; no lint success claimed. Actual mounted Hermes acceptance remains operator work, distinct from tested SDK and synthetic Skill evidence.

Closing status/contracts/governance verification:37passed,exit0,5.92s(--basetemp=.pytest-tmp/56dclose). Repeated compileall -q src scripts exit0; repeated git diff --check exit0. Official prerequisites returned056 package; non-destructive Converge task SHA remained unchanged during audit. Final runtime tests2850passed26native-symlink skips,0failures; all14tasks complete.

## User-approved learning-note format follow-up (2026-10-07)

Scope: existing FR-012/US3 presentation guidance only, following the user's feedback that one-line topic summaries were insufficient and project application obscured learning from the source. Update the portable source-content-qa Skill, add references/learning-notes-template.md, synchronize contracts/skill.md and quickstart.md, and add one reference-discovery/portability guard to test_source_content_qa_skill.py. Core, MCP signatures/tool count, source data, provider gates and original T001-T014 are unchanged. This bounded docs/test refinement follows ADR-0006 rather than creating a new runtime feature package.

The editable default explains each actual issue, speaker reasoning and source examples, with labelled AI terminology explanations or invented examples. Project application is omitted by default and added separately only when requested. Current user preferences override the layout; a saved template edit changes future defaults after reload/synchronization, not existing notes. The full-source coverage rules remain independent of output formatting. Protected Skill files were updated using a scoped approved escalation; no installation, host settings change, provider/media execution or commit occurred.

RED: the new reference guard failed with `Learning-notes template route missing`; the direct file check also confirmed the template did not exist. User-observed prior output supplied the actual quality failure. A read-only baseline agent already produced an acceptable beginner explanation for the explicitly scoped supplied passage, so no measured baseline-to-forward quality improvement is claimed.

Forward check: a separate read-only agent read the updated Skill/template and produced a three-topic explanation of supplied 08:00-11:12 passage evidence, with source reasoning/examples, labelled AI TDD explanations and a labelled invented test example. It omitted project application and correctly limited coverage to the supplied passages. This is a synthetic format probe, not a mounted Hermes or real MCP retrieval acceptance test.

Targeted command: .venv/Scripts/python.exe -m pytest -q tests/test_source_content_qa_skill.py tests/test_spec_056_source_content_docs.py tests/test_ai_governance_docs.py tests/test_spec_kit_backfill_docs.py tests/test_repository_secret_boundary.py tests/test_repository_gitignore_policy.py --basetemp=.pytest-tmp/56-notes-target --tb=short. Result:27passed,29skipped,exit0,153.55s. The29skips were Git availability/ownership gating; the standard full run applies process-only exact-repo safe.directory so these checks run. Skill quick_validate reports `Skill is valid!`; compileall and diff-check command block exit0, with existing line-ending warnings.

Standard full verification is running with process-only exact-repo Git safe.directory: .venv/Scripts/python.exe -m pytest -q -rs --basetemp=.pytest-tmp/56-notes-full --tb=short. Log: .pytest-tmp/56-notes-full.log. Final result and closing checks will be appended after completion; do not treat this pending run as passed.

Follow-up validation continuation: the restricted-context full run ended early near56%,exit1,without a final pytest summary. Progress showed two failures at the existing test_mcp_source_preparation.py::test_actual_owned_transport_submit_disconnect_and_later_status[False/True] cases. The incomplete run is not a passed full suite; collection contains2877items. A focused restricted-context `-vv -x` rerun reproduced the False case as `AssertionError: owned HTTP startup timeout` at line119,1failed,41.13s. No Skill/template is read by that transport test.

The identical two owned transport cases were then run with approved scoped execution escalation and process-only Git safe.directory:2passed,47.09s,exit0; the only warning was denied .pytest_cache metadata writing. This indicates an execution-context effect but does not establish its precise cause. No HTTP/Core/worker code or timeout assertion was modified. Current venv reports Python3.12.9; historical Python3.11 observations above remain historical. The media/provider stages are owned fakes.

Current format/docs checks:8passed,exit0,1.17s (--basetemp=.pytest-tmp/56-notes-docs-close); separately repeated compileall -q src scripts exit0 and git diff --check exit0. A standard full run now uses the same approved execution context as the passing transport probe: --basetemp=.pytest-tmp/56-notes-host-full,log .pytest-tmp/56-notes-host-full.log. This run is still pending; no full-suite success is claimed yet.

Windows temporary-path correction: the host full run exposed existing external-data verification failures writing long digest filenames under the long `56-notes-host-full` basetemp. A single matching host probe with `56-notes-external-host-probe` reproduced FileNotFoundError in `_write_preverification_boundary_snapshot`; the identical test with the short `56e` basetemp passed (1passed,0.68s). The excessive path length came from this session's validation-directory choice, not a Skill edit. No runtime code, assertions or Windows settings were changed.

Stopped only the verified owned long-basetemp pytest process: Get-CimInstance filtered exact `-m pytest` and `--basetemp=.pytest-tmp/56-notes-host-full`; actual child PID64660 was killed using .NET after rechecking its command line. Launcher PID87460 had already exited. The stopped run returned-1 without a final pytest summary and remains failed/incomplete evidence; its log and scratch files are preserved. No other process or history was targeted.

The final standard full run now uses unused short workspace-contained `.pytest-tmp/56nt`, with log `.pytest-tmp/56nt-pytest.log`, process-only exact-repo Git safe.directory and the passing host execution context. Workspace containment and absence of existing temp/log paths were checked before launch. This run is pending; its final result will be recorded separately.

Recovery continuation: the 56nt session was unavailable after interruption; its log stopped near22% without a summary and an exact scoped process query found no surviving test process. It is incomplete evidence, not a passing full suite. Started a hidden owned PowerShell runner for a fresh unused short basetemp56n2, preserving `.pytest-tmp/56n2-pytest.log` and an explicit `.pytest-tmp/56n2-exit.txt` receipt. The runner applies process-only exact-repo Git safe.directory and the approved host execution context; it performs only the standard offline pytest suite. A subsequent server restart interrupted the tool session but the background test process survived and log progress continued. No duplicate full suite was launched after that restart.

Current follow-up checks after recovery:8passed,exit0,1.02s (`.venv/Scripts/python.exe -m pytest -q tests/test_source_content_qa_skill.py tests/test_spec_056_source_content_docs.py --basetemp=.pytest-tmp/56nd --tb=short`). Repeated `compileall -q src scripts` exit0, exact-repo `git diff --check` exit0 (existing line-ending warnings), and UTF-8 Skill `quick_validate.py` reports `Skill is valid!`,exit0. The56n2 full suite is still pending; final counts and exit receipt will be appended after completion.

### Learning-note format final verification

**Full suite:2851passed,26skipped,1warning,976.09s(16:16),exit0.** Command: `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.pytest-tmp/56n2 --tb=short`, with process-only exact-repo Git safe.directory and approved host execution context. Authoritative output is `.pytest-tmp/56n2-pytest.log`; the runner's explicit `.pytest-tmp/56n2-exit.txt` receipt contains0. All26skips are unavailable native symlink creation (secure snapshot3; study-guide10; verified catalog3; source revalidation1; derivation safety9). The single warning is denied `.pytest_cache` metadata writing; no test failed. Earlier interrupted/long-path runs above remain historical failed or incomplete evidence and are superseded only by this completed run.

Changed paths for this bounded follow-up: `.agents/skills/source-content-qa/SKILL.md`, new `.agents/skills/source-content-qa/references/learning-notes-template.md`, `tests/test_source_content_qa_skill.py`, `specs/056-source-content-query/contracts/skill.md`, `specs/056-source-content-query/quickstart.md`, and this implementation log. The editable template, reference route and portability guard satisfy the approved format change. Synthetic format evidence and actual mounted Hermes acceptance remain distinct; Hermes mounting/reload was not performed. No runtime, provider, source-data, cache, dependency or host-settings change; no branch, commit, worktree or deployment. Unrelated working-tree changes and all verification history are preserved.
