# Data Model: Multi-Document Study Guide

## Identity

Same as every other corpus artifact: `podcast_id` + `episode_ref` + canonical transcript `title`. Paths are derived, never hand-composed.

## Directory and files

```text
data/study-guides/{podcast_id}/{episode_ref}__{title_slug}/
    00_video_info.md
    03_full_summary.md
    04_learning_notes.md
    07_final_study_guide.md
data/corpus/{podcast_id}/study-guide-runs/{episode_ref}.study-guide-run.json
data/corpus/{podcast_id}/study-guide-runs/{episode_ref}.study-guide-run.md
```

Staging: `.../{episode_ref}__{title_slug}.part/` then replace the canonical directory.

## Cover (`00`) fields (deterministic)

Written only when present on the local seed and/or audio asset:

- podcast_id, episode_ref, title
- seed_source, selector, published_at, duration
- audio path, audio size bytes (if the file exists)
- not_investment_advice (static true, matching other artifacts)

Forbidden: codec, resolution, stream index, anything requiring a remux or network.

## Generated files

- `03`: headings 影片主題, 核心觀念, 影片結構, 一句話總結, 適合誰看, 不確定事項
- `04`: per-concept 這個觀念是什麼 / 為什麼重要 / 影片中怎麼說 / 實際開發時怎麼用 / 錯誤用法 / 正確用法 + 不確定事項
- `07`: 背景知識, 核心重點, 白話說明, 常見錯誤, 30 秒版本總結, 3 分鐘版本總結, 不確定事項; optional reusable-prompt section only if the source summary already has one

## Corpus family `study_guide`

Per-episode `artifact_status["study_guide"]`:

| status | meaning |
| --- | --- |
| `available` | all four files exist and are readable UTF-8 |
| `partial` | 1–3 of the four exist |
| `unreadable` | four names exist but at least one fails the read cap / UTF-8 check |
| `missing` | zero files |

Family counts: `partial` increments `unreadable`.

## `StudyGuideBundleResult`

Frozen dataclass, metadata-only:

- podcast_id, episode_ref, confirm, run_mode (`dry-run` / `confirmed`)
- source_summary_path
- planned_reads, planned_writes, planned_reuses
- output_paths (four file paths; null on dry-run)
- report paths (null on dry-run if the family writes reports only on confirm — confirm writes them)
- reused: bool
- warnings (must include cache-stale on confirm writes)
- not_investment_advice: true

No generated_at. No body text. No prompt. No secret.

## Errors

`StudyGuideBundleError` (subclass of `PodcastIngestCoreError`) for profile mismatch, missing/unreadable/finance-shaped source, incomplete ack, parse failure, atomic-write failure. Identity errors reuse existing `storage` validators / `EpisodeNotFoundError` as appropriate.
