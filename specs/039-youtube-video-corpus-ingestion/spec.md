# Feature Specification: YouTube Video Corpus Ingestion and Source-Type Seam

**Feature Branch**: `039-youtube-video-corpus-ingestion`

**Created**: 2026-08-19

**Status**: Implemented and live-confirmed (2026-08-22 — see Live Confirm Record)

**Input**: Spec 036 added X videos as a second corpus source and left two named follow-ups for the next source spec: `source_type` does not travel through corpus index → remediation plan → runner, and re-transcription can fork one episode onto `{ref}__{ref}.*` because the local transcription runner never passes the seed title. Task B in `HANDOFF-2026-08-19.md` asks for YouTube as the third source **and** those two closures in the same package, because a third source without the seam closed triples the operator confusion.

## Clarifications

### Session 2026-08-19 (planning defaults)

These defaults follow Spec 036's clarify answers and the 036 architecture review. Correct them before `$speckit-tasks` / implement if any is wrong.

- Q: One `podcast_id` per YouTube channel, one shared YouTube bucket, or one per topic? → A: **Per channel**, `yt-{handle-slug}`. Same "one feed, one index" mapping Spec 036 chose for `x-{handle}`. A handle rename splits identity forever; accepted knowingly, as with X.
- Q: What is `episode_ref`? → A: **The YouTube video id** (11 characters, `A-Za-z0-9_-`). Parsed from the URL, never from a playlist id. Unlike an X status id, a video id may contain `_`, so the repo-wide episode-ref alphabet MUST gain `_` (see FR-017). Mapping `_` to `-` is rejected because it is lossy.
- Q: `source_type` / `seed_source` value? → A: **`yt-video`**, matching `x-video`.
- Q: How does the index stay config-free while closing the seam? → A: **The discriminant is `seed_source` already stored on the episode seed and echoed by the index.** Profile `source_type` stays an ingest-surface check. `corpus_index` MUST NOT import config.
- Q: What should the remediation plan do when a video-sourced episode is missing audio? → A: **Block the RSS download action** and name the source ingest command (X or YouTube) using the seed `selector`. Do not mark it `ready` for `download_episode.py`. Do not fold URL-driven ingest into `corpus_audio_download_runner` (036 architecture review: that family is remediation-plan-driven and podcast-scoped).
- Q: Is title provenance in v1? → A: **Yes.** The local transcription runner MUST pass the plan/index episode title (seed-backed when no transcript exists) into `transcribe_episode(..., title=...)` and into planned write paths. Omitting `title` on `transcribe_episode` itself stays backward-compatible.
- Q: MCP tool? → A: **No.** Core plus a thin CLI. Registry stays at exactly 22. Exposure waits for a successor (040 remains the X-ingest MCP candidate; YouTube exposure is a later spec).
- Q: Operator `--podcast` override? → A: **Not in v1.** Identity is derived, then confirm refuses unless that exact `podcast_id` is registered with `source_type: yt-video`. Same as X.

## User Scenarios & Testing

### User Story 1 — Ingest a YouTube Video into the Corpus (Priority: P1)

An operator supplies a public YouTube watch / short / share URL and receives a conformant episode seed plus transcript trio. After that, index, validation, cache, search, and summarisation work with no YouTube-specific branching.

**Why this priority**: This is the new source. Spec 036 already proved the cheap route: acquisition writes audio into `data/audio/`; `transcribe_episode(..., audio_path=...)` does the rest.

**Independent Test**: Given a public YouTube URL, a confirmed run writes the WAV, seed, and transcript trio at storage-derived paths; `validate_transcript` returns `valid`; `generate_corpus_index` lists the episode with `seed_source="yt-video"` and audio + transcript available.

**Acceptance Scenarios**:

1. **Given** a public YouTube watch URL and a registered `yt-video` profile whose id matches the derived channel slug, **When** the operator confirms ingest, **Then** the seed, WAV, and transcript trio exist at the deterministic storage paths and the source video is not stored under `data/`.
2. **Given** the produced transcript, **When** `validate_transcript` runs, **Then** it returns `status=valid` with a `segment_count` matching the transcription.
3. **Given** the produced seed, **When** `generate_corpus_index` runs for that `podcast_id`, **Then** the episode appears with `seed_source="yt-video"` and the canonical watch URL as `selector`.
4. **Given** an existing RSS podcast and an existing X podcast in the same corpus, **When** a YouTube episode is ingested, **Then** those other podcasts' corpus indexes and search results are unchanged.

---

### User Story 2 — Dry-Run Tells the Truth (Priority: P1)

The default call downloads no video, extracts no audio, transcribes nothing, and writes nothing. It does resolve public metadata so the plan names real identifiers and write paths.

**Why this priority**: Principle III. Spec 036 already taught that a plan which claims a write it will not perform is a defect.

**Independent Test**: `confirm=false` against a resolvable public URL returns planned paths and performs zero filesystem writes under `data/`.

**Acceptance Scenarios**:

1. **Given** a public YouTube URL, **When** dry-run runs, **Then** the plan names `podcast_id`, `episode_ref`, title, and every planned write path, and the `data/` tree is identical afterwards (no `.part` residue).
2. **Given** a dry-run whose WAV already exists, **When** the plan is read, **Then** it says the audio will be reused, not rewritten.
3. **Given** any dry-run or confirm result, **When** stdout is inspected, **Then** it is metadata-only JSON: no transcript body, no prompt, no secret.
4. **Given** any run, **When** cache behaviour is inspected, **Then** SQLite is not rebuilt and the response warns that the operator must rebuild before search.

---

### User Story 3 — The Source-Type Seam Tells the Truth (Priority: P1)

For an X or YouTube episode that is missing audio, the remediation plan no longer pretends RSS download will work. Corpus audio download and one-stage "next" workflows do not dispatch `download_episode` / `download_audio` for those episodes. The suggested next human step is the matching ingest CLI and the seed's canonical URL.

**Why this priority**: This is the first operational confusion an operator hits today on X, and a third source without closing it triples that confusion. Spec 036 named it as the next source spec's job.

**Independent Test**: Fixture an `x-video` (and a `yt-video`) seed with `has_audio_url=true` and no audio file. The remediation plan marks audio `blocked` (not `ready`), the suggested command is the ingest CLI with that seed's `selector`, and the audio-download runner / 014-style next dispatch refuses RSS download.

**Acceptance Scenarios**:

1. **Given** an `x-video` seed whose audio artifact is missing, **When** the remediation plan is generated, **Then** the audio action is not `ready` for `scripts/download_episode.py`; the suggested command is `scripts/run_x_video_ingest.py` with the seed selector.
2. **Given** a `yt-video` seed whose audio artifact is missing, **When** the remediation plan is generated, **Then** the audio action is not `ready` for `scripts/download_episode.py`; the suggested command is the YouTube ingest CLI with the seed selector.
3. **Given** either video seed, **When** the corpus audio download runner is asked to execute that audio action, **Then** it refuses before calling `download_audio`, naming the ingest path.
4. **Given** a one-stage fresh / completion / latest-deterministic workflow whose next ladder step would have been audio for a video seed, **When** it selects the next action, **Then** it does not dispatch the RSS audio runner.
5. **Given** an RSS episode whose feed has no enclosure (`has_audio_url=false`), **When** the plan is generated, **Then** today's `feed audio is unavailable` blocker is unchanged.
6. **Given** an RSS episode whose feed has an enclosure and whose audio is missing, **When** the plan is generated, **Then** the audio action stays `ready` with `scripts/download_episode.py`.

---

### User Story 4 — Re-transcription Keeps One Title (Priority: P1)

Re-transcribing an X or YouTube episode writes the trio under the seed title, not under `{episode_ref}__{episode_ref}`. Planned writes in dry-run name those same paths.

**Why this priority**: Spec 036 already hit this collision. A third source makes a second writer more likely, not less. `storage.find_transcript_asset_paths` resolving by `sorted()[0]` is not an acceptable disambiguator.

**Independent Test**: Fixture a video-source seed titled `Real Title` plus a matching WAV and no transcript. A confirmed local-transcription run writes `{ref}__real_title.{txt,srt,json}` and does not create `{ref}__{ref}.*`.

**Acceptance Scenarios**:

1. **Given** a seed with a non-empty title and local audio, **When** the local transcription runner plans the write, **Then** the planned paths use `storage.transcript_asset_paths(..., title=seed_or_index_title)`, not `title=episode_ref`.
2. **Given** that same episode, **When** the runner confirms transcription, **Then** the written trio matches those planned paths.
3. **Given** an RSS episode with no seed title override, **When** local transcription runs as today, **Then** existing RSS fixtures keep their current path behaviour (title still comes from the downloaded `AudioAsset` when the runner goes through `download_audio`; the audio-path branch is the one that gains the seed title).

---

### User Story 5 — A YouTube Source Is a First-Class Non-RSS Source (Priority: P2)

A YouTube channel is registered with `source_type: yt-video` and no `rss_url`. RSS-only surfaces refuse it by naming the source type and the ingest path. The YouTube ingest surface refuses an RSS or X profile whose id happens to match the derived `yt-…` slug.

**Why this priority**: Spec 036's architecture review caught the X surface not reading the discriminant it introduced. This spec must not repeat that.

**Independent Test**: Load a `yt-video` profile without `rss_url`; `list_episodes` / `get_episode` / `download_audio` raise a named unsupported-source error; YouTube ingest of an `x-video` or `rss` profile with the same id refuses before download.

**Acceptance Scenarios**:

1. **Given** a profile with `source_type: yt-video` and no `rss_url`, **When** it is loaded, **Then** it parses and `language` is still required.
2. **Given** gooaye with no `source_type` key, **When** it is loaded, **Then** it still defaults to `rss` and behaves exactly as before.
3. **Given** a YouTube source, **When** `list_episodes` or `get_episode` or `download_audio` is called, **Then** the error names `yt-video` and points at the YouTube ingest path.
4. **Given** a derived `yt-…` id registered as `x-video` or `rss`, **When** YouTube ingest is invoked, **Then** it refuses before any video download.

---

### Edge Cases

- URL is a playlist or channel page with no video id: refuse before download; do not invent an episode.
- URL is `youtu.be/`, `/shorts/`, `/embed/`, `/live/`, `m.youtube.com`, or `music.youtube.com` with a video id: accept and canonicalise to `https://www.youtube.com/watch?v={id}`.
- Video id contains `_`: accepted; paths use the id unchanged.
- Video is private, members-only, age-gated, or otherwise not publicly retrievable with a guest token: refuse; do not prompt for cookies or credentials.
- Video has no audio stream: refuse; write no seed and no WAV.
- Profile is missing at confirm: refuse after dry-run has already warned, matching X.
- Repeated confirm for the same video id: do not duplicate the seed; reuse existing WAV unless the operator has deleted it.
- Existing `{ref}__{ref}.*` trio plus a seed with a real title: new writes go to the seed title; the runner does not delete the old trio (cleanup is out of scope).

### Safety and Data Boundaries

- Side-effect and dry-run-first: no video download, audio extraction, transcription, or write without `confirm=true`.
- **This dry-run is zero-write, not zero-network**, same deliberate trade as Spec 036. Metadata resolution is what makes the plan real. Any future MCP exposure MUST document that distinction or name the mode differently.
- Download uses yt-dlp with a guest token only. No login, no cookies, no credential, no stored session.
- Accepts a source URL; derived `podcast_id` / `episode_ref` must pass the storage slug and episode-ref predicates. Never accepts an arbitrary local write path.
- Does not rebuild the SQLite cache; the response carries the stale-cache warning.
- Ingesting a YouTube episode MUST NOT modify any other `podcast_id`'s artifacts.
- No LLM, no `api_cost_ack`, no `.env` read on this path.
- No live market API. No investment advice.
- Index stays config-free. Seam logic reads `seed_source` / `selector` / `title` from the seed projection the index already emits.

## Requirements

### Acquisition

- **FR-001**: The system MUST resolve a public YouTube URL's metadata, yielding at minimum video title, upload date, duration, channel handle or channel id, and canonical watch URL.
- **FR-002**: The system MUST download the video with yt-dlp using a guest token and extract a mono 16 kHz PCM WAV with PyAV to `storage.audio_asset_path(podcast_id, episode_ref, title, ".wav")`.
- **FR-003**: The downloaded source video MUST NOT be written anywhere under `data/`; only the extracted audio is a corpus artifact.
- **FR-004**: The system MUST write a `CorpusEpisodeSeed` at `storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)` with `seed_source="yt-video"`, the canonical watch URL as `selector`, `has_audio_url=true`, and `published_at` from the resolved upload date when present.
- **FR-005**: Transcription MUST reuse `transcribe_episode(..., audio_path=..., title=...)`. No second transcript writer.

### Identity and registration

- **FR-006**: `episode_ref` MUST default to the 11-character YouTube video id parsed from the URL. `info["id"]` MAY be used only as a consistency check; the URL id wins if they differ.
- **FR-007**: `podcast_id` MUST default to `yt-{handle-slug}`. Handle is lowercased, `@` stripped, `_` and `.` mapped to `-`, and any remaining non-slug character dropped. If no handle is available, use `yt-` plus the lowercased channel id. Confirm MUST refuse unless that exact id is registered with `source_type: yt-video`.
- **FR-008**: `title` MUST default to the metadata title, MUST be overridable by an explicit operator argument, MUST collapse whitespace, and MUST be capped by the existing `storage.title_slug`. Do not apply the X-specific `{uploader} - ` strip.
- **FR-009**: RSS-only surfaces MUST refuse `yt-video` with a message that names the source type and the YouTube ingest path.
- **FR-010**: The YouTube ingest surface MUST refuse a profile whose `source_type` is not `yt-video`, including a missing profile, before any video download on confirm.

### Source-type seam

- **FR-011**: `corpus_index` MUST keep echoing `seed_source`, `selector`, and seed `title`. It MUST NOT import config or grow a `source_type` field from the profile.
- **FR-012**: For `seed_source` in `{x-video, yt-video}`, a missing or unreadable audio artifact MUST NOT produce a `ready` remediation action that suggests `scripts/download_episode.py`. The action MUST be blocked for the RSS download path and MUST suggest the matching ingest CLI with the seed `selector`.
- **FR-013**: `run_corpus_audio_download` MUST refuse a video-sourced audio action before `download_audio`. One-stage workflows that would have dispatched that runner (014 / 016 / 017) MUST NOT dispatch it for those episodes.
- **FR-014**: RSS `has_audio_url=false` and RSS `has_audio_url=true` missing-audio behaviour MUST remain unchanged.

### Title provenance

- **FR-015**: The local transcription runner MUST resolve write-title from the remediation-plan episode title (index title: existing transcript title, else seed title, else `episode_ref`) and MUST pass that title into `transcribe_episode` on the `audio_path` branch and into planned write paths.
- **FR-016**: `transcribe_episode` omitting `title` MUST preserve current behaviour exactly.

### Episode-ref alphabet

- **FR-017**: The storage episode-ref predicate MUST accept `_` in addition to `A-Za-z0-9-`. Existing refs without `_` MUST keep working. Duplicate episode-ref regexes in runners, claims, and MCP wrappers MUST use the same predicate so a YouTube id containing `_` is not accepted by ingest and then rejected by a later workflow.

### Boundaries

- **FR-018**: `confirm=false` MUST resolve metadata only: no video download, no audio extraction, no transcription, zero writes.
- **FR-019**: The run MUST NOT rebuild the SQLite cache.
- **FR-020**: Acquisition MUST NOT accept, prompt for, or store credentials, and MUST refuse when the URL is not publicly retrievable with a guest token.
- **FR-021**: Ingestion MUST NOT modify artifacts belonging to any other `podcast_id`.
- **FR-022**: No new runtime dependency. Reuse `yt-dlp` and `av`.
- **FR-023**: No new MCP tool. Registry stays at exactly 22.

### Key Entities

- **YouTube identity**: derived `podcast_id` + video-id `episode_ref` + canonical watch URL.
- **YouTube episode seed**: existing `CorpusEpisodeSeed` with `seed_source="yt-video"`.
- **Video seed sources**: the closed set `{x-video, yt-video}` used by the seam. Not an enum on the seed (seeds stay unconstrained strings); the plan/runner treat only these two as video ingest sources.
- **Remediation audio action**: existing 009 action whose `status`, `reason`, and `suggested_command` become seed-source-aware.

## Success Criteria

- An operator turns a public YouTube URL into a searchable corpus episode without hand-editing any file.
- `validate_transcript` returns `valid` for the produced episode.
- `generate_corpus_index` reports audio and transcript available with `seed_source="yt-video"`.
- gooaye's corpus index file is byte-for-byte unchanged across a YouTube ingestion.
- An X episode missing audio no longer receives a `ready` `download_episode.py` suggestion; the plan names `run_x_video_ingest.py` and the RSS audio runner does not run.
- Re-transcribing a video-sourced episode does not create `{episode_ref}__{episode_ref}.*` when the seed has a real title.
- A YouTube video id containing `_` is a legal `episode_ref` end-to-end (ingest, index, transcription, later workflows).
- The reviewed MCP registry stays at exactly 22 tools.
- Full repository regression shows no new failure outside the pre-existing blocked Hermes chain (24 failed).

## Assumptions

1. Spec 036's acquisition stack is the right reuse: yt-dlp metadata + guest download + PyAV 16 kHz mono WAV + `transcribe_episode`. YouTube is a new identity/seed surface on that stack, not a parallel producer.
2. `corpus_index` already projects `seed_source`, `selector`, and seed `title`. The seam is a reader problem in 009 / 012 / 011 / 014 / 016 / 017, not a missing index field.
3. 036 architecture review still holds: URL-driven ingest stays outside the `corpus_*_runner` family.
4. Expanding episode-ref to allow `_` is additive and path-safe (`_` is not a separator). It is not a constitution change and not one of the nine handoff safety boundaries. It **is** a cross-module identity contract and must be single-sourced.
5. No committed YouTube channel profile is required to land the package; tests use fixtures. The operator adds a real `yt-…` profile locally before a live confirm.
6. Principle IV is unamended: this path does not send transcript text to an LLM.
7. Spec 038 remains a separate in-progress package. This spec does not touch study-guide files.

## Out of Scope (v1)

- MCP exposure for YouTube or X ingest (040 and successors).
- Playlists, channel crawls, batch ingest, scheduling, auto-remediation.
- Cookies, logins, members-only or age-gated videos.
- Operator `--podcast` / `--episode-ref` overrides.
- Folding ingest into `corpus_audio_download_runner`.
- Deleting leftover `{ref}__{ref}.*` trios after the title fix.
- Retrofitting `source_type` to a closed enum at profile load (037 explicitly left that asymmetry).
- Live market API, investment advice, cache auto-rebuild, translation, `05` / `06` study-guide derivations.
- Constitution amendment.

## Live Confirm Record

Run on 2026-08-22 against `https://www.youtube.com/watch?v=BOvyerl_0cE` (NASA, 78 s, US
government work). The operator registered `yt-nasa` locally, confirmed the ingest, then
removed the profile again. Nothing from the run is committed: every artifact landed under
the ignored `data/` tree.

| Claim | Evidence |
| --- | --- |
| Identity derivation (FR-007) | `@NASA` → `yt-nasa`; `@NASAJPL` → `yt-nasajpl` |
| URL canonicalisation | `youtu.be/`, `m.`, and `music.` resolved to one `episode_ref` |
| Preview is zero-write (FR-018) | `data/` held 155 files before and after; empty diff |
| Title-slug fix | Wrote `BOvyerl_0cE__GoNo-Go_NASAs_Space_Toilet_Explained.*`, not `{ref}__{ref}.*` |
| Trio at deterministic paths | Seed, 16 kHz mono WAV (77.2 s), and txt/srt/json all present |
| Source video not under `data/` | No `.mp4`/`.webm`/`.mkv`/`.m4a` anywhere in the tree |
| `validate_transcript` | `valid: true`, 27 segments, zero problems, zero warnings |
| Index row | `seed_source: yt-video`, audio `available`, transcript `valid` |
| gooaye untouched | `corpus-index.json` digest unchanged across the run |
| Refuse cases | Channel and playlist URLs, unregistered id, `source_type` mismatch (4.1 s, pre-download), and `list_episodes` / `download_audio` all refused |

Three things the mocked suite cannot see, because it stands in for exactly the
preconditions this run tested:

1. **yt-dlp goes stale against YouTube.** 2026.06.09 returned `HTTP 403` on the media URL
   while metadata still resolved. 2026.08.19 downloads. A CI job that runs a live confirm has
   to upgrade yt-dlp per run rather than pin it.
2. **ffmpeg is an undeclared prerequisite, and only YouTube trips it.**
   `video_acquire.guest_download_options` sets no `format`, so yt-dlp's default selector
   merges separate streams. X serves pre-muxed MP4 and never needs the merge; YouTube serves
   DASH and always does. `specs/036-x-video-corpus-ingestion/tasks.md:266` shows ffmpeg was
   present when 036 was written, which is why it was never written down.
3. **The documented procedure turns `test_contracts.py` red.** That test asserts
   `set(profiles) == {"gooaye", "x-raytar"}` against the real config file, while Assumption 5
   requires the operator to add a `yt-…` profile to it, and `run_youtube_video_ingest` takes
   no alternate config path. Measured: 1 failed / 68 passed with the profile present, green
   once removed.

Two follow-ups, neither in this spec's scope:

- Request an audio-only `format` in `video_acquire`, updating `DOWNLOAD_OPTION_KEYS` and the
  subset assertion at `tests/test_video_acquire.py:22` with it. This run fetched 32.30 MiB of
  video plus 1.26 MiB of audio, merged them, and discarded the video; the audio alone would
  have done. It drops the ffmpeg dependency, and it touches the X path too, so it needs its
  own change and review.
- Give the runner an alternate config path, so a live confirm no longer has to edit the
  committed profile file.

One observation: `planned_writes` listed seven paths and the run wrote eight. The extra file
is `data/corpus/yt-nasa/.episode-claims/BOvyerl_0cE.writer.claim`, the writer lock. Whether a
lock counts as a planned write is a judgement call, but the plan currently under-reports.
