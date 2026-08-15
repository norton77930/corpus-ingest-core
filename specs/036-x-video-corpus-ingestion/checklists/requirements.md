# Requirements Checklist: X Video Corpus Ingestion

Unchecked — v1 is not implemented. One box per FR group in `spec.md`.

## Acquisition

- [ ] FR-001 Metadata resolved via `yt-dlp --write-info-json`: title, upload date,
      duration, canonical status URL
- [ ] FR-002 Video downloaded with a guest token; mono 16 kHz WAV extracted with
      PyAV to `storage.audio_asset_path(...)`
- [ ] FR-003 Source video written outside `data/`
- [ ] FR-004 Seed written with `seed_source="x-video"`, canonical URL as
      `selector`, `published_at` from the upload date

## Reuse

- [ ] FR-005 Transcription reuses `transcribe_episode(..., audio_path=...)`; no new
      transcription, SRT-formatting, or transcript-writing code
- [ ] FR-006 Optional `title` names the trio by title; omitting it preserves
      current behaviour exactly
- [ ] FR-007 Segments carry exactly `id`/`start`/`end`/`text`, asserted by test

## Source registration

- [ ] FR-008 `PodcastProfile.source_type` defaults to `"rss"`; RSS-only fields
      optional for non-RSS; `language` required for every source
- [ ] FR-009 Existing profiles without `source_type` parse and behave identically
- [ ] FR-010 `list_episodes` / `get_episode` / `download_audio` refuse a non-RSS
      source with a source-aware message, not a bare `KeyError`

## Identity and defaults

- [ ] FR-011 `episode_ref` defaults to the tweet status id; `podcast_id` to a
      per-account slug; both validated by the existing patterns
- [ ] FR-012 `title` defaults to yt-dlp metadata, whitespace-collapsed,
      operator-overridable, capped by `storage.title_slug`

## Grouping

- [ ] FR-013 `group_segments()` ported as a pure function; not persisted anywhere

## Boundaries

- [ ] FR-014 `confirm=false` returns a plan from metadata resolution alone
- [ ] FR-015 No cache rebuild; response states the episode is not yet searchable
- [ ] FR-016 No credentials accepted, prompted for, or stored
- [ ] FR-017 No other `podcast_id`'s artifacts modified
- [ ] FR-018 `yt-dlp` and `av` declared; no other new runtime dependency
