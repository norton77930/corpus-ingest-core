# Contract: `run_youtube_video_ingest`

## Core

```text
run_youtube_video_ingest(
    url: str,
    *,
    confirm: bool = False,
    title: str | None = None,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    force: bool = False,
    work_dir: str | Path | None = None,
) -> YoutubeVideoIngestResult
```

Pinned via `inspect.signature` in `tests/test_contracts.py` when the symbol is exported.

Identity helper (pure, no network):

```text
derive_youtube_identity(url: str) -> YoutubeVideoIdentity
```

Raises `ValueError` when the URL has no video id.

## CLI

`scripts/run_youtube_video_ingest.py`

| Flag | Required | Default | Notes |
| --- | --- | --- | --- |
| `--url` | yes | | watch / short / share / embed / live / mobile / music URL with a video id |
| `--confirm` | no | off | execute download + extract + seed + transcribe |
| `--title` | no | metadata title | operator override |
| `--model` | no | transcriber default | forwarded |
| `--device` | no | `cpu` | forwarded |
| `--compute-type` | no | `int8` | forwarded |
| `--force` | no | off | forwarded to `transcribe_episode` |
| `--work-dir` | no | system temp | video scratch; deleted after; never under `data/` |

Stdout: metadata-only JSON (`dataclasses.asdict`). Exit 1 on `PodcastIngestCoreError` or `ValueError` with `{"error": "..."}`. No transcript body, no secret.

## Dry-run vs confirm

| | dry-run | confirm, WAV missing | confirm, WAV exists |
| --- | --- | --- | --- |
| network | metadata only | metadata + video download | metadata only (reuse WAV) |
| filesystem writes | 0 | seed + WAV + transcript trio | seed + transcript trio |
| transcription | never | yes | yes |
| video under `data/` | never | never | never |

A plan that will reuse audio must list the WAV as reuse, not as a planned write.

## Registration

Confirm refuses before download when:

- `config/podcasts.yaml` has no `podcast_id`, or
- `source_type != yt-video`

Dry-run still resolves metadata and appends the registration problem as a warning, matching X.

## Shared acquire

`video_acquire.resolve_metadata(url) -> dict`
`video_acquire.acquire_wav(url, audio_target, work_dir) -> None`

X ingest calls the same two. No cookies, no `cookiefile`, no username/password options.

## MCP

Unchanged. Exact 22 tools.
