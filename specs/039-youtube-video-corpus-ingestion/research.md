# Research: YouTube Video Corpus Ingestion and Source-Type Seam

## Decision: YouTube is a new surface on the 036 acquire stack

- **Decision**: Extract shared video acquire (metadata resolve, guest download, 16 kHz mono WAV extract) and add `youtube_video_ingest` as an X-shaped surface. Do not copy `x_video_ingest.py` wholesale and do not teach that module a second source type.
- **Rationale**: 036 already proved the cheap route. The architecture review said URL-driven ingest belongs outside the `corpus_*_runner` family. A third source that duplicates yt-dlp / PyAV would fork bugfixes (merged-filename resolution, `.part` cleanup, no video under `data/`).
- **Alternatives considered**: (1) `run_x_video_ingest` grows a URL switch — rejected, name and `X_SOURCE_TYPE` check would lie. (2) Fold YouTube into `corpus_audio_download_runner` — rejected by the 036 review. (3) Parallel producer that writes its own transcript trio — rejected, private writers stay private.

## Decision: discriminant for the seam is `seed_source`, not profile `source_type`

- **Decision**: 009 / 012 / 014 / 016 / 017 read `source_metadata.episode_seed.seed_source` and `selector` from the index projection. `corpus_index` does not import config.
- **Rationale**: 038 already recorded that importing config from the index would make gooaye look like it owes a `study_guide`. The index already echoes `seed_source` / `selector` / `title`. Profile `source_type` remains the ingest-surface check (X and YouTube each refuse the wrong profile).
- **Alternatives considered**: (1) Add `source_type` onto every index row from `load_podcast_profile` — rejected, breaks the config-free index. (2) Infer source from `podcast_id` prefix `x-` / `yt-` — rejected, prefixes are conventions, not a contract.

## Decision: missing audio on a video seed is blocked for RSS download

- **Decision**: For `seed_source` in `{x-video, yt-video}`, a missing/unreadable audio artifact is `blocked` with blocker `source_ingest` (or equivalent named blocker), reason naming the ingest path, `suggested_command` = matching ingest CLI plus `--url {selector}`. RSS `has_audio_url=false` stays the existing `feed_audio_url` blocker. RSS `has_audio_url=true` stays `ready` + `download_episode.py`.
- **Rationale**: Today's X seed sets `has_audio_url=true`, so 009 emits `ready` + `download_episode.py`, and 012 then fail-softs on `UnsupportedSourceTypeError`. A plan that names a command that cannot work is the 036 dry-run-lie class of defect. Blocking the RSS action tells the truth without pulling URL-driven ingest into the runner family.
- **Alternatives considered**: (1) Keep `ready` but change only `suggested_command` — 014/016/017 would still dispatch 012. (2) New action family `source_ingest` on `ARTIFACT_LADDER` — larger than needed; ingest is not podcast-scoped. (3) Have 012 call ingest — rejected, ingest needs a URL and a different dry-run (network metadata).

## Decision: expand episode-ref to allow `_`, single-sourced from storage

- **Decision**: `storage` gains a public `is_safe_episode_ref` (or equivalent) whose alphabet is `A-Za-z0-9_-`. Duplicate regexes in 014 / 015 / 017 / 018 / 019 / 023 / `episode_claim` / MCP wrappers call that predicate. Do not map `_` to `-`.
- **Rationale**: YouTube video ids are 11 characters from `A-Za-z0-9_-`. Mapping `_` to `-` collides. `_` is not a path separator and is legal on Windows and POSIX. Leaving the copies unsynced would accept an id at ingest and reject it at 014/015/018.
- **Alternatives considered**: (1) Refuse ids containing `_` unless the operator supplies `--episode-ref` — rejected, `--episode-ref` is out of v1 and most ids would fail closed. (2) Expand only `storage._SAFE_EPISODE_REF_PATTERN` — rejected, the copies would still reject. (3) Base32-encode every YouTube id — rejected, operator-hostile and splits from the public video id.

## Decision: 011 takes title from the plan episode row

- **Decision**: `corpus_local_transcription_runner` uses `episode_payload["title"]` (009 already copies index title: transcript title else seed title else `episode_ref`) for `transcribe_episode(..., title=)` and for `_planned_transcript_writes`. It does not parse filenames and does not call `sorted()[0]`.
- **Rationale**: A third title algorithm would be a third fork. The seed is already the external selector in `canonical_transcript._trusted_seed_title`. Index title is that value when no transcript exists — exactly the first-transcription case that today writes `{ref}__{ref}.*`.
- **Alternatives considered**: (1) Change `transcribe_episode` default title from `episode_ref` to seed lookup — rejected, 036 required omit-`title` to stay byte-identical. (2) Teach 011 to read the seed file itself — redundant with the plan row.

## Decision: no new dependency, no MCP, no committed YouTube profile

- **Decision**: Reuse `yt-dlp` and `av`. Registry stays at 22. Tests use fixture profiles; operators add a real `yt-…` entry locally before a live confirm.
- **Rationale**: 004 → 035 and 036 already separated Core/CLI from MCP blast radius. A committed channel would pick a winner the user has not named.
- **Alternatives considered**: Tool 23 in this spec — rejected (040 is the X-ingest MCP candidate). Adding a sample YouTube channel to `config/podcasts.yaml` — deferred until a live confirm target is chosen.

## Decision: YouTube title normalisation is not the X title strip

- **Decision**: Collapse whitespace, honour `--title`, cap via `title_slug`. Do not strip `{uploader} - ` or a trailing ellipsis.
- **Rationale**: yt-dlp's YouTube `title` is usually a real title. The X strip exists because X titles are truncated post text. Applying it to YouTube would delete legitimate titles that start with the channel name.
- **Alternatives considered**: Share `_resolve_title` with X unchanged — rejected, X-specific.

## Open items carried out of v1

- MCP dry-run wording for a future tool (zero-write ≠ zero-network).
- Leftover `{ref}__{ref}.*` cleanup after the title fix.
- Closed `source_type` enum at profile load (037 left this).
