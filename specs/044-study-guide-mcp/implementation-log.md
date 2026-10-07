# Implementation Log — 044 Safe Study-guide MCP Access

**Interpreter**: `.\.venv\Scripts\python.exe`
**Feature selector**: `SPECIFY_FEATURE_DIRECTORY=specs/044-study-guide-mcp`
**HEAD**: `b42b5a2c765ac41b8e22134a2752928f8d40443e` (`b42b5a2 fix: publish workflow derivation 05/06 as one directory swap`)
**Writer**: one implementation session. No branch, worktree, commit, or deployment.

## T001 — Baseline reconciliation

HEAD matches `workflow-record.md`. Uncommitted planning at start was `M AGENTS.md`, `M specs/README.md`, `?? specs/044-study-guide-mcp/`. Those files were preserved and then extended by this implementation. No functional source differed from `b42b5a2` before the first RED.

`check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` selected `specs/044-study-guide-mcp` with research, data-model, contracts, quickstart, and tasks.

## T002 — Pre-change baselines

| Command | Result |
| --- | --- |
| Core set (`044-core`) | 59 passed, exit 0, 16.10s |
| MCP set without the new file (`044-mcp`) | 49 passed, exit 0, 17.19s |
| Safety set (`044-safety`) | 85 passed, exit 0, 91.63s |
| Docs set (`044-docs`) | 40 passed, exit 0, 4.85s |

No skips. Each run also emitted `PytestCacheWarning`: `.pytest_cache` could not be created (`WinError 5` access denied). That did not fail the tests.

## RED → GREEN

| Slice | RED | GREEN |
| --- | --- | --- |
| T003/T004 preservation | 3 failed. Cover-only rewrote LF to CRLF and dropped `05`/`06` plus `extra.bin`. Force deleted `extra.bin`. | `tests/test_study_guide_bundle.py` 22 passed |
| T005/T006 identity and no-follow | Reserved/invalid identity raised `StudyGuideBundleError` instead of `StudyGuideBundleStateError`. Child directory, special file, and mocked reparse did not refuse. | 48 passed, 10 skipped |
| T007/T008 derivation and recovery | Preview with `05`/`06` or a recovery sibling did not raise. | 82 passed, 10 skipped |
| T009/T010 publication states | All 8 injections raised generic `StudyGuideBundleError`. | The 8 failure tests plus confirm/cover/force passed (11) |
| T012/T013 projector | `describe_study_guide_plan` was absent. | 3 passed, including dry-run |
| T021/T022 registry | After expectation updates and before the facade import: registry length 25, order missing `generate_study_guide_bundle`. | Registry, workflow slot, setup validation, and Tool 26 behavior tests passed after the append |
| T023/T024 docs | Dynamic count checker listed live `25` claims against a 26-tool registry. | Checker passed after the live-doc update |

Native symlink cases (`test_symlinked_source_is_refused`, summary ancestor, bundle ancestor, dangling link, symlinked seed; preview and confirm) skip with `symlink creation is unavailable: OSError`. Portable checks still run: child directory, special-file mode, and mocked Windows reparse.

## T026 — Final verification

These commands ran in this session. Planning-session counts were not reused.

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp/44f -q --tb=line` | **1639 passed, 17 skipped**, exit 0, 770.61s |
| same interpreter `-m compileall -q src scripts` | exit 0 |
| `git -c safe.directory=... diff --check` | exit 0. Git printed a CRLF-to-LF warning for `docs/ai-development-framework.md`; it was not a whitespace error |

After that full run, two additional real-Core cases were added and passed on their own: missing/finance preview, and confirm reevaluation after fixture drift (`2 passed`, 6.32s, `--basetemp=.pytest-tmp/044-sg3`). The 1639 count does not include those two.

The full-suite output did not print the 17 skip reasons (`-q` without `-rs`). Ten of them are the native symlink skips above. The other seven were already represented as `s` outside the new study-guide block.

`.pytest_cache` still cannot be created (`WinError 5`).

## T027 — Separate reviews

### Spec behavior

FR-001–FR-014 and SC-001–SC-005 are covered by the public Core and Tool 26 tests: preview/confirm, conditional ack, derivation refusal, byte preservation, fixed errors, append-only registry, and separate derivation. No spec contradiction found. Native symlink execution was not observed on this machine; the refusal code uses `lstat` and the mocked reparse test passed.

### Engineering and safety boundaries

Core owns the behavior. The MCP module only delegates and maps errors. Tool 26 is imported last inside the facade fence. Tools 1–25 keep their order; Tool 25 is index 24. No `.env` read, no real provider, no download or transcription, no cache rebuild. Result and report keys are unchanged; `planned_reads` now also names the identity JSON. Shared snapshot helpers and `models.py` were not edited.

The review was done in this same writing session, not by a fresh-context reviewer.

## T028 — Converge

Checked the 14 functional requirements, 5 success criteria, the publication/identity state table, and the MCP contract against the code and tests. No remaining in-scope gap required a new task. `tasks.md` was not given a Convergence phase. `.specify/extensions.yml` is absent, so no converge hooks ran.

Checkboxes T001–T028 are marked from this session's evidence.

## Convergence reopened by acceptance — T029–T031

Two P1 gaps contradicted the spec. Phase 7 appended T029–T031. No extension hooks (`.specify/extensions.yml` absent).

| Gap | RED | GREEN |
| --- | --- | --- |
| Copy skipped an entry when its metadata check failed, then published and dropped `extra.bin` | `test_extra_metadata_failure_aborts_publish_and_keeps_directory` did not raise | Raises `unsafe_path`; original directory bytes unchanged; no `.part` or `.old` left |
| Cover `PermissionError` was treated as unreadability, so preview/confirm took the cover-only path | `test_cover_io_error_refuses_instead_of_cover_only` did not raise for preview or confirm | Both modes raise `unsafe_path`; cover bytes unchanged |
| Tool 26 | — | Same injections return `error_type=StudyGuideBundleStateError` and the fixed unsafe-path sentence, with no `boom-extra-meta` or `boom-cover-read` text |

### Verification after the fix

| Command | Result |
| --- | --- |
| Targeted Core/MCP/registry/facade/setup/Tool 25 set, `--basetemp=.pytest-tmp/044-t` | **206 passed, 10 skipped**, exit 0, 154.63s. The 10 skips are symlink creation `OSError`. |
| `.\.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp/44f -q --tb=line` | **1647 passed, 17 skipped**, exit 0, 826.27s |
| `compileall -q src scripts` | exit 0 |
| `git diff --check` | exit 0. CRLF warning on `docs/ai-development-framework.md` only |

`.pytest_cache` still cannot be created (`WinError 5`). No branch, commit, or deployment.

## Phase 8 convergence — directory metadata — T032–T035

`check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` again selected `specs/044-study-guide-mcp`. `.specify/extensions.yml` is still absent, so no converge hooks ran. Phase 7 stayed closed. The new gap is that `_lstat` treated every `OSError` as absence. Inside the publisher, one unreadable `lstat` of an existing destination therefore kept `preserved=[]`, published only the overlay, and deleted `.old`.

| ID | Gap | Severity | Source | Evidence |
| --- | --- | --- | --- | --- |
| F1 | contradicts | CRITICAL | FR-007 / US3 | Publisher treated a failed destination stat as "no directory", then replaced and removed the backup |
| F2 | contradicts | CRITICAL | FR-013 | Recovery siblings, ancestors, and 05/06 used the same absence collapse, so an unreadable stat skipped the refusal |
| F3 | partial | HIGH | FR-014 | Rollback and cleanup decided from swallowed stats. An unreadable backup stat took the success path; a pre-commit status error skipped rollback and still raised `publish_failed` |
| F4 | partial | HIGH | FR-014 | Tool 26 returned `ok: true` for that destination-stat failure |

### RED before the fix

`.\.venv\Scripts\python.exe -m pytest tests/test_study_guide_bundle.py tests/test_mcp_study_guide_bundle.py -k dir_meta -q --tb=line -rs --basetemp=.pytest-tmp/44d`

**18 failed, 1 passed**, exit 1, 17.15s. The passing test was `test_dir_meta_listed_entry_missing_aborts`: a preserved `extra.bin` that raises `FileNotFoundError` at copy time was already refused by `_is_safe_regular_file`. The other failures were the directory-level bug:

| Case | Observed before the fix |
| --- | --- |
| Cover-only, first destination `lstat` inside the publisher | Did not raise. Publication returned success |
| Force generation, same destination stat | Did not raise |
| Four recovery siblings, preview | Did not raise |
| Four recovery siblings, confirm | Reached the provider (`AssertionError: provider`) |
| 05 and 06 metadata during the derivation check | Did not raise |
| Ancestor metadata, preview and confirm | Did not raise |
| Pre-commit failure after `dest.rename(old)`, rollback rename available, status `lstat` injected | Public directory was gone (`FileNotFoundError` on the original path) |
| Same window, rollback rename unavailable | Reason was `publish_failed` (claims restored), not `rollback_failed` |
| Post-commit `lstat` of `.old` | Did not raise |
| Tool 26, cover-only destination stat | `ok: true` with a `data` payload |

### Spec acceptance

FR-007 / US3: an unreadable destination or ancestor is refused before `mkdir`. An entry already listed for preservation still aborts on a later `FileNotFoundError` or other `OSError`. Cover-only and allowed force keep every original filename and its bytes; no `.part` or `.old` is left, and the previous run report bytes stay unchanged.

FR-013: preview and confirm both refuse when any of `.part`, `.old`, `.wfderive.part`, `.wfderive.old` cannot be stat'd, and when 05 or 06 cannot be stat'd at the derivation check. No provider, publisher, or report write runs. `FileNotFoundError` is still absence for a sibling or a derivation file that is not there.

FR-014: after `dest.rename(old)` and before `part.rename(dest)`, rollback is attempted from the `moved` flag. The rename result is the only proof of restore (`publish_failed`). A failed rollback keeps `.old` and `.part` and raises `rollback_failed`, whose message does not say the public bundle was restored. After `part.rename(dest)`, an unreadable backup stat raises `published_cleanup_failed`, leaves the new directory and `.old` in place, and does not roll the new directory back or write a new run report. Tool 26 maps the destination refusal to `error_type=StudyGuideBundleStateError` and the fixed unsafe-path sentence. The JSON does not contain `boom-dest-dir` or `PermissionError`.

Tools 1–25, the public runner signature, the result schema, dependencies, and the report-pair helper were not changed. No cross-process lock was added.

### Engineering and error-handling review

This is a same-session self-review by the writer that implemented the fix. There was no fresh-context reviewer.

`_lstat` now returns `None` only for `FileNotFoundError`. `PermissionError` and every other `OSError` raise `StudyGuideBundleStateError("unsafe_path")` at the preflight and pre-staging call sites. Call sites:

| Call | Missing (`FileNotFoundError`) | Other `OSError` |
| --- | --- | --- |
| Ancestor chain | Stop. A missing component cannot hide a later entry | `unsafe_path` before staging |
| Four recovery siblings | No remnant | `unsafe_path`. Not `recovery_required`, because the remnant was not confirmed |
| Bundle directory and 05/06 | No bundle, or that derivation file is absent | `unsafe_path` before provider |
| Bundle children and preserved names at copy | Refusal. A listed name is not skipped | `unsafe_path` |
| Optional seed/audio and source metadata | Absent optional file, or the existing missing-summary error for the source | `unsafe_path` |
| Publisher destination snapshot, before `mkdir` | New bundle, empty preserve list | `unsafe_path`. No staging, no swap |
| Post-commit backup | Direct `lstat`, not `_lstat`. Confirmed absence means cleanup has nothing to remove | `published_cleanup_failed`. The new directory stays |

Publication phase is the flags set by this attempt, not a later stat:

- Before `dest.rename(old)`: refusal or `publish_failed`. Original bytes stay. Staging is removed only if this attempt's `mkdir` returned and a follow-up stat shows a normal directory. An unreadable staging directory is left in place; the public directory is not deleted.
- `moved` and not `committed`: `old.rename(dest)` is attempted with no preceding stat. Rename success is required before `publish_failed`. Rename failure raises `rollback_failed` and keeps both recovery directories.
- `committed`: cleanup never renames the new directory back. `FileNotFoundError` on a backup this attempt created is confirmed absence. Any other stat failure, a non-directory, or a backup this attempt did not create raises `published_cleanup_failed` and does not delete it.

`_is_readable` already separated `FileNotFoundError` from other read errors and was left as it was. Seed JSON parsing in the cover renderer still treats a later read error as an empty optional field; that path is not an `_lstat` site and was not part of this directory-metadata failure.

### Verification

| Command | Result |
| --- | --- |
| New tests plus the previous preservation and publication cases, `--basetemp=.pytest-tmp/44e` | **64 passed**, exit 0, 37.63s |
| Targeted Core/MCP/registry/facade/setup/Tool 25 set, `--basetemp=.pytest-tmp/44t -rs` | **225 passed, 10 skipped**, exit 0, 81.43s. All 10 skips are `tests/test_study_guide_bundle.py:709` symlink creation `OSError` |
| `.\.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp/44g -q --tb=line -rs` | **1666 passed, 17 skipped**, exit 0, 558.52s |
| `compileall -q src scripts` | exit 0 |
| `git diff --check` | exit 0. CRLF warning on `docs/ai-development-framework.md` only; this phase did not edit that file |

Full-suite skips, all symlink `OSError`: `test_secure_local_snapshot.py` (3), `test_study_guide_bundle.py:709` (10), `test_verified_research_report_catalog.py` (3), `test_verified_research_report_source_revalidation.py` (1). `.pytest_cache` still cannot be created (`WinError 5`). No branch, commit, deployment, or real provider.

2026-10-04 authorized052 bookkeeping cleanup:spec lifecycle corrected to Implemented,matching35/35completed tasks and existing recorded verification. Current related175passed10native-symlinkskips,exit0,127.04s;no new live provider run or044runtimechange. Historical verification entries preserved.
