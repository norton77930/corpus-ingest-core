# Contract: source-type seam (009 / 011 / 012 / 014 / 016 / 017)

## Discriminant

```text
episode_seed.seed_source in {"x-video", "yt-video"}
```

Read from the index/plan episode payload (`source_metadata.episode_seed`). Never from `load_podcast_profile`. `corpus_index` does not import config.

The frozenset has one definition in core.

## 009 remediation audio action

When `audio` is missing or unreadable and the seed is a video source:

- `status` = `blocked` (not `ready`)
- `blocking_artifacts` includes `source_ingest`
- `suggested_command` =
  - `x-video` → `python scripts/run_x_video_ingest.py --url {selector}`
  - `yt-video` → `python scripts/run_youtube_video_ingest.py --url {selector}`
- `reason` states that RSS download will not run and names the ingest CLI

RSS rows are unchanged: `has_audio_url=false` still uses `feed_audio_url`; `has_audio_url=true` still suggests `download_episode.py`.

`_suggested_command` takes source metadata (or seed_source + selector), not only `(podcast_id, episode_ref, family)`.

## 012 audio download runner

If the selected episode's seed is a video source, the row is `rejected` / not executed. `download_audio` is not called. The reason names the ingest CLI. Applies to dry-run and confirm.

## 014 / 016 / 017 one-stage dispatch

If the next ladder action is `audio` and the episode seed is a video source:

- do not call `run_corpus_audio_download`
- report that the human next step is the ingest CLI
- no second automatic action

A stale plan that still marks such an action `ready` is also refused here (defense in depth).

## 011 title provenance

```text
title = episode_payload["title"]   # 009 copy of index title
transcribe_episode(..., audio_path=..., title=title)
planned_writes = storage.transcript_asset_paths(podcast_id, episode_ref, title)
```

Row `title` field on `CorpusLocalTranscriptionRunRow` uses the same string, not `episode_ref`, when the plan title is non-empty.

`transcribe_episode` called without `title` remains the 036 contract (audio-path branch names by `episode_ref`).

## Episode-ref predicate

All `src/` validators use `storage.is_safe_episode_ref`. A grep-style test fails if a second alphabet regex for episode refs appears in `src/`. Length caps stay local.

## Non-goals

- 012 does not download YouTube or X media.
- 009 does not add `source_ingest` to `ARTIFACT_LADDER`.
- Index family list is unchanged.
