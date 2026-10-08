# Validation guide

Status: Local implementation and verification complete; actual operator-source and Hermes acceptance pending. Results and remaining environment checks are separated below.

## Local tests and standard checks

Use synthetic owned fixtures; do not download/transcribe, read .env, modify settings or call providers.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/060-source-learning-host-reliability'
.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
.\.venv\Scripts\python.exe -m pytest -q tests/test_source_learning_host_reliability.py tests/test_source_content_query.py tests/test_mcp_source_content_query.py tests/test_source_learning_reliability.py tests/test_source_content_qa_skill.py tests/test_source_learning_entry_skill.py tests/test_learning_mcp_acceptance.py tests/test_spec_060_source_learning_docs.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
.\.venv\Scripts\python.exe scripts/verify_learning_mcp.py inventory
```

Runtime and instruction guards are in test_source_learning_host_reliability.py; package integrity checks use test_spec_060_source_learning_docs.py and existing Spec Kit governance tests. Record exact failures/skips; no blanket statement that platform skips establish native Linux execution.

Expect new57-character tokens, legacy continuation acceptance/upgrading, exact split-text reconstruction, rejection of changed scope/version and corrupt positions, successful one-time recovery from the last successful response and partial stopping after a second error. Check recovery call/character budgets and all preparation no-retry/approval rules. Description tests parse actual YAML, normalize Unicode characters, simulate desc[:57] + '...', exercise an overlong negative case and check every Skill's visible purpose. Main Skills and references must consistently require foreground source calls and evidence-first answers.

## Whole-source MCP verification with unchanged defaults

Use an explicitly selected owned corpus root or already managed numeric-loopback endpoint; inventory alone has no scope_complete result and does not prove host loading. No new service or installation is required/authorized here.

Obtain current inspect metadata using only podcast_id and episode_ref. Choose wholeEnd strictly above end_seconds and lower bound0, including a possible final zero-duration segment. Set ownedCorpus, sourceId, sourceRef and wholeEnd to operator-selected values locally; these variables are not host settings to commit.

```powershell
.\.venv\Scripts\python.exe scripts/verify_learning_mcp.py verify --data-dir $ownedCorpus --podcast $sourceId --episode $sourceRef --start 0 --end $wholeEnd
```

For an already managed HTTP server, replace --data-dir with --mcp-url and the operator's existing numeric-loopback /mcp URL. Keep defaults: max_calls20, max_total_chars120000, timeout60. Do not silently raise limits merely to label the default check successful. The verifier remains no-retry.

Required result: ok=true, scope_complete=true and selected_segments == delivered_segments == current inspect segment_count, with the same source_version before/after. A partial range with scope_complete=true does not meet this whole-source acceptance. Defaults are not a promise that every arbitrarily long source fits; budget exhaustion is partial and disclosed. Add a real-SDK synthetic1448-segment source over60000 characters as the repeatable default-budget regression; label it synthetic. The actual operator source check remains separate if access is unavailable.

## Actual Hermes acceptance (separate, pending)

An operator synchronizes all three learning Skills and references, reloads MCP/Skills as required, and records Hermes revision/model/ACP mode and installed descriptions locally. Do not commit settings, transcripts, tool/session logs, source media or personal handoff files. The actual installed version determines whether ACP notification behavior matches historical reports.

1. **Fresh URL entry, no body preloading**: Give one prepared supported YouTube/X URL and request whole-source notes. Verify the discovery view exposes local priority. Skill loading can precede source processing; the first source-processing MCP call must be prepare_learning_source(confirm=false). No x_search/web_search/web_extract or third-party transcript lookup occurs first. A blocked or unavailable path explains and asks user choice; failure does not automatically authorize web fallback.
2. **Foreground and completeness**: Observe direct main-conversation prepare/inspect/search/read calls, sequential pages, no delegate_task/background AI reading and no unsupported promise that notes continue after the turn. Whole-source notes require all consecutive same-version chunks. Interrupted reading reports actual examined ordinals/time scope and partial status. Accepted download/transcription jobs can be described as submitted/as-of status without claiming completed notes or automatic AI continuation.
3. **Recovery fault injection, separate from natural behavior**: In an isolated read-only harness, inject a cursor copying mistake. After exact-ID inspect and original-version validation, retry must copy next_cursor from the last successful response, not repeat the corrupt outgoing request. No first successful page means empty cursor. A second error, changed source or failed inspect stops partial. This artificial result is reported separately from an unmodified model conversation; never weaken the server, execute preparation or publish state to induce an error.
4. **Source concept questions**: Ask what the speakers emphasize about TDD or why they use a kitchen metaphor. Verify search/read evidence and surrounding context precede source-attributed answers even though these resemble conceptual questions. No literal matches are not reported as conceptual absence. General knowledge, if useful and allowed, is explicitly AI 補充.
5. **Speaker and example review**: Compare relevant read passages to the answer. Without explicit gender, assistant prose uses 講者 or confirmed names, not 他/她. Preserve key example details and their reasoning; for the operator's previously reported kitchen passage, check the family-in-the-kitchen detail against the actual transcript instead of inferring it from this guide. Do not force examples from unread/irrelevant passages.
6. **Requested output only**: No unrequested project application, audience summary or extra deliverable; source-only requests omit AI supplements. Necessary evidence/coverage/ASR caveats remain accurate. Review supplements for separate labeling and source examples for correct attribution.

Report each scenario as passed/failed/not run with safe metadata and brief conclusions. Deterministic delivery does not prove model compliance or transcription accuracy; textual Skill guards do not prove these host scenarios. Keep unresolved host acceptance pending rather than treating local pytest as a substitute.

## Current local verification and pending environment acceptance

The implementation's targeted cursor/MCP/Skills/verifier/registry/setup/docs/privacy checks passed288 tests with1 native-symlink OSError skip. The other affected Skill frontmatter/approval/no-retry checks passed46 tests. Independent read-only review found no actionable implementation issue; its separate focused synthetic check passed52 tests with2 intentionally deselected. Compileall and tracked/new-file whitespace checks passed. Final full suite:2979 passed,27 skipped,exit0 in1131.22s; all27 skips were native symlink OSError. Command: python -m pytest -q --basetemp=.pytest-tmp/60h -p no:cacheprovider --tb=short -rs. The first full run found one named-episode description guard failure; the compact description was corrected without changing its body, then70 focused checks and the final full run passed.

The real owned stdio SDK/CLI test test_default_cli_sdk_delivers_whole_long_synthetic_source passes with1448 synthetic segments, over60000 characters, default budgets, exact split-text delivery, scope_complete=true and inspect/selected/delivered equality. This is synthetic delivery evidence, not actual source accuracy or Hermes note-quality acceptance.

verify_learning_mcp inventory returned ok=true with all seven learning resources available and host_loaded=false. A read-only attempt against the previously identified X source in the repository data root stopped at inspect with source_missing; no page was read and no preparation was started. T026 remains pending until the actual prepared corpus is selected/available. T027 remains pending because the remote Hermes environment is unavailable here. Do not infer host loading, model obedience or real-video completeness from local results.

The generic skill-creator quick validator accepts13 portable Skills. It rejects the10 Spec Kit Skills' existing compatibility metadata key; that key and every other non-description metadata value are preserved. All23 Skills independently pass the parsed YAML/60-character/purpose guards. No source data, settings or session/operation traces are added.

Convergence found no additional unbuilt code/Skill work against the20 requirements and four stories. Existing T026/T027 remain pending; no duplicate convergence tasks were appended. Implementation verification preceded Git publication; commit/push requires separate explicit user authorization. No feature branch, host installation or deployment was performed.

Publication checks: the two new SPEC060 test files pass Ruff lint/format checks and focused pytest after preserving the imported fixture explicitly and binding the mutation callback value. Repository-wide lint retains the782 pre-existing diagnostics observed on SPEC059; GitHub CI stops at Lint before pytest. Local test results and actual Hermes acceptance remain separate from this CI baseline.
