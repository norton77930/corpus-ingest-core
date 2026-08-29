# Tasks: YouTube Video Corpus Ingestion and Source-Type Seam

**Input**: Design documents from `specs/039-youtube-video-corpus-ingestion/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md
**TDD**: RED before GREEN on every behaviour slice.
**Status**: Implemented (unit/integration verified; live YouTube confirm not run).

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C4 YouTube dry-run / confirm | `tests/test_youtube_video_ingest.py` |
| C5 X acquire still green | `tests/test_x_video_ingest.py` |
| C6 Seam blocked-not-ready | `tests/test_source_type_seam.py` |
| C7 011 seed/index title | `tests/test_corpus_local_transcription_runner.py` |
| C8 Episode-ref `_` single-sourced | `tests/test_episode_ref_predicate.py` |
| C9 Registry exact 22 | `tests/test_mcp_tool_registry_contract.py` unmodified |
| C10 Full verify | pytest / compileall / diff-check; Hermes 24 remain allowed |

Non-goals: MCP, playlists, cookies, `--podcast` override, 012-as-ingest, leftover trio delete, `source_type` enum, 038 study-guide files, commits.

## Phase 1: Setup

- [x] T001 Add a verification-matrix row for Spec 039 in `docs/verification-matrix.md`
- [x] T002 [P] Add a YouTube / seam paragraph in `docs/architecture.md` (append; do not rewrite pinned 036 sentences)

---

## Phase 2: Foundational

**Purpose**: Identity predicate, shared acquire, types. Blocks all user stories.

- [x] T003 RED `tests/test_episode_ref_predicate.py`: `storage.is_safe_episode_ref` accepts `dQw4w9WgXcQ` and an id containing `_`; rejects `.`, `/`, space; existing hyphenated refs still pass
- [x] T004 GREEN public `is_safe_episode_ref` in `src/corpus_ingest_core/storage.py`; alphabet `^[A-Za-z0-9][A-Za-z0-9_-]*$`; error text includes `與 _`
- [x] T005 RED same test file: no `src/` module other than `storage.py` may define the old episode-ref alphabet `^[A-Za-z0-9][A-Za-z0-9-]*$` or `^[A-Za-z0-9][A-Za-z0-9-]{0,127}$` (016 `_SAFE_IDENTIFIER_PATTERN` already allows `._-` and is exempt)
- [x] T006 GREEN switch episode-ref copies to `storage.is_safe_episode_ref` plus a local length cap in `src/corpus_ingest_core/episode_claim.py`, `corpus_episode_workflow_runner.py`, `corpus_semantic_remediation_runner.py`, `corpus_latest_episode_deterministic_workflow_runner.py`, `latest_episode_verified_research_report_workflow_runner.py`, `mcp_episode_verified_research_report.py`, `mcp_tools_corpus_workflows.py`, `historical_verified_report_path.py`; catalog/revalidation already call storage
- [x] T007 RED/GREEN `YoutubeVideoIngestDependencyError`, `YoutubeVideoIngestFailedError` in `src/corpus_ingest_core/errors.py` and `YoutubeVideoIdentity` / `YoutubeVideoIngestResult` in `src/corpus_ingest_core/models.py`; add `VIDEO_SEED_SOURCES = frozenset({"x-video", "yt-video"})` next to the ingest package (one definition)
- [x] T008 Confirm `tests/test_x_video_ingest.py` is green before the extract (characterisation, not a new RED)
- [x] T009 GREEN lift metadata/download/extract into `src/corpus_ingest_core/video_acquire.py` and `tests/test_video_acquire.py`; pin that acquire options have no `cookiefile` / username / password (FR-020); `src/corpus_ingest_core/x_video_ingest.py` calls it; rerun `tests/test_x_video_ingest.py`

**Checkpoint**: `_` is legal; X acquire behaviour frozen.

---

## Phase 3: User Story 2 — Dry-run (P1)

**Goal**: Plan a YouTube ingest without writing.

**Independent Test**: Fake metadata; `confirm=false` returns identifiers and planned paths; `data/` tree unchanged.

- [x] T010 [US2] RED `tests/test_youtube_video_ingest.py`: `derive_youtube_identity` accepts watch / `youtu.be` / shorts / embed / live / `m.youtube.com` / `music.youtube.com`; canonical URL is `https://www.youtube.com/watch?v={id}`; playlist-without-id raises; video id with `_` is kept; handle `@Foo.Bar` becomes `yt-foo-bar`; title path does not strip `{uploader} - ` (FR-007, FR-008)
- [x] T011 [US2] RED dry-run calls metadata only, lists planned writes, writes zero files (including no `.part`)
- [x] T012 [US2] RED existing WAV makes the plan say reuse, not rewrite
- [x] T013 [US2] GREEN dry-run path in `src/corpus_ingest_core/youtube_video_ingest.py`

**Checkpoint**: US2 independently testable.

---

## Phase 4: User Story 1 — Confirm ingest (P1)

**Goal**: One public URL becomes seed + WAV + transcript trio.

**Independent Test**: Faked yt-dlp/av/transcribe; confirm writes storage-derived paths; no video under `data/`.

- [x] T014 [US1] RED confirm writes seed (`seed_source=yt-video`), WAV, trio; source video not under `data/`; cache-stale warning present; no cache rebuild; a sibling podcast_id tree is unchanged (FR-021)
- [x] T015 [US1] RED missing profile and wrong `source_type` refuse on confirm before `acquire_wav`; dry-run only warns
- [x] T016 [US1] GREEN confirm path reuses `transcribe_episode(..., audio_path=..., title=...)` in `src/corpus_ingest_core/youtube_video_ingest.py`
- [x] T017 [US1] Thin CLI `scripts/run_youtube_video_ingest.py` + metadata-only stdout; export runner/errors from `src/corpus_ingest_core/__init__.py`

**Checkpoint**: US1 + US2 work with fakes.

---

## Phase 5: User Story 3 — Source-type seam (P1)

**Goal**: Video missing-audio is not a ready RSS download.

**Independent Test**: Fixture x-video and yt-video seeds without audio; 009 blocked; 012/014 do not call `download_audio`.

- [x] T018 [US3] RED `tests/test_source_type_seam.py`: x-video and yt-video missing audio → status `blocked`, blocker `source_ingest`, suggested command is the matching ingest CLI plus seed selector
- [x] T019 [US3] RED RSS `has_audio_url=false` still `feed_audio_url`; RSS `has_audio_url=true` still `ready` + `download_episode.py` in `tests/test_corpus_remediation_plan.py`
- [x] T020 [US3] GREEN seed-source-aware `_suggested_command` / blocker in `src/corpus_ingest_core/corpus_remediation_plan.py` using `VIDEO_SEED_SOURCES`
- [x] T021 [US3] RED `run_corpus_audio_download` refuses a video-seed audio action and does not call `download_audio` in `tests/test_corpus_audio_download_runner.py` or `tests/test_source_type_seam.py`
- [x] T022 [US3] GREEN refuse in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [x] T023 [US3] RED 014 / 016 / 017 do not dispatch 012 when next audio is a video seed (`tests/test_corpus_episode_workflow_runner.py` plus targeted cases in `tests/test_source_type_seam.py`; add fixtures, do not rewrite RSS snapshots)
- [x] T024 [US3] GREEN refuse/skip in `src/corpus_ingest_core/corpus_episode_workflow_runner.py`, `corpus_episode_completion_workflow_runner.py`, `corpus_latest_episode_deterministic_workflow_runner.py`

**Checkpoint**: Seam tells the truth for X and YouTube.

---

## Phase 6: User Story 4 — Title provenance (P1)

**Goal**: Re-transcribe uses seed/index title.

**Independent Test**: Seed titled `Real Title`; 011 planned writes and outputs are `{ref}__real_title.*`.

- [x] T025 [US4] RED planned writes in `tests/test_corpus_local_transcription_runner.py` use plan/index title, not `episode_ref`
- [x] T026 [US4] RED confirmed transcription writes those paths and does not create `{ref}__{ref}.*`
- [x] T027 [US4] GREEN pass plan episode title into `transcribe_episode` and `_planned_transcript_writes` in `src/corpus_ingest_core/corpus_local_transcription_runner.py`

**Checkpoint**: One title per episode on the audio-path branch.

---

## Phase 7: User Story 5 — First-class YouTube source (P2)

**Goal**: Registration and RSS refusal name the YouTube path.

**Independent Test**: `yt-video` profile without `rss_url` loads; RSS surfaces refuse it; YouTube ingest refuses rss/x-video.

- [x] T028 [US5] RED `tests/test_podcast_profile_source_type.py`: `source_type: yt-video` without `rss_url` loads; `language` required; gooaye still defaults to `rss`
- [x] T029 [US5] RED `tests/test_feed_reader.py` / `tests/test_downloader.py`: `UnsupportedSourceTypeError` for a `yt-video` fixture names `yt-video` and `run_youtube_video_ingest`
- [x] T030 [US5] RED YouTube ingest of an `x-video` or `rss` profile with the derived id refuses before download (covered in `tests/test_youtube_video_ingest.py`)
- [x] T031 [US5] GREEN `src/corpus_ingest_core/config.py` RSS refusal names the YouTube ingest path when `source_type == yt-video`; YouTube registration check already in T015/T016

**Checkpoint**: Discriminant enforced on both surfaces.

---

## Phase 8: Polish

- [x] T032 Pin `run_youtube_video_ingest` export and signature in `tests/test_contracts.py`
- [x] T033 [P] Docs already started in T001/T002; confirm `specs/README.md` 039 line still matches shipped behaviour
- [x] T034 `python -m pytest tests/test_mcp_tool_registry_contract.py -q` stays green without editing that file
- [x] T035 Run `python -m pytest tests/test_youtube_video_ingest.py tests/test_video_acquire.py tests/test_source_type_seam.py tests/test_episode_ref_predicate.py tests/test_x_video_ingest.py tests/test_corpus_remediation_plan.py tests/test_corpus_audio_download_runner.py tests/test_corpus_local_transcription_runner.py tests/test_corpus_episode_workflow_runner.py tests/test_podcast_profile_source_type.py tests/test_contracts.py tests/test_mcp_tool_registry_contract.py -q` then `python -m pytest -q --tb=no -ra`, `python -m compileall src scripts`, `git diff --check`

---

## Dependencies

- Phase 1 → Phase 2 → US2 → US1 → US3 / US4 (US4 does not need YouTube confirm) → US5 → Polish
- US3 can start after Phase 2 even before US1 if `VIDEO_SEED_SOURCES` exists
- US4 only needs Phase 2 + 011; it does not depend on YouTube ingest
- One writer: sequential TDD

## Parallel (not used — one writer)

T001/T002 are independent. T010–T012 RED tests can be drafted together before T013.

## MVP

Phase 1 + 2 + US2 + US1. Seam (US3) and title (US4) ship in the same package because 036 named them as this spec's job.

## Notes

- Fake yt-dlp/av at the `video_acquire` seam. No live network in tests. No `.env`.
- Do not edit `study_guide_*` or 038 runtime.
- Do not add a committed YouTube profile.
- Do not create commits or branches.
