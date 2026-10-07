# SPEC058 implementation evidence

2026-10-08. User approved the proposed scope and explicitly requested continuation after updated AGENTS instructions. Root sole writer, existing dirty044-057 changes preserved. No branch/commit/worktree/deployment.

## Planning

Constitution1.0.1 reviewed without amendment. Specify/clarify/plan/checklist/tasks applied with explicit SPECIFY_FEATURE_DIRECTORY=specs/058-learning-mcp-acceptance. Official spec-template resolved; setup-plan and setup-tasks returned058 paths. No extensions.yml, no hooks/branches. Clarify resolved developer/live boundary from existing user intent; no new scope question. Written quality checklists8/8 and10/10 complete. Analyze:12FR,4SC,3stories mapped to17tasks;100% requirement coverage, no contradiction/unmapped implementation task. Live operational gates are intentionally independent, not promised automated outcomes.

Sandbox process startup failed twice with helper_unknown_error/setup refresh before execution, unrelated to code or auto-review. Narrow escalated reads/scaffold/plan write succeeded; no automatic-approval rejection. Official plan scaffold required scoped escalation to replace due ownership. No host secrets/settings read.

## RED and GREEN

- Focused RED `.venv/Scripts/python.exe -m pytest -q tests/test_learning_mcp_acceptance.py::test_selected_delivery_is_metadata_only_and_not_host_acceptance tests/test_learning_mcp_acceptance.py::test_inventory_includes_transitive_references_and_template tests/test_spec_058_learning_acceptance_docs.py --basetemp=.pytest-tmp/58r -p no:cacheprovider --tb=short`:4failed,exit1,1.84s. Core absent, scope/discovery guidance absent.
- Core first GREEN41passed/1native-symlink skip,2.91s,exit0 (`58g1`). Additional default-connection/.env-link/frontmatter RED3failed/2passed,4.83s,exit1 (`58r2`); fixes GREEN46passed/1skip,3.60s,exit0 (`58g2`). Fake async adapter was corrected to await the Core rather than nesting asyncio.run.
- Initial broad regression `58t`:190passed/1skip/1failed,201.80s,exit1; failure was missing explicit metadata wording in the new written contract. Contract clarified before final focused checks.
- Fresh reviewer reproduced HTTP SDK raw-body logging and implicit GET reconnect. No-network focused RED2failed,12.79s,exit1 (`58r3`). Temporary owned SDK logger filters and pre-network replay hooks fixed these; focused GREEN50passed/1skip,11.12s,exit0 (`58g3`).
- Reviewer reproduced reference-style Markdown omission and legitimate overlap-selected ordinal gaps. Focused RED2failed/1passed,3.45s,exit1 (`58r4`); stdio SDK logging RED1failed,6.09s,exit1 (`58r5`). Added Markdown definitions, strict increasing selected ordinals (not forced adjacency), exact chunk/count validation and quiet context on stdio.
- Final focused command: `.venv/Scripts/python.exe -m pytest -q tests/test_learning_mcp_acceptance.py tests/test_spec_058_learning_acceptance_docs.py --basetemp=.pytest-tmp/58g4 -p no:cacheprovider --tb=short`:54passed/1native-symlink skip,7.86s,exit0. HTTP tests use actual SDK with MockTransport, not external networking.

## Actual local CLI / SDK evidence

Existing isolated source x-natewiki/2106893534980685927 at `.pytest-tmp/54m/data`; four preserved inputs include the existing writer.claim (never cleaned). Source_version ddfc97d0ada4c1b90bd3f327f98293eac9a75961b96d7921700af40e266026af, recorded medium/cuda/float16/VAD=true. No ASR/provider/corpus generation/config changes.

- `.venv/Scripts/python.exe -X utf8 .pytest-tmp/58/pilot.py`: three fresh inspect/read/final-inspect runs, exit0; TDD600–674:21segments/1277chars; intent573–633:16/1011; kitchen749–929:52/2873. Same version, registry35; all four file hashes preserved. Metadata receipt `.pytest-tmp/58/pilot-receipt.json`.
- `.venv/Scripts/python.exe -X utf8 .pytest-tmp/58/multi-page-pilot.py` invokes public `scripts/verify_learning_mcp.py verify --data-dir ... --podcast x-natewiki --episode 2106893534980685927 --start 0 --end 4000 --max-total-chars 80000 --timeout 60`:exit0,11consecutive pages,1088segments,60834chars, final version unchanged, all four input hashes preserved. Receipt `.pytest-tmp/58/multi-page-receipt.json`. The receipt certifies selected interval delivery, not whole-source understanding/ASR accuracy/Hermes.
- `.venv/Scripts/python.exe -X utf8 .pytest-tmp/58/negative-cli.py`: public inventory exit0/all7resources; public verify against explicit empty owned root exit1/source_missing, no files created. Helper exits0 verifying the intended rejection. Receipt `.pytest-tmp/58/negative-receipt.json`.
- First pilot helper rejected its own too-narrow extension assumption before MCP execution: the fourth file is writer.claim. Explicitly admitted that known owned file into hashing, preserved it and reran. No source was copied/repaired.

## Currently mounted MCP: separate evidence

2026-10-08 actual Tool35 inspect returned source_missing. Separate actual Tool33 original X URL preview returned blocked/metadata_unavailable, network_read=true, writes_count0, no plan/job, no confirmation. Public metadata network was attempted; no download/transcription occurred and failure root cause is not inferred. Receipts `.pytest-tmp/58/mounted-source.json` and mounted-preview.json. These prerequisites are not satisfied by owned SDK success; mount settings were not altered.

## Independent review

Fresh-context read-only reviewer read standards and058 spec/plan/contracts separately, bounded review to new utility/tests/docs, and independently reproduced four gap classes above. Final review found no outstanding Critical/Important/Minor findings. Actual SDK/MockTransport successful path, no-leak probes and14fake-session checks passed; reconnect probe changed from3GETs to1 dispatched GET; all four logger filter lists were restored. No reviewer edits/network/provider/.env/settings access. Research agent was requested but remained pending_init and was stopped; root researched local interfaces directly and the independent reviewer supplied additional concrete evidence. No unavailable research output is counted.

## Preservation and final checks

Current `.venv/Scripts/python.exe -m compileall -q src scripts`:exit0. `git -c safe.directory=<this repo> diff --check`:exit0. `.venv/Scripts/python.exe .pytest-tmp/57s/preservation-check.py`:154existing runtime/standalone Skill files checked,0changes. New utility is additive; original35 tool names/order/contracts and original Skill behavior are unchanged.

Full regression `.venv/Scripts/python.exe -m pytest -q -rs --basetemp=.pytest-tmp/58f --tb=short -p no:cacheprovider`:2917passed,27skipped,1174.83s,exit0. Every skip is native symlink creation OSError:1 acceptance inventory,3 secure snapshot,10 study-guide bundle,3 verified report catalog,1 source revalidation,9 derivation safety. No warnings reported; cacheprovider explicitly disabled. Stdout/stderr saved to new `.pytest-tmp/58/full-pytest.log`; full-exit.txt independently contains0. Full run includes all unchanged functionality and final behavior fixes. Only completion-status documentation edits followed this run; closing focused checks are recorded below.

## Converge

Explicit058 prerequisite check returned this package; no extensions.yml before/after. Assessed12FR,4SC,8user-story acceptance scenarios,8plan obligations and all9constitution principles. Zero missing/partial/contradicts/unrequested build findings, zero appended tasks. Converge itself left tasks.md byte-for-byte unchanged: before/after SHA256 dcae90d858b5e3385f8dd6f6c67b2651d046590b588e1b06341387c2f4c2e2ae. After assessment, implementation bookkeeping marked T016/T017 complete separately. No empty Convergence phase added.

| Build intent | Current evidence |
|---|---|
| FR001–003 / explicit selection and capabilities | Core request/transport validation, registry check; CLI and negative tests |
| FR004–007 / pinned bounded safe delivery | Core inspect/read/final-inspect, chunk/cursor/count/budget tests; actual11-page CLI receipt and SDK logging probes |
| FR008 / complete resources | Bounded transitive Markdown inventory, frontmatter/template/missing/unsafe checks; actual7-resource inventory |
| FR009–011 / content and staged handoff | Three questions/replay rubric, full-folder handoff guide, independent operational records and discovery tests |
| FR012 / compatibility and preservation | Full2917-passed regression, unchanged35-tool registry/contracts, four pilot file hashes and154 prior-file preservation checks |
| SC001–004 and US1–3 / deliverable outcomes | Corresponding Core/CLI failures and success; complete resource inventory; human criteria and repeatable local/VM instructions |
| Plan obligations | Core/CLI boundaries, transport selection, finite metadata, chunk/version/budget handling, safe inventory, handoff, TDD/full review and preservation all implemented |
| Constitution I–IX | Local traceable metadata, thin CLI, no confirmed side effects/provider/secrets/advice/live market/cache rebuild, evidence separation and current verification |

Real Hermes, live preparation and human replay remain pending OP001–003; SDK evidence cannot close057 T017/T018. Currently mounted Tool35 source_missing and Tool33 metadata_unavailable remain unresolved operational evidence, not silently repaired or reclassified as success.

## Closing verification after status edits

- `.venv/Scripts/python.exe -m pytest -q tests/test_learning_mcp_acceptance.py tests/test_spec_058_learning_acceptance_docs.py --basetemp=.pytest-tmp/58close -p no:cacheprovider --tb=short`:54passed,1native-symlink skip,7.81s,exit0.
- `.venv/Scripts/python.exe -m pytest -q tests/test_spec_registry_status_consistency.py tests/test_docs_registry_count_consistency.py tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/58registry -p no:cacheprovider --tb=short`:18passed,6.89s,exit0.
- `.venv/Scripts/python.exe -m compileall -q src scripts`:exit0.
- `git -c safe.directory=<this repo> diff --check`:exit0; Git reports CRLF-to-LF warnings across existing dirty files, no whitespace errors.
- `.venv/Scripts/python.exe .pytest-tmp/57s/preservation-check.py`:154files,0changed,exit0. Four pilot source hashes also remained unchanged in their recorded actual CLI/SDK runs.

T001–T017 developer tasks complete; OP001–003 remain unchecked. No behavior changed after the full suite, so no second full run was needed for documentation bookkeeping.

## Changed paths and delivery boundary

Added src/corpus_ingest_core/learning_mcp_acceptance.py, scripts/verify_learning_mcp.py, tests/test_learning_mcp_acceptance.py and tests/test_spec_058_learning_acceptance_docs.py; added the058 spec/design/contracts/checklists/tasks/acceptance/handoff/evidence package. Edited discovery only in AGENTS.md, specs/README.md, docs/install-and-porting.md, docs/verification-matrix.md and docs/roadmap.md. Existing044–057 runtime/tests/standalone Skills are preserved. No branch, commit, worktree, deployment, new tool, settings repair, cache rebuild or confirmed preparation/provider action.
