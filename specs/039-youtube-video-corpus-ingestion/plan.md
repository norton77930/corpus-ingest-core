# Implementation Plan: YouTube Video Corpus Ingestion and Source-Type Seam

**Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

## Summary

Add YouTube as a third corpus source by reusing Spec 036's acquire stack, and close the `source_type` seam Spec 036 left in index → plan → runner. A YouTube URL becomes a `yt-video` seed plus WAV plus transcript trio. Missing audio on `x-video` / `yt-video` seeds is no longer a `ready` RSS download. Re-transcription uses the seed/index title. No MCP tool. No new dependency. No constitution amendment.

## Technical Context

**Language/Version**: Python 3.12 (repo as-is)

**Primary Dependencies**: none new. Reuse `yt-dlp` and `av`.

**Storage**: existing `data/audio/`, `data/transcripts/`, `data/corpus/{id}/episode-seeds/`. No new family. Episode-ref alphabet gains `_`.

**Testing**: pytest. TDD per slice. Baseline 24 failed / 1628 passed / 14 skipped (038 may have added tests in the working tree; the Hermes 24 stay the allowed failures).

**Target Platform**: Windows first (PowerShell); path helpers already cap slugs.

**Project Type**: library + thin CLI

**Performance Goals**: one confirmed download + one local transcription per video; dry-run is metadata only.

**Constraints**: dry-run zero-write (not zero-network); guest token only; no LLM / ack / `.env`; no MCP; no cache rebuild; index stays config-free.

**Scale/Scope**: one URL per invocation; one new ingest surface; seam readers in 009 / 011 / 012 / 014 / 016 / 017; identity predicate consolidation.

## Constitution Check

- **I Local artifacts**: WAV, seed, and transcript trio at storage-derived paths; video never lands under `data/`.
- **II Thin interfaces**: behaviour in `src/podcast_ingest_core`; `scripts/run_youtube_video_ingest.py` parses, calls, prints metadata-only JSON.
- **III Dry-run first**: `confirm=false` default; plan lists real identifiers and writes/reuses; no `.part` residue; a reuse must say reuse.
- **IV LLM opt-in / secrets**: unused. No `.env`. Guest token only.
- **V Evidence separation**: `[不確定：<guess>]` remains the transcriber's convention; this spec does not invent market facts.
- **VI No investment advice**: unused on this path; existing review guards stay in place for later summarisation.
- **VII No live market API**: unused.
- **VIII Manual cache rebuild**: warn only; same wording class as `x_video_ingest.CACHE_STALE_WARNING`.
- **IX TDD**: RED then GREEN per slice below.

Post-design re-check: expanding episode-ref is an additive identity contract, not a constitution change. Blocking video-source audio actions changes 009 output for those episodes only; RSS fixtures must stay byte-stable. Extracting shared acquire from `x_video_ingest` is behaviour-frozen for X: existing `tests/test_x_video_ingest.py` stay green without rewriting expectations.

No constitution violations. Complexity table not used.

## Design Decisions

1. **Shared `video_acquire` module.** Lift `_resolve_metadata`, `_download_video`, `_downloaded_path`, `_extract_audio`, `_write_resampled` out of `x_video_ingest.py`. X and YouTube own identity, seed, title, and `source_type` registration. X tests pin behaviour, not file location of the helpers.
2. **`seed_source` is the seam discriminant.** Closed reader set `{x-video, yt-video}`. Index unchanged except tests that prove it still echoes those fields without importing config.
3. **009 blocks RSS download for video seeds.** New blocker name `source_ingest`. `suggested_command` uses the seed `selector`. `_suggested_command` therefore needs `source_metadata`, not only `(podcast_id, episode_ref, family)`.
4. **012 / 014 / 016 / 017 refuse, they do not ingest.** Defense in depth if a stale plan still says `ready`.
5. **011 uses plan episode title.** One line of title authority. `transcribe_episode` omit-`title` stays frozen.
6. **`storage.is_safe_episode_ref` is the single predicate.** Alphabet `^[A-Za-z0-9][A-Za-z0-9_-]*$`. Error text gains `與 _`. Callers listed in Project Structure switch to the helper. Length-capped copies (`{0,127}`) keep their length check **after** the shared alphabet check.
7. **No MCP. No new dependency. No committed YouTube profile.**

## Registry Impact

**None.** No MCP tool. `tests/test_mcp_tool_registry_contract.py` and the docs-count checker stay green without modification.

## Project Structure

```text
specs/039-youtube-video-corpus-ingestion/
src/podcast_ingest_core/video_acquire.py          (new: shared metadata/download/extract)
src/podcast_ingest_core/youtube_video_ingest.py   (new: identity, seed, orchestrate)
src/podcast_ingest_core/x_video_ingest.py         (call video_acquire; behaviour frozen)
src/podcast_ingest_core/storage.py                (public is_safe_episode_ref; allow _)
src/podcast_ingest_core/errors.py                 (YoutubeVideoIngest* errors)
src/podcast_ingest_core/models.py                 (YoutubeVideoIngestResult)
src/podcast_ingest_core/__init__.py               (export runner + errors)
src/podcast_ingest_core/config.py                 (RSS refusal names YouTube ingest path)
src/podcast_ingest_core/corpus_remediation_plan.py
src/podcast_ingest_core/corpus_audio_download_runner.py
src/podcast_ingest_core/corpus_local_transcription_runner.py
src/podcast_ingest_core/corpus_episode_workflow_runner.py
src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py
src/podcast_ingest_core/corpus_latest_episode_deterministic_workflow_runner.py
src/podcast_ingest_core/episode_claim.py
src/podcast_ingest_core/corpus_semantic_remediation_runner.py
src/podcast_ingest_core/latest_episode_verified_research_report_workflow_runner.py
src/podcast_ingest_core/mcp_episode_verified_research_report.py
src/podcast_ingest_core/mcp_tools_corpus_workflows.py
src/podcast_ingest_core/historical_verified_report_path.py
scripts/run_youtube_video_ingest.py
tests/test_youtube_video_ingest.py                (new)
tests/test_video_acquire.py                       (new; fakes yt-dlp/av)
tests/test_source_type_seam.py                    (new; 009/012/014 video-seed matrix)
tests/test_corpus_local_transcription_runner.py   (title provenance)
tests/test_corpus_remediation_plan.py             (RSS unchanged; video blocked)
tests/test_x_video_ingest.py                      (still green after extract)
tests/test_podcast_profile_source_type.py
tests/test_storage.py or test_contracts.py        (episode-ref _ accepted)
docs/verification-matrix.md
docs/architecture.md
specs/README.md
```

## Implementation Slices (for `$speckit-tasks`, not implemented here)

1. **Identity predicate** — RED: `_` accepted by `storage` and one workflow copy; GREEN: public helper + callers.
2. **`video_acquire` extract** — RED not required if characterisation tests already cover X download/extract; GREEN must keep `test_x_video_ingest.py` green.
3. **YouTube ingest** — RED dry-run / confirm / registration / URL forms / no video under `data/`; GREEN new module + thin CLI.
4. **Seam** — RED x-video and yt-video missing audio are not `ready` for `download_episode.py`; 012/014 refuse; RSS fixtures unchanged; GREEN 009/012/014/016/017.
5. **Title provenance** — RED 011 planned writes and confirm use seed title; GREEN pass plan title through.
6. **Docs + registry pin** — verification-matrix row; architecture paragraph; README package line; MCP still 22.

## Risks

- **Episode-ref expansion blast radius.** Many copies exist. Missing one leaves a YouTube id working in ingest and failing later. Mitigation: grep-backed test that no second alphabet regex remains in `src/`.
- **009 output change on existing X episodes.** Any test that snapshots a full x-raytar plan will move. Mitigation: targeted assertions on the audio action only; do not rewrite RSS snapshots.
- **`video_acquire` extract regresses X.** Mitigation: do not change X options, guest-token policy, or filename resolution; run `test_x_video_ingest.py` in the same slice.
- **014/016/017 in-memory fixtures** often hardcode `seed_source: rss`. Video-seed cases need new fixtures, not edits to RSS ones.
- **038 uncommitted work** is in the same tree. This package must not edit study-guide runtime files.

## Verification

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/039-youtube-video-corpus-ingestion"
python -m pytest tests/test_youtube_video_ingest.py tests/test_video_acquire.py tests/test_source_type_seam.py -q
python -m pytest tests/test_x_video_ingest.py tests/test_corpus_remediation_plan.py tests/test_corpus_audio_download_runner.py tests/test_corpus_local_transcription_runner.py tests/test_corpus_episode_workflow_runner.py -q
python -m pytest tests/test_mcp_tool_registry_contract.py tests/test_contracts.py tests/test_podcast_profile_source_type.py -q
python -m pytest -q --tb=no -ra
python -m compileall src scripts
```

End-to-end acceptance, run once against a real public YouTube URL after the unit gates pass and the operator names the channel / registers `yt-…`:

```powershell
python scripts/run_youtube_video_ingest.py --url <youtube-watch-url>
python scripts/run_youtube_video_ingest.py --url <youtube-watch-url> --confirm
python scripts/validate_transcript.py --podcast <yt-id> --episode <video-id>
python scripts/generate_corpus_index.py --podcast <yt-id>
python scripts/generate_corpus_remediation_plan.py --podcast x-raytar
python scripts/rebuild_cache.py --podcast <yt-id>
```

The x-raytar plan must not suggest `download_episode.py` for a missing-audio X row. gooaye's index file must be unchanged.

## Next

`$speckit-checklist` then `$speckit-tasks`. Do not implement from this plan until those exist, unless the operator explicitly skips them.
