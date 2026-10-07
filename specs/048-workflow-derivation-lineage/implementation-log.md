# SPEC048 Implementation Evidence

User authorized implementation on2026-10-04 (start implementation, then continue). One active writer; existing dirty044-047 changes preserved. Baseline recorded in ignored .pytest-tmp/48-implementation-baseline.json: runtime27 tool order/signatures and file hashes, plus git status. Requirements/safety quality checklists have0 incomplete items. No extension hooks. No branch/worktree/commit/deployment or real provider operations.

## RED/GREEN slices so far

- Codec absent (ModuleNotFoundError) and preview lacked metadata_writes (AttributeError). Implemented pure bounded strict codec/defaulted model field/additive preview:26 passed (.pytest-tmp/48codec-green).
- Generation receipt absent (FileNotFoundError). Captured consumed inputs/request before provider, staged-byte output digests and same-directory receipt publication. Core/MCP/preservation regression258 passed,9 native-symlink skips (.pytest-tmp/48generation-green,68.12s).
- Inspection entry absent (AttributeError). Implemented six-state finite query with ordered roles and bounded observations:91 passed (.pytest-tmp/48query-green,64.38s).
- MCP wrapper absent (ModuleNotFoundError), then10 passed (.pytest-tmp/48mcp-green,4.26s).
- Skill lacked metadata clauses/oracle fields. Added metadata display/validation and narrow owned receipt exception, updated only derivation fixtures and seven incompatible metadata cases:27 passed (.pytest-tmp/48skill-g2,7.95s). These are static offline oracles, not live agent execution. The protected .agents Skill required a scoped sandbox escalation; automatic review allowed the authorized single-file write.
- Registry expected28 while live27 (RED). Appended separate mcp_tools_workflow_lineage group; the original plan's same-group decorator would register before26/27, so plan/tasks now name the separate group. First registry regression52 passed/1 docs count failure; corrected install-and-porting current count.

No default context file was opened as a complete settings dump; tests use isolated fixtures. No .env, real provider, network, corpus operation or cache rebuild.

## Integration and independent review

Targeted integrated Core/MCP/Skill/Tool27/registry/facade/setup/console/docs regression:459 passed,9 native-symlink skips, exit0,165.61s (.pytest-tmp/48target). Additional public reparse/special-entry/source-mutation cases:7 passed (.pytest-tmp/48query-extra).

Fresh-context read-only roles review_048_behavior and review_048_engineering reviewed requirements and engineering separately. They found safe lecture-read failure classification, unsafe-entry versus recovery precedence, expected profile-unavailable exceptions and receipt identity regex alignment. Ten focused checks observed RED,10 failed (.pytest-tmp/48review-r2). Query-only fixes preserve generation046 behavior; codec now matches canonical leading-alphanumeric episode alphabet. Both reviewers re-read fixes and reported no remaining findings within scope. Reviewers performed no writes/tests/network/providers; test evidence belongs to the parent. Excluded claims remain live agent compliance, adversarial/concurrent-writer protection, crash durability, model quality and upstream lecture freshness.

A first full-suite run started before these review fixes; it is superseded by the required full-suite rerun after fixes, regardless of its result. The initial PowerShell append of review tests hit a transient file stream error and collected0 cases; Python append succeeded and produced the10 actual failures above.

Baseline runtime check after registration:28 tools, first27 names/order unchanged,0 existing signature changes.640 baseline files were hashed; only authorized048 runtime/tests/docs/Skill/package paths changed. Existing046/047 Core, Tool26/27 modules, lecture Skill and prior044-047 packages remain protected.

Review-fix GREEN: .\.venv\Scripts\python.exe -m pytest -q tests/test_workflow_derivation_lineage.py tests/test_mcp_workflow_derivation_lineage.py tests/test_workflow_derivation_safety.py tests/test_mcp_learning_workflow_next_step.py --basetemp=.pytest-tmp/48review-green --tb=short ->279 passed,9 native-symlink skips, exit0,103.87s.

compileall -q src scripts and git diff --check both returned0 after fixes (CRLF/LF warnings only). A supplemental hash script initially assumed pyproject.toml was in the runtime-directory baseline and raised KeyError; corrected comparison uses its prior planning baseline. Recheck:50 prior044-047 package files unchanged; Tool26/27 modules, lecture Skill, existing publication-safety tests and pyproject.toml unchanged.

Superseded first full run (.pytest-tmp/48full):2044 passed,55 skipped, exit0,570.68s.26 skips were native symlink OSError;29 Git ignore-policy checks skipped because this Windows checkout was not trusted by ordinary Git subprocesses. The final rerun will provide process-local safe.directory via GIT_CONFIG_COUNT/KEY/VALUE, without changing persistent Git configuration, so those29 policy guards execute. This first run also predates the final review fixes and is not closeout evidence.

New receipt publication/fault cases live together in test_workflow_derivation_lineage.py; existing test_workflow_derivation_safety.py remains unchanged and is run as regression. T008 path wording was aligned to this surgical placement. No requested behavior or fault category was removed.

Second full run (.pytest-tmp/48full-final):2083 passed,26 native-symlink OSError skips, exit0,518.66s; all29 Git ignore-policy checks ran with temporary process-local safe.directory. During final acceptance review an escaped YAML surrogate revealed UnicodeEncodeError rather than inputs_unavailable (1 actual RED, .pytest-tmp/48unicode-red). Query-only catch now includes UnicodeError; fresh behavior reviewer confirmed closure, and Core/MCP119 passed (.pytest-tmp/48unicode-green,46.47s). An optional attempt to stop the superseded test runner via a specifically filtered process query was denied by the sandbox;0 processes stopped, and the run finished normally. Its result is superseded by final verification below.

Final additive acceptance: unencodable context and actual Tool26 cover-only preservation of receipt/pair/lecture bytes ->2 passed (.pytest-tmp/48accept-final,3.42s). Cover-only constructs no provider, never refreshes lineage, and inspection remains current. No runtime or test changes remain planned before the last full run.

## Requirement and success-criteria evidence map

| Requirement | Public Core/MCP/fixture evidence |
| --- | --- |
| FR-001 / SC-001 | test_confirm_records_consumed_inputs_and_actual_staged_bytes; test_provider_time_source_mutation_does_not_rewrite_recorded_inputs |
| FR-002 / SC-001 | Same generation test checks captured messages and hashes of actual on-disk05/06 bytes, including mixed LF/CRLF lecture input; staged hashing publication fault tests |
| FR-003 / SC-003 | test_record_publication_faults_keep_matching_tuple_or_recovery covers receipt write, staged read/hash, output cap, backup/publish/rollback/cleanup/report failures; unchanged046 safety suite also runs |
| FR-004 | test_preview_metadata_is_separate_and_provider_free pins generate/reuse/force Core/MCP metadata lists and zero writes/provider; confirmed result serializes additive defaulted field |
| FR-005 | test_force_replaces_recognized_record_and_reuse_leaves_it_byte_identical, legacy state fixtures, test_lecture_cover_only_preserves_lineage_and_pair_bytes |
| FR-006 / SC-002 | Six-state inspection fixtures, two required MCP arguments, pre-access invalid identity tests and canonical-title no-fallback case |
| FR-007 | Strict codec role/schema/digest/duplicate/limit cases, reserved-name pre-provider refusal, invalid/unsupported/wrong-identity/unreadable receipt inspection matrix |
| FR-008 | Effective context comments/whitespace/unused fields ignored, ordering/duplicates detected; valid custom context skips all content/default-context loading |
| FR-009 / SC-002 | Closed safe result shape and private sentinels; zero-write/provider/cache tripwires; bounded source/output/receipt failures; MCP fixed error mapping |
| FR-010 / SC-004 | Skill static clause/oracle cases, append-only exact28 registry and facade order, unchanged Tool26/27 behavior regression, baseline first27 names/order/signatures comparison |
| FR-011 | Provider-time mutation observed stale, report failures preserve committed tuple, malformed receipt retained byte-identical on reuse; no freshness gating of Tool27 |
| FR-012 / SC-004 | Actual RED/GREEN commands above; independent read-only behavior/engineering reviews and closures; full checks and convergence closeout below |

Status markers/checklists document lifecycle and requirements clarity; they do not replace the executable acceptance evidence.

## Final implementation verification

.\.venv\Scripts\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/48f3 --tb=short ->2085 passed,26 skipped, exit0,516.99s. The temporary process-local GIT_CONFIG safe.directory setting made all Git ignore-policy guards execute. All26 remaining skips are native symlink OSError: secure snapshots3, lecture10, catalog3, report revalidation1, derivation safety9. Simulated reparse/special-entry checks and new048 acceptance cases all execute. No runtime/test changes after this final suite.

.\.venv\Scripts\python.exe -m compileall -q src scripts ->exit0; git -c safe.directory=D:/SourceCode/CORP/FASBD/NewProd/GitHub/podcast-ingest-core diff --check ->exit0 after final code. Line-ending warnings are saved in ignored .pytest-tmp/48-diffcheck-warnings.txt. README entrypoints now link the new query contract; their pre-edit hashes were added as a supplemental baseline before changing either file.

## Convergence and changed paths

Constitution reviewed with no amendment. Spec Kit converge used explicit048 selector/check-prerequisites; present-code intent assessment covered FR-001 through FR-012, SC-001 through SC-004, all three stories/nine acceptance scenarios, edge cases and named plan seams. No unbuilt requirement or unrequested runtime was found;0 tasks appended, tasks.md byte-identical during convergence. Implementation tracking then marked T022, leaving22 completed tasks/0 pending. No extension hooks or taskstoissues action.

Runtime paths: src/corpus_ingest_core/workflow_derivation.py, workflow_derivation_lineage.py (new pure codec), models.py, mcp_tools_workflow_derivation.py, mcp_tools_workflow_lineage.py (new read-query group), mcp_server.py; scripts/validate_mcp_setup.py.

Verification paths: tests/test_workflow_derivation_lineage.py, tests/test_mcp_workflow_derivation_lineage.py, tests/test_workflow_derivation_bundle_skill.py, tests/fixtures/workflow_lineage_skill_cases.json; derivation-only updates in tests/fixtures/learning_workflow_skill_cases.json; registry/facade/setup/console/current-count guard tests and tests/test_spec_048_workflow_lineage_docs.py. Existing046 publication safety tests were preserved and rerun.

Operator/documentation paths: .agents/skills/workflow-derivation-bundle/SKILL.md; README.md, README.zh-TW.md; AGENTS.md; docs/{agent-handoff,ai-development-framework,api,architecture,claude-mcp-setup,codex-mcp-setup,install-and-porting,mcp-readiness,mcp-usage,roadmap,verification-matrix}.md; specs/README.md and this048 package. Ignored .specify/feature.json remains an explicit local048 selector.

Boundaries: one writer; existing044-047 packages and Tool26/27/lecture Skill bytes protected. No .env, real provider/network/corpus execution, cache rebuild, new dependency, branch/worktree/commit/staging, release or deployment. Stored receipt contains only identities/versions/context discriminator/digests; public query returns no body/hash/path/settings/error text. Existing exact ack, no-investment-advice, bounded market-data and manual-cache constraints remain.

Remaining limits: legacy pairs are untracked, custom-context comparison is not_evaluated, equality is limited to derivation inputs/outputs and observations are non-atomic. No upstream lecture/transcript freshness, semantic/model-quality, hostile-tamper or crash-durability claim. A long-running MCP server must reload this code to expose Tool28; no running server was restarted by this task.

## Final closeout checks

After lifecycle/README updates, .\.venv\Scripts\python.exe -m pytest -q tests/test_spec_048_workflow_lineage_docs.py tests/test_spec_047_learning_next_step_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_020_verified_research_report_catalog_docs.py tests/test_docs_registry_count_consistency.py tests/test_repository_secret_boundary.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_server_facade_boundary.py --basetemp=.pytest-tmp/48closeout --tb=short ->80 passed, exit0,86.65s.

Final baseline check:642 existing files (640 initial plus2 README pre-edit hashes);39 authorized existing paths changed,0 unexpected changes.28 tools; first27 names/order and every existing signature unchanged.22 tasks completed,0 pending. The50 prior044-047 package files and protected Tool26/27/lecture Skill/046 safety tests remain unchanged. Final diff check was repeated after this record, with exit0 and only working-tree line-ending warnings.
