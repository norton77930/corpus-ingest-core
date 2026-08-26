# Data Model: YouTube Video Corpus Ingestion and Source-Type Seam

No new artifact family. YouTube maps onto the existing seed / audio / transcript contract. The seam changes how 009 *interprets* an existing seed, not the seed schema.

## Identity

| Field | YouTube value | Constraint |
| --- | --- | --- |
| `podcast_id` | per-channel slug, e.g. `yt-3blue1brown` | `storage` slug `^[a-z0-9][a-z0-9-]*$` |
| `episode_ref` | 11-character video id, e.g. `dQw4w9WgXcQ` or an id containing `_` | `storage.is_safe_episode_ref` `^[A-Za-z0-9][A-Za-z0-9_-]*$` |
| `title` | yt-dlp metadata title, whitespace-collapsed, operator-overridable | `storage.title_slug` cap 80 |
| `selector` | `https://www.youtube.com/watch?v={id}` | derived, never a playlist URL |

Handle slug: strip `@`, lowercase, map `_` and `.` to `-`, drop other non-slug characters, prefix `yt-`. If no handle, `yt-` + lowercased channel id.

X identity is unchanged: `x-{handle}` + numeric status id (no `_` needed).

## Paths (all derived, never hand-composed)

```text
data/audio/{podcast_id}/{episode_ref}__{title_slug}.wav
data/transcripts/{podcast_id}/{episode_ref}__{title_slug}.{txt,srt,json}
data/corpus/{podcast_id}/episode-seeds/{episode_ref}.episode-seed.json
```

The selected source media is written outside `data/` and is not a corpus artifact.

## `CorpusEpisodeSeed` mapping

Dataclass unchanged.

| Field | RSS | X (`x-video`) | YouTube (`yt-video`) |
| --- | --- | --- | --- |
| `published_at` | RSS pubDate | yt-dlp `upload_date` | yt-dlp `upload_date` |
| `duration` | RSS duration | yt-dlp `duration` | yt-dlp `duration` |
| `guid_status` | present / missing | present (status id) | present (video id) |
| `has_audio_url` | enclosure present | `true` | `true` |
| `seed_source` | `rss` | `x-video` | `yt-video` |
| `selector` | RSS selector | canonical status URL | canonical watch URL |
| `not_investment_advice` | `true` | `true` | `true` |

`seed_source` stays an unconstrained string on the seed. Seam readers treat only `{x-video, yt-video}` as video ingest sources; anything else keeps RSS rules.

## Video seed sources (reader-side set)

```text
VIDEO_SEED_SOURCES = frozenset({"x-video", "yt-video"})
```

Single definition in core (ingest package or a tiny constant next to the plan helper). 009 / 012 / 014 / 016 / 017 import it. Do not copy the set.

## Remediation audio action (009)

For a missing/unreadable `audio` family:

| seed_source | has_audio_url | status | blocker | suggested_command |
| --- | --- | --- | --- | --- |
| `rss` or absent | `false` | `blocked` | `feed_audio_url` | `download_episode.py` (unchanged text) |
| `rss` or absent | `true` | `ready` | none | `python scripts/download_episode.py --podcast … --episode …` |
| `x-video` | any | `blocked` | `source_ingest` | `python scripts/run_x_video_ingest.py --url {selector}` |
| `yt-video` | any | `blocked` | `source_ingest` | `python scripts/run_youtube_video_ingest.py --url {selector}` |
| other non-empty | `true` | `ready` | none | `download_episode.py` (unknown sources keep today's RSS assumption) |

Reason text for `source_ingest` names the ingest path and says RSS download will not run.

## `YoutubeVideoIdentity`

```text
podcast_id: str
episode_ref: str
channel_slug: str
canonical_url: str
```

## `YoutubeVideoIngestResult`

Frozen, metadata-only, X-shaped:

- `podcast_id`, `episode_ref`, `title`, `canonical_url`
- `confirmed: bool`
- `planned_writes: list[str]`
- `audio_path`, `seed_path`, `transcript_json_path` (null on dry-run)
- `warnings` (must include cache-stale warning)

No `generated_at`. No transcript body. Adding `run_mode` / `not_investment_advice` is **out of v1** (036 listed those as exposure-spec gaps on `XVideoIngestResult`; do not invent a third result shape here).

## Episode-ref predicate

Before:

```text
^[A-Za-z0-9][A-Za-z0-9-]*$
```

After (storage source of truth):

```text
^[A-Za-z0-9][A-Za-z0-9_-]*$
```

Callers that also cap length at 128 keep `len(value) <= 128` (or their existing `{0,127}` check) *after* `storage.is_safe_episode_ref(value)`.

## Errors

- `YoutubeVideoIngestDependencyError` — missing yt-dlp / av (should be unreachable if X ingest already imported them; still mirror X).
- `YoutubeVideoIngestFailedError` — URL / metadata / download / extract / registration failures.
- Existing `UnsupportedSourceTypeError` — RSS surfaces; message must mention the YouTube ingest path when `source_type == yt-video`.
- Existing `ValueError` from storage for illegal ids.

## Title authority for 011

Write-title resolution, in order, already implemented by index `_episode_title` and copied onto the 009 episode row:

1. Existing identity-valid transcript title
2. Seed title
3. `episode_ref`

011 uses that row title. It does not invent a fourth source.
