# Feature Specification: X Video Corpus Ingestion

**Feature Branch**: `036-x-video-corpus-ingestion`  
**Created**: 2026-08-15  
**Status**: Implemented (v1). One confirmed real-URL run completed 2026-08-15. Both review axes passed: `code-reviewer` after five fixes, `architecture-reviewer` after one (the X surface was not enforcing the `source_type` discriminant it introduced). Structural follow-ups for the next source spec are listed in `tasks.md`.

**Input**: The corpus ingests RSS podcasts only, but the AI practitioners the user learns from teach on X. A working single-video prototype already exists outside this repo (`../prompt-engineering`, built 2026-06-30): yt-dlp downloads an X video with a guest token, PyAV extracts audio, faster-whisper transcribes, and `group_segments()` merges fragments into 30-90s blocks. Its weakness is the analysis layer — `generate_learning_docs.py` bakes hand-written zh-TW prose into source, so a second video would need rewriting by hand. This repo already automates exactly that layer. A seam trial on 2026-08-15 shaped the prototype's existing 366-segment output into the corpus contract and confirmed the whole downstream pipeline accepts it unchanged. What is missing is the producer: a path from an X video URL to a conformant episode seed plus transcript trio, after which the existing pipeline takes over.

## Clarifications

### Session 2026-08-15

- Q: One `podcast_id` per X account, one shared X bucket, or one per topic? → A: **Per account** (`x-raytar`). `corpus-index` is generated per `podcast_id`, so an account maps cleanly onto the existing "one feed, one index" model.
- Q: What is `episode_ref` for a video? → A: **The tweet status id** (`2071290493581840707`). It satisfies `^[A-Za-z0-9][A-Za-z0-9-]*$` unmodified and is the stable canonical identifier.
- Q: `seed_source` value for non-RSS sources? → A: **`"x-video"`**. Verified unconstrained — no enum, no `Literal`, no validator; `"rss"` was merely the only value ever written. The trial's seed was accepted and echoed by `corpus_index` unchanged.
- Q: `not_investment_advice` is a finance-corpus field and semantically odd on AI-teaching content — remove it? → A: **Keep `true` in v1.** Repo-wide grep confirms no code reads it as a gate; it is only ever written into artifacts as a static disclaimer. Changing it buys nothing and would be a second variable. Revisit only if a consumer starts reading it.
- Q: Where do the prototype's 30-90s `groups` live? → A: Not landed in the trial; **resolved below as computed-on-demand.** Recorded because it stays true whatever is decided later: a sidecar named `{episode_ref}__*.json` under `data/transcripts/` is a closed path — `storage.find_transcript_asset_paths`'s `glob` + `sorted()[0]` would select it as the canonical transcript.
- Q: Must a new `podcast_id` be registered in `config/podcasts.yaml`? → A: **No, for the filesystem paths.** `generate_corpus_index`, `validate_transcript`, cache and search never read config. Only RSS-backed functions (`list_episodes`, `get_episode`, `download_audio`) do, and they will raise `KeyError` for an X source.
- Q: New dependencies? → A: **Yes** — `yt-dlp` and `av` (PyAV). `faster-whisper>=1.1.0` is already a direct dependency.
- Q: Which layer does X acquisition plug into — reuse the transcription path, or build a parallel producer? → A: **Reuse.** `transcribe_episode` already accepts `audio_path`, which bypasses `download_audio` entirely, and its `profile` lookup is used for exactly one thing: `profile.language`. So the only new code is acquisition (yt-dlp + PyAV) writing an audio asset into `data/audio/{podcast_id}/`; transcription, emission, validation, indexing and search are all existing code. This also makes the `audio` artifact family available in `corpus_index`, which the trial left missing.
- Q: If X sources reuse the transcription path, they need a podcast profile. How? → A: **Register them in `config/podcasts.yaml` with a `source_type` discriminator.** `rss_url` and `default_episode_prefix` are consumed only by `feed_reader.py`, so they become optional for non-RSS sources while `language` stays required. Defaulting `source_type` to `"rss"` keeps every existing profile valid unchanged.
- Q: Is the public transcript-emission seam (an earlier draft's FR-005) still needed? → A: **No.** Reusing `transcribe_episode` means nothing outside `transcriber.py` needs to write a transcript trio, so the private writers stay private. The requirement is reduced to plumbing a `title` through the `audio_path` branch.
- Q: Where does `title` come from once this is automated? → A: **yt-dlp metadata, operator-overridable.** Run yt-dlp with `--write-info-json` (the prototype did not, which is why the trial had no `published_at`), take the video title, collapse whitespace, and let the existing `storage.title_slug` cap it at 80 characters. An explicit `--title` overrides.
- Q: Where do the 30-90s groups finally live? → A: **Nowhere — computed on demand.** `group_segments()` is a pure function of the segments, so persisting it would add an unvalidated field that RSS episodes would not have. Port the function; call it where grouping is needed.

## User Scenarios & Testing

### User Story 1 — Ingest an X Video into the Corpus (Priority: P1)

An operator supplies an X video URL and receives a conformant episode seed plus transcript trio, after which every existing corpus capability — index, validation, cache, search, summarisation — works on it with no special-casing.

**Why this priority**: This is the whole feature. The prototype proved the media path; the 2026-08-15 trial proved the corpus contract accepts the result. Nothing connects the two.

**Independent Test**: Given an X video URL for a talk, the run produces `data/transcripts/{podcast_id}/{episode_ref}__{title_slug}.{txt,srt,json}` and `data/corpus/{podcast_id}/episode-seeds/{episode_ref}.episode-seed.json`; `validate_transcript` returns `valid`; `generate_corpus_index` lists the episode with the transcript family available; `search_transcripts` returns a hit whose timestamp falls inside the video.

**Acceptance Scenarios**:

1. **Given** an X video URL, **When** the ingestion runs confirmed, **Then** the transcript trio and episode seed exist at the deterministic paths derived from `storage`, never hand-composed.
2. **Given** the produced transcript, **When** `validate_transcript` runs, **Then** it returns `status=valid` with zero problems and a `segment_count` matching the transcription.
3. **Given** the produced seed, **When** `generate_corpus_index` runs for that `podcast_id`, **Then** the episode appears with `seed_source="x-video"` and its canonical URL as `selector`.
4. **Given** the episode is indexed into the SQLite cache, **When** `search_transcripts` is called with a phrase spoken in the video, **Then** it returns a hit with a timestamp inside the video's duration.
5. **Given** an existing RSS podcast in the same corpus, **When** an X episode is ingested, **Then** that podcast's corpus index and search results are unchanged.

### User Story 2 — Dry-run First (Priority: P1)

The default call downloads nothing, transcribes nothing, and writes nothing; it returns the plan — resolved identifiers, planned writes, and the cost of the transcription step.

**Why this priority**: `AGENTS.md` requires side-effect workflows to stay dry-run-first where practical, and this one spends a long GPU/CPU transcription and a large download.

**Acceptance Scenarios**:

1. `confirm=false` returns an action plan naming the resolved `podcast_id`, `episode_ref`, and every planned write path, and performs zero writes and zero network calls beyond metadata resolution.
2. The plan states that the run does not rebuild the SQLite cache and that the operator must do so to make the episode searchable.
3. `confirm=true` executes once; a repeated confirmed run for the same `episode_ref` does not duplicate the seed.

### User Story 3 — A Non-RSS Source Is a First-class Corpus Source (Priority: P2)

A source that has no RSS feed is registered, transcribed, indexed, and searched by the same code paths as an RSS podcast, and the RSS-only surfaces refuse it in a way that explains itself.

**Why this priority**: `podcast_id` currently means "an RSS feed". Every filesystem path already tolerates a non-RSS source — the trial proved that with no registration at all — but `load_podcast_profile` gates transcription, and `list_episodes` / `get_episode` / `download_audio` would fail with a bare `KeyError`. Making the source type explicit is what turns an accidental capability into a supported one.

**Acceptance Scenarios**:

1. **Given** a profile with `source_type: x-video` and no `rss_url`, **When** it is loaded, **Then** it parses successfully and `language` is still required.
2. **Given** an existing RSS profile with no `source_type` key, **When** it is loaded, **Then** it defaults to `rss` and behaves exactly as before.
3. **Given** an X source, **When** `list_episodes` or `get_episode` is called for it, **Then** the error names the source type and points to the ingestion path, instead of raising `KeyError` from a config lookup.
4. **Given** an X source with an extracted audio asset, **When** `transcribe_episode` runs with `audio_path`, **Then** it produces the trio under the real title, not under the episode ref.

## Safety and Data Boundaries

- Side-effect and dry-run-first: no download, transcription, or write without `confirm=true`.
- **This dry-run is zero-write, not zero-network** — and that differs from the `corpus_*` runner family, whose dry-runs promise no network read at all. Resolving metadata is what makes the plan real (title, upload date, duration, and whether the post even has a video), so it is a deliberate trade, not an oversight. Any successor spec that exposes this over MCP must either document the distinction on the tool or name the mode differently, because zero-side-effect dry-run is that family's tool contract.
- Download uses yt-dlp with a guest token only. No login, no cookies, no credential, no stored session. If a URL requires authentication, the run refuses rather than prompting for credentials.
- Accepts a source URL and a `podcast_id`/`episode_ref` pair, never an arbitrary local write path. `podcast_id` must satisfy `^[a-z0-9][a-z0-9-]*$` and `episode_ref` `^[A-Za-z0-9][A-Za-z0-9-]*$`; both already raise on violation in `storage`.
- Does not rebuild the SQLite cache; the response carries the stale-cache warning, consistent with every existing side-effect tool.
- Ingesting a new source MUST NOT modify any other `podcast_id`'s artifacts. `generate_corpus_index` is per-podcast and `rebuild_cache --podcast <id>` scopes discovery to that podcast's directories.
- Transcription confidence is evidence, not decoration: the prototype's `[不確定：<guess>]` convention for unclear audio is retained, matching this repo's evidence-vs-inference rule.
- No investment advice. The corpus's existing no-advice boundary is unchanged; AI-teaching content simply does not invoke it.

## Requirements

**Acquisition — the only genuinely new capability**

- **FR-001**: The system MUST resolve an X video URL's metadata with `yt-dlp --write-info-json`, yielding at minimum the video title, upload date, duration, and canonical status URL.
- **FR-002**: The system MUST download the video with yt-dlp using a guest token and extract a mono 16 kHz PCM WAV with PyAV, written to `storage.audio_asset_path(podcast_id, episode_ref, title, ".wav")`. `.wav` is already recognised by `corpus_index._AUDIO_SUFFIXES`, so the `audio` artifact family becomes available.
- **FR-003**: The downloaded source video MUST NOT be written anywhere under `data/`; only the extracted audio is a corpus artifact.
- **FR-004**: The system MUST produce a `CorpusEpisodeSeed` at `storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)` with `seed_source="x-video"`, the canonical status URL as `selector`, and `published_at` populated from the resolved upload date.

**Reuse — no second transcription or emission path**

- **FR-005**: Transcription MUST reuse `transcriber.transcribe_episode(..., audio_path=...)`. No new transcription, SRT-formatting, or transcript-writing code may be introduced; `_write_transcript_outputs` and its helpers stay private.
- **FR-006**: `transcribe_episode` MUST accept an optional title for its `audio_path` branch so the trio is named by the real title rather than by `episode_ref` (today `_audio_asset_from_path` hardcodes `title=episode_ref`). Omitting it MUST preserve current behaviour exactly.
- **FR-007**: Because emission is reused, contract conformance is inherited: segments carry exactly `id`, `start`, `end`, `text`, and Whisper quality fields (`avg_logprob`, `no_speech_prob`, `words`, `flags`) never reach the transcript. This MUST be asserted by test, not assumed.

**Source registration**

- **FR-008**: `PodcastProfile` MUST gain a `source_type` field defaulting to `"rss"`. `rss_url` and `default_episode_prefix` MUST become optional when `source_type != "rss"`; `language` MUST stay required for every source because transcription depends on it.
- **FR-009**: Every existing profile lacking a `source_type` key MUST parse and behave exactly as before.
- **FR-010**: RSS-only surfaces (`list_episodes`, `get_episode`, `download_audio`) MUST refuse a non-RSS source with a message naming the source type and the correct ingestion path, not a bare `KeyError` from `load_podcast_profile`.

**Identity and defaults**

- **FR-011**: `episode_ref` MUST default to the tweet status id and `podcast_id` to a per-account slug derived from the X handle; both MUST be validated by the existing `storage` slug and ref patterns.
- **FR-012**: `title` MUST default to the yt-dlp metadata title, MUST be overridable by an explicit operator argument, and MUST be capped by the existing `storage.title_slug`. Normalisation MUST collapse whitespace, strip the redundant `"{uploader} - "` prefix, and strip yt-dlp's own trailing ellipsis. A real resolve on 2026-08-15 returned `"Raytar - My friend makes $1.2 million a year as an Anthropic engineer.  I aske..."` — for X the metadata title is the post's text, not a title, so the default is best-effort and the override is the real answer whenever the name matters. See the known limitation in Assumptions.

**Grouping**

- **FR-013**: `group_segments()` MUST be ported from the prototype as a pure function of the segments (sentence-boundary soft break at ≥30s, hard cap at 90s) and MUST NOT be persisted into any artifact. Callers compute it on demand.

**Boundaries**

- **FR-014**: `confirm=false` MUST return an action plan built from metadata resolution alone — no video download, no audio extraction, no transcription, and zero writes.
- **FR-015**: The run MUST NOT rebuild the SQLite cache; the response MUST state that the episode is not searchable until the operator rebuilds.
- **FR-016**: Acquisition MUST NOT accept, prompt for, or store credentials, and MUST refuse when a URL is not publicly retrievable with a guest token.
- **FR-017**: Ingestion MUST NOT modify artifacts belonging to any other `podcast_id`.
- **FR-018**: `yt-dlp` and `av` MUST be added as declared dependencies; no other new runtime dependency.

## Success Criteria

- An operator turns an X video URL into a searchable corpus episode without hand-editing any file.
- `validate_transcript` returns `valid` for the produced episode, with `segment_count` equal to the transcription's segment count and `last_segment_end_seconds` within the video's duration.
- `search_transcripts` returns a hit for a phrase spoken in the video, with a timestamp inside the video's duration.
- `generate_corpus_index` reports the `audio` family available for the episode, which the 2026-08-15 trial could not achieve because it shaped a transcript without acquiring audio.
- An existing RSS podcast's corpus index file and search results are byte-for-byte unchanged across an X ingestion.
- An existing RSS episode's transcript output is byte-for-byte unchanged after the `transcribe_episode` title change.
- The semantic summariser runs on an X episode with no source-specific branching, replacing the prototype's hand-written analysis layer.
- Full repository regression shows no new failure outside the pre-existing blocked chain.

## Assumptions

1. The seam is already proven. On 2026-08-15 the prototype's existing `_transcript_segments.json` (366 segments, 33:24, English) was shaped into `x-raytar` / `2071290493581840707` and accepted end-to-end: `validate_transcript` → `valid` (366 segments, 2003.31s), `generate_corpus_index` → 1 episode with transcript available, `rebuild_cache --podcast x-raytar` → 1 indexed, 0 problems, `search_transcripts` → FTS5 hits at 00:09:49 / 00:16:02. gooaye's index mtime and search output were unchanged. Only the four mechanical gaps and the grouping decision remain.
2. The corpus JSON readers are tolerant. No pydantic, no `extra="forbid"`; every consumer is a `dict.get` scan, so additive keys are safe but unvalidated.
3. `data/transcripts/` and `data/corpus/` are gitignored, so ingested artifacts never enter version control.
4. Transcription cost is the operator's, on existing hardware. GPU faster-whisper is already configured on the target machine and remains optional.
5. Path length is a real constraint on Windows but not a binding one here: `title_slug` is already capped at 80 characters, so a 19-digit tweet id yields filenames of at most ~106 characters. Only an unusually deep data root breaches `MAX_PATH`; the repo's own `data/` does not.
6. The prototype's `output/00_*.md` .. `07_*.md` sequence is the user's own design for AI-learning output and is treated as target, not as something to redesign.
7. The RSS coupling is thinner than it looks. `load_podcast_profile` has nine callers, and the analyze pass on 2026-08-15 checked what each actually reads: `entity_extractor`, `episode_intelligence`, `external_data_boundary`, `industry_mapping`, `semantic_summarizer`, `stock_lens`, and `summarizer` read only `profile.display_name`; `transcriber` reads only `profile.language`; `feed_reader` is the sole reader of `rss_url` and `default_episode_prefix`. Making those two optional therefore cannot reach any analysis module — this is what makes reuse cheaper than a parallel producer.
8. `.wav` is already in `corpus_index._AUDIO_SUFFIXES`, so the extracted audio needs no index change to be recognised.
9. The prototype ran yt-dlp without `--write-info-json`, which is why the trial seed had `published_at: null`. Enabling it is what makes FR-004's upload date and FR-012's title available. Confirmed by a real resolve on 2026-08-15: `upload_date=20260628`, `duration=2003.868`, `uploader=Raytar`.

10. **Known limitation — the default X title is mediocre.** yt-dlp reports an X post's title as `{uploader} - {truncated post text}...`. FR-012 strips the uploader prefix and the ellipsis, but what remains is post text truncated mid-word by yt-dlp, and `storage.title_slug` then removes punctuation — so `$1.2 million` becomes `12_million` in the filename, which reads as twelve million. Fixing that would mean changing `title_slug`, which is shared with every RSS episode and out of scope here. Pass `--title` for anything worth naming properly.

11. **`info["id"]` is not the status id.** The real resolve returned `id=2071288253727096832` for status `2071290493581840707` — a media-entity id. `episode_ref` comes from the URL path, never from `info["id"]`.

## Out of Scope (v1)

- **MCP exposure (a Tool 23).** v1 ships Core plus a thin CLI script only. This follows the repo's own precedent: Spec 004 built the stock lens Core and CLI, and exposing it as Tool 22 waited for Spec 035 — because the registry count is a pinned chain running through the Hermes AST projection, the Spec 029 descriptor snapshot, the deny adapter, and the docs-count consistency check. Bundling that blast radius with a new ingestion source would make both harder to review.
- YouTube and any source other than X.
- Porting or rewriting the prototype's analysis layer (`generate_learning_docs.py`); the existing semantic summariser replaces it.
- A new artifact family for the study-guide document sequence.
- Exposing X episodes through the RSS-backed `list_episodes` / `get_episode` surfaces beyond a clear refusal.
- Batch or playlist ingestion, scheduling, and auto-remediation.
- Translation of transcripts; the corpus stores the source-language transcript.
