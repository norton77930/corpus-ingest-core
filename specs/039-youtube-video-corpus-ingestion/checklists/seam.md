# Seam Checklist: Source Type, Title, and Episode-Ref

**Purpose**: Requirement quality for the 036 follow-up seam closures in Spec 039
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md)

## Discriminant and plan truth

- [x] CHK001 Is the seam discriminant specified as seed `seed_source`, not profile `source_type`? [Clarity, FR-011]
- [x] CHK002 Is the closed reader set `{x-video, yt-video}` documented, with seeds remaining unconstrained strings? [Completeness, Spec §Key Entities]
- [x] CHK003 Is missing/unreadable audio on a video seed forbidden from being `ready` for `download_episode.py`? [Clarity, FR-012]
- [x] CHK004 Are suggested ingest commands specified per seed source, using the seed `selector`? [Completeness, FR-012, US3 AC1–AC2]
- [x] CHK005 Are RSS `has_audio_url=false` and RSS `has_audio_url=true` missing-audio behaviours required to stay unchanged? [Consistency, FR-014, US3 AC5–AC6]

## Runners refuse, they do not ingest

- [x] CHK006 Is `run_corpus_audio_download` required to refuse video-sourced audio before `download_audio`? [Completeness, FR-013]
- [x] CHK007 Are 014 / 016 / 017 required not to dispatch the RSS audio runner for those episodes? [Completeness, FR-013, US3 AC4]
- [x] CHK008 Is folding URL-driven ingest into `corpus_audio_download_runner` explicitly out of scope? [Boundary, Spec §Out of Scope]

## Title provenance

- [x] CHK009 Is 011 write-title specified as plan/index title (transcript else seed else `episode_ref`)? [Clarity, FR-015]
- [x] CHK010 Is `transcribe_episode` omit-`title` required to stay backward-compatible? [Consistency, FR-016]
- [x] CHK011 Is leftover `{ref}__{ref}.*` cleanup explicitly out of scope? [Boundary, Spec §Edge Cases]

## Episode-ref alphabet

- [x] CHK012 Is `_` required in the episode-ref alphabet, without mapping `_` to `-`? [Clarity, FR-017]
- [x] CHK013 Are duplicate validators required to share one predicate so ingest and later workflows agree? [Completeness, FR-017]
- [x] CHK014 Are existing refs without `_` required to keep working? [Coverage, FR-017]

## YouTube identity

- [x] CHK015 Is `episode_ref` specified as the URL video id (URL wins over `info["id"]`)? [Clarity, FR-006]
- [x] CHK016 Is `podcast_id` slug derivation specified (handle, then channel id) with confirm-time `yt-video` registration? [Completeness, FR-007]
- [x] CHK017 Are accepted URL forms and playlist-without-id refusal specified? [Coverage, Spec §Edge Cases]
- [x] CHK018 Is YouTube title normalisation specified as distinct from the X `{uploader} - ` strip? [Consistency, FR-008]
- [x] CHK019 Must the YouTube surface refuse a non-`yt-video` profile before confirm download? [Completeness, FR-010]
- [x] CHK020 Must RSS surfaces name `yt-video` and the YouTube ingest path? [Completeness, FR-009]

## Notes

Evaluated against the written spec/plan. All items pass. No spec patch required before tasks.
