# Implementation Plan: X Video Corpus Ingestion

**Date**: 2026-08-15 | **Spec**: [spec.md](spec.md)

## Summary

Add X videos as a corpus source by writing only the acquisition step. yt-dlp
resolves metadata and downloads the video, PyAV extracts a mono 16 kHz WAV into
`data/audio/{podcast_id}/`, and the existing `transcribe_episode(..., audio_path=...)`
does everything after that. Non-RSS sources become explicit through a
`source_type` field on `PodcastProfile`. v1 is Core plus a thin CLI; no MCP tool.

## Constitution Check

Local artifacts with preserved segment timestamps (I); runtime in
`src/podcast_ingest_core` behind a thin CLI (II); dry-run-first with a `confirm`
gate (III); no LLM, no `api_cost_ack`, no `.env`, no credentials — yt-dlp uses a
guest token only (IV); the prototype's `[不確定：<guess>]` marking for unclear
audio is retained, keeping evidence separate from inference (V); no investment
advice and no market data involved (VI, VII); no automatic cache rebuild (VIII);
TDD with targeted tests before implementation (IX). **No constitution amendment.**

Two contract touches are additive and backward-compatible, and are the parts
worth reviewing rather than assuming: `PodcastProfile` gains `source_type` with
a `"rss"` default, and `transcribe_episode` gains an optional keyword-only
`title`. Existing profiles and existing calls MUST behave identically.

## Design Decisions

1. **Reuse the transcription path instead of building a producer.** The seam
   trial on 2026-08-15 shaped a transcript by hand and proved the corpus contract
   accepts it, but it needed `transcriber`'s private writers to do so. The
   cheaper route found during clarify: `transcribe_episode` already takes
   `audio_path`, which skips `download_audio` entirely, and its profile lookup
   feeds exactly one value — `profile.language`. So acquisition is the only new
   capability, and the private writers stay private.
2. **`source_type` on the profile, not a parallel registry.** `rss_url` and
   `default_episode_prefix` are consumed only by `feed_reader.py`, so they can
   become optional for non-RSS sources without touching any other consumer.
   `language` stays required precisely because transcription needs it.
3. **Audio is a corpus artifact; the video is not.** Only the extracted WAV is
   written under `data/`; the 260 MB source video stays outside. `.wav` is
   already in `corpus_index._AUDIO_SUFFIXES`, so the `audio` family lights up
   with no index change — closing the one gap the trial left open.
4. **Groups are computed, never stored.** `group_segments()` is a pure function
   of the segments. Persisting it would add a field no validator protects and
   that RSS episodes would not have. A sidecar is not an option either: a
   `{episode_ref}__*.json` file under `data/transcripts/` is selected as the
   canonical transcript by `storage.find_transcript_asset_paths`.
5. **No MCP tool in v1.** The registry count is a pinned chain — the Hermes AST
   projection, the Spec 029 descriptor snapshot, the deny adapter, and the
   docs-count checker all move together, as Spec 035 documented. This repo's own
   precedent separates the two: Spec 004 built the stock lens Core and CLI, and
   Spec 035 exposed it as Tool 22 later. Exposure gets its own successor spec.
6. **Metadata resolution is separable from download**, which is what makes a
   real dry-run possible: `yt-dlp --skip-download --write-info-json` yields
   title, upload date, and duration without spending the download or the
   transcription.

## Registry Impact

**None.** v1 adds no MCP tool; the registry stays at exactly 22 with Tools 1-22
unchanged in name, order, signature, and defaults. `tests/test_mcp_tool_registry_contract.py`
and the docs-count checker must stay green without modification — if either
needs editing, the change has drifted out of scope.

## Project Structure

```text
specs/036-x-video-corpus-ingestion/
src/podcast_ingest_core/x_video_ingest.py     (new: metadata resolve, download, extract, orchestrate)
src/podcast_ingest_core/segment_grouping.py   (new: ported group_segments, pure)
src/podcast_ingest_core/models.py             (PodcastProfile.source_type; rss fields optional)
src/podcast_ingest_core/config.py             (_parse_profile becomes source-aware)
src/podcast_ingest_core/feed_reader.py        (source-aware refusal for non-RSS)
src/podcast_ingest_core/downloader.py         (source-aware refusal for non-RSS)
src/podcast_ingest_core/transcriber.py        (optional title through the audio_path branch)
config/podcasts.yaml                          (x-raytar profile, source_type: x-video)
pyproject.toml                                (yt-dlp, av)
scripts/run_x_video_ingest.py                 (thin CLI, dry-run first)
tests/test_x_video_ingest.py, tests/test_segment_grouping.py,
tests/test_podcast_profile_source_type.py,
tests/test_transcriber.py, tests/test_feed_reader.py, tests/test_downloader.py,
tests/test_contracts.py                       (two pinned contracts — see below)
docs/architecture.md, docs/verification-matrix.md, specs/README.md
```

`tests/test_contracts.py` was missed in the first draft of this plan and added by
the analyze pass. It pins two things this feature necessarily moves:
`assert set(profiles) == {"gooaye"}` (breaks when `x-raytar` is registered) and
`transcribe_episode`'s exact parameter list by `inspect.signature` (breaks when
`title` is added). Both are deliberate contract updates, not collateral damage,
and both must land in the same commit as the change that moves them.

## Risks

- **Network dependence in tests.** yt-dlp must be faked at the seam; no test may
  reach x.com. The acquisition module needs a boundary thin enough to stub.
- **PyAV on Windows.** Wheel availability and the WAV extraction path are the
  most likely install-time friction; the prototype proves it works on this
  machine, not that it works everywhere.
- **Regression surface on `transcribe_episode`.** The title change touches the
  function every RSS episode uses. Byte-for-byte output equality for an existing
  episode is the gate, not "tests pass". Analyze lowered this from high to
  moderate: `tests/test_transcriber.py:317` already covers the `audio_path`
  branch and asserts it does not download, so the change extends a real test
  instead of landing uncovered.
- **Behaviour change on a shipped MCP tool.** The non-RSS guard on
  `download_audio` reaches Tool 3 through `mcp_tools_side_effect.py:87`, and the
  `get_episode` guard reaches the RSS seed bootstrap at
  `corpus_episode_intake.py:58`. Both refusals are correct, neither changes a
  signature or the registry count, but they are runtime behaviour changes on
  shipped surfaces and must be called out rather than discovered.

## Verification

```powershell
python -m pytest tests/test_x_video_ingest.py tests/test_segment_grouping.py tests/test_podcast_profile_source_type.py -q
python -m pytest tests/test_transcriber.py tests/test_feed_reader.py tests/test_downloader.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest -q --tb=no -ra
python -m compileall src scripts
```

End-to-end acceptance, run once against a real X URL after the unit gates pass:

```powershell
python scripts/run_x_video_ingest.py --url <x-status-url>                  # dry-run: plan only, zero writes
python scripts/run_x_video_ingest.py --url <x-status-url> --confirm
python scripts/validate_transcript.py --podcast <id> --episode <status-id> # expect status=valid
python scripts/generate_corpus_index.py --podcast <id>                     # expect audio AND transcript available
python scripts/rebuild_cache.py --podcast <id>
python scripts/search_transcripts.py --query <spoken-phrase> --podcast <id>
python scripts/search_transcripts.py --query 台積電 --podcast gooaye        # unchanged from baseline
```
