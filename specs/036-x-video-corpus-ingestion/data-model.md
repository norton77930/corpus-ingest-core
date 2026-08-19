# Data Model: X Video Corpus Ingestion

No new artifact family and no new persisted schema. This records how an X video
maps onto the existing contract, and the one additive config change.

## Identity

| Field | Value for an X video | Constraint |
| --- | --- | --- |
| `podcast_id` | per-account slug, e.g. `x-raytar` | `storage._SAFE_SLUG_PATTERN` `^[a-z0-9][a-z0-9-]*$` |
| `episode_ref` | tweet status id, e.g. `2071290493581840707` | `storage._SAFE_EPISODE_REF_PATTERN` `^[A-Za-z0-9][A-Za-z0-9-]*$` |
| `title` | yt-dlp metadata title, whitespace-collapsed, operator-overridable | `storage.title_slug` caps the slug at 80 chars |

## Paths (all derived, never hand-composed)

```text
data/audio/{podcast_id}/{episode_ref}__{title_slug}.wav          storage.audio_asset_path
data/transcripts/{podcast_id}/{episode_ref}__{title_slug}.txt    storage.transcript_asset_paths
data/transcripts/{podcast_id}/{episode_ref}__{title_slug}.srt
data/transcripts/{podcast_id}/{episode_ref}__{title_slug}.json
data/corpus/{podcast_id}/episode-seeds/{episode_ref}.episode-seed.json
                                                                 storage.corpus_episode_seed_asset_path
```

The source video is written outside `data/` and is not a corpus artifact.

## `CorpusEpisodeSeed` mapping

The dataclass (`models.py`) is unchanged; only the values differ from RSS.

| Field | RSS today | X video |
| --- | --- | --- |
| `published_at` | RSS pubDate | yt-dlp `upload_date` |
| `duration` | RSS duration | yt-dlp `duration` |
| `guid_status` | `present` / `missing` | `present` — the status id is the guid |
| `has_audio_url` | RSS enclosure present | `true` — the video URL yields audio |
| `seed_source` | `rss` | `x-video` |
| `selector` | RSS selector | canonical status URL |
| `not_investment_advice` | `true` | `true`, unchanged |

`seed_source` is unconstrained — no enum, no `Literal`, no validator — and
`corpus_index._source_metadata` echoes it verbatim. Verified by the 2026-08-15
trial, whose `x-video` seed was accepted and displayed unchanged.

Note `corpus_index` reads `warning_count` but not the `warnings` array, so seed
warning text does not surface in the index. Pre-existing behaviour; not changed here.

## Transcript JSON

Unchanged and inherited by reusing `transcribe_episode`. Segments carry exactly
`id`, `start`, `end`, `text`. Whisper quality fields (`avg_logprob`,
`compression_ratio`, `no_speech_prob`, `avg_word_probability`, `flags`, `words`)
exist in the prototype's output and MUST NOT reach the transcript.

The 30-90s groups are **not** part of this model. They are recomputed from
`segments` on demand.

## `PodcastProfile` — the one additive change

```python
podcast_id: str
display_name: str
rss_url: str | None            # was: str    — required only when source_type == "rss"
language: str                  # unchanged, required for every source
default_episode_prefix: str | None  # was: str — required only when source_type == "rss"
source_type: str = "rss"       # new
```

Consumers, verified 2026-08-15: `rss_url` and `default_episode_prefix` are read
only by `feed_reader.py`; `language` is read by `transcriber.py`, which uses the
profile for nothing else. A profile with no `source_type` key parses as `"rss"`,
so `config/podcasts.yaml`'s existing `gooaye` entry is untouched.
