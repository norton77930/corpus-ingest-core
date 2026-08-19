# Implementation Plan: Multi-Document Study Guide

**Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

## Summary

Add a dry-run-first Core runner that turns one existing `learning-notes` semantic summary into a four-file study-guide bundle (`00` cover + `03`/`04`/`07`), index it as a single new corpus family, and expose it through a thin CLI. The runner never sends transcript text to an LLM. Principle IV is not amended. MCP stays at 22 tools. gooaye / finance artifacts are refused and left untouched.

## Technical Context

**Language/Version**: Python 3.12 (repo as-is)

**Primary Dependencies**: none new. Reuse `create_provider` → `SemanticSummaryProvider.complete`.

**Storage**: new directory `data/study-guides/` via `storage.STUDY_GUIDES_DIR`; four canonical Markdown files per episode; metadata-only run report under `data/corpus/{podcast_id}/`.

**Testing**: pytest. TDD per slice. Baseline 24 failed / 1628 passed / 14 skipped.

**Target Platform**: Windows first (PowerShell); path helpers already cap slugs.

**Project Type**: library + thin CLI

**Performance Goals**: one confirmed LLM call for `03`/`04`/`07` together; `00` is local and free.

**Constraints**: exact `api_cost_ack` first; dry-run zero-write/zero-LLM; no transcript egress; no MCP; no cache rebuild; no new dependency.

**Scale/Scope**: one episode per invocation; one new family; one new script.

## Constitution Check

- **I Local artifacts**: bundle is derived from the on-disk semantic summary and local seed/audio metadata. Speaker-attributed claims keep timestamps that already exist in that summary.
- **II Thin interfaces**: all behaviour in `src/podcast_ingest_core`; `scripts/run_study_guide_bundle.py` parses, calls, prints metadata-only JSON.
- **III Dry-run first**: `confirm=false` default; plan lists real reads/writes/reuses; no `.part` residue.
- **IV LLM opt-in / secrets**: confirmed `03`/`04`/`07` generation requires exact ack before `create_provider`. Input is the semantic summary's final half (text before `## Chunk Summaries`), never the transcript. `.env` values never appear in stdout or artifacts. **No constitution amendment.**
- **V Evidence separation**: reconstruction and missing support go to 不確定事項. `05`/`06` workflow advice is forbidden unless already present and labelled in the source.
- **VI No investment advice**: `prohibited_advice` on all three generated files. No disclaimer requirement (037 already proved the detector).
- **VII No live market API**: unused.
- **VIII Manual cache rebuild**: warn only; same wording class as `x_video_ingest.CACHE_STALE_WARNING`.
- **IX TDD**: RED then GREEN per slice below.

Post-design re-check: adding `STUDY_GUIDES_DIR` is picked up by the 025 data-dir fixture reflection; adding `study_guide` to the index family tuple is an additive contract and must **not** join `ARTIFACT_LADDER` (009/010 stay unaware).

## Design Decisions

1. **One family, four files, `partial` is not available.** `CorpusArtifactFamilyCounts` only has available / missing / unreadable. Per-episode status may be `partial`; family counts map `partial` → `unreadable` so it cannot fall through the existing `else: available` branch.
2. **Do not import config from `corpus_index`.** gooaye episodes will report `study_guide: missing`. That is honest. Remediation will not try to fill it because `study_guide` is not on `ARTIFACT_LADDER`.
3. **Title provenance follows the canonical transcript title**, via the same helper `canonical_semantic_summary_path` already uses (`semantic_summary_identity`). No third `sorted()[0]` fork.
4. **One `complete()` call, structured JSON out.** Prompts live in a new pure-data module. The provider protocol is not extended: `complete` already exists on `SemanticSummaryProvider`. `summarize_chunk` / `summarize_final` stay unused and unaltered so the five fakes stay unmodified.
5. **Source window is the final summary only.** Split the semantic Markdown on `^##\s+Chunk Summaries\s*$` (same regex `stock_lens_synthesis` uses) and send only the first half. Chunk dumps are not a second transcript.
6. **`00` never justifies an LLM call.** If `03`/`04`/`07` will be reused, confirmed mode writes or reuses `00` deterministically and does not construct a provider.
7. **Atomic bundle replace.** Write four files plus a sibling manifest into a `.part` directory next to the canonical episode directory, fsync, then replace. Failure deletes the `.part` tree. Never leave two files from generation N and two from N+1.
8. **Learning-notes shape is checked twice.** Profile must be `learning-notes`, and the source document must not contain finance section headings (市場觀點 / 台股觀點 / 美股觀點 / 總經觀點 / 業配). Either mismatch refuses before ack-gated provider work on dry-run, and before provider construction on confirm.
9. **Ack order.** `require_exact_api_cost_ack` is the first statement of the confirmed-LLM path, before profile re-read and before `create_provider`. Dry-run does not demand ack.

## Registry Impact

**None.** No MCP tool. `tests/test_mcp_tool_registry_contract.py` and the docs-count checker stay green without modification.

## Project Structure

```text
specs/038-multi-document-study-guide/
src/podcast_ingest_core/storage.py                 (STUDY_GUIDES_DIR + path helper)
src/podcast_ingest_core/errors.py                  (StudyGuideBundleError)
src/podcast_ingest_core/models.py                  (result dataclasses)
src/podcast_ingest_core/study_guide_profiles.py    (new: prompts + heading lists, pure data)
src/podcast_ingest_core/study_guide_bundle.py      (new: core runner)
src/podcast_ingest_core/corpus_index.py            (append study_guide family)
src/podcast_ingest_core/__init__.py                (export runner + error)
scripts/run_study_guide_bundle.py                  (thin CLI)
tests/test_study_guide_bundle.py                   (new)
tests/test_study_guide_profiles.py                 (new)
tests/test_corpus_index.py                         (deliberate missing-family list update)
tests/test_data_dir_fixture_contract.py            (add STUDY_GUIDES_DIR to known set)
tests/test_contracts.py                            (export + signature pin)
docs/verification-matrix.md
specs/README.md
HANDOFF-2026-08-19.md                              (already updated §7)
```

`tests/test_corpus_index.py` already copies `_use_tmp_data_dirs` (allowlisted). New tests MUST use the shared `tmp_data_dirs` fixture.

There is no `scripts/semantic_summarize_episode.py`; the semantic entry remains `scripts/summarize_episode.py --mode semantic`. This runner is a new script because it is a new artifact family, not a summary-mode flag.

## Risks

- **`missing_artifacts` contract on gooaye.** `test_generate_corpus_index_reports_missing_artifact_families` pins the family list. Adding `study_guide` is a deliberate contract update in the same commit, not a silent assertion edit.
- **`partial` falling through to `available`.** `_artifact_family_counts` treats unknown statuses as available. The mapping must be explicit and tested.
- **009/010 accidentally growing a study-guide action.** Mitigation: do not touch `ARTIFACT_LADDER`. A test asserts the ladder tuple is unchanged.
- **Second title provenance.** Paths must use the canonical transcript title, not `episode_ref` as title and not `glob+sorted()[0]`.
- **`complete()` sending more than the summary.** A test captures messages and asserts no transcript segment text and no `## Chunk Summaries` body.
- **Finance heading leakage into 03/04/07.** A fixture finance-shaped summary is refused; a learning-notes fixture that still contains 市場觀點 is refused.
- **Fabricating 05/06.** A fixture summary without operator-tool names must not produce Claude Code / Codex / Copilot / CLAUDE.md / Skill workflow advice.
- **Ack masked by profile errors.** Wrong ack with a finance profile must raise the ack error first on the confirmed-LLM path.

## Verification

Targeted:

```powershell
python -m pytest tests/test_study_guide_profiles.py tests/test_study_guide_bundle.py tests/test_corpus_index.py tests/test_data_dir_fixture_contract.py tests/test_contracts.py tests/test_llm_ack_guard_contracts.py tests/test_llm_cli_no_leak.py tests/test_cache_rebuild_guard.py tests/test_mcp_tool_registry_contract.py tests/test_summary_profiles.py tests/test_semantic_summarizer.py tests/test_corpus_remediation_plan.py -q --tb=short
```

Full:

```powershell
python -m pytest
python -m compileall src scripts
git diff --check
```

Failure set must remain the 24 Hermes tests. A 25th failure is a regression.
