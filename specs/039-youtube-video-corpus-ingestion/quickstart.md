# Quickstart: YouTube Video Corpus Ingestion and Source-Type Seam

Validation only. Do not run a live YouTube download until targeted tests are green and the operator names the URL plus registers `yt-…`.

## Prerequisites

- `yt-dlp` and `av` already installed (Spec 036)
- A `config/podcasts.yaml` profile whose id equals the derived `yt-{handle-slug}` and whose `source_type` is `yt-video`
- Public video (guest token; no cookies)

## Dry-run (always first)

```powershell
python scripts/run_youtube_video_ingest.py --url "https://www.youtube.com/watch?v=<id>"
```

Expect `confirmed: false`, planned write paths, zero new files under `data/`. If the WAV already exists, the plan must say reuse.

`youtu.be/`, `/shorts/`, and `music.youtube.com` URLs must resolve to the same `episode_ref`.

## Confirm (operator-authorised)

```powershell
python scripts/run_youtube_video_ingest.py --url "https://www.youtube.com/watch?v=<id>" --confirm
```

Expect seed + WAV + transcript trio. Then:

```powershell
python scripts/validate_transcript.py --podcast <yt-id> --episode <video-id>
python scripts/generate_corpus_index.py --podcast <yt-id>
```

Index row: `seed_source=yt-video`, audio and transcript available. gooaye's index file is unchanged.

Search only after a **manual** cache rebuild:

```powershell
python scripts/rebuild_cache.py --podcast <yt-id>
```

## Seam check (no download)

After 009 is source-aware, a fixture or an existing x-raytar seed with missing audio must produce:

```powershell
python scripts/generate_corpus_remediation_plan.py --podcast x-raytar
```

Audio action is not `ready` for `scripts/download_episode.py`. Suggested command is `scripts/run_x_video_ingest.py --url <selector>`.

## Title check

Re-run local transcription on a video-sourced episode that already has a seed title. Planned writes and outputs use `{ref}__{title_slug}.*`, not `{ref}__{ref}.*`.

## Refuse cases

- Playlist or channel URL with no video id → error, zero writes
- Unregistered `yt-…` id on `--confirm` → error before download
- Profile registered as `rss` or `x-video` → error before download
- `list_episodes` / `download_audio` on a `yt-video` profile → `UnsupportedSourceTypeError` naming the YouTube ingest path
