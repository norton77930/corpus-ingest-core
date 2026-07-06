# Tasks: Ingestion Transcript Core

**Status: Backfilled / As-built**

These retrospective tasks trace implemented behavior to code and tests. They are
not a new runtime backlog.

## Phase 1: As-built Traceability

- [x] T001 Trace episode listing and lookup to `feed_reader.py`, `list_episodes.py`, and `test_feed_reader.py`
- [x] T002 Trace audio download to `downloader.py`, `download_episode.py`, and `test_downloader.py`
- [x] T003 Trace local transcription to `transcriber.py`, `transcribe_episode.py`, and `test_transcriber.py`
- [x] T004 Trace transcript validation to `validator.py`, `validate_transcript.py`, and `test_validator.py`
- [x] T005 Trace deterministic summary to `summarizer.py`, `summarize_episode.py`, and `test_summarizer.py`
- [x] T006 Trace shared contracts to `models.py`, `storage.py`, `config.py`, `errors.py`, and `test_contracts.py`

## Phase 2: Constitution Checks

- [x] T007 Confirm no LLM provider call, no `.env` read, no live market API, no investment advice, and manual cache rebuild boundaries for this package

## Spec Kit workflow record

This package completed `$speckit-tasks`, `$speckit-analyze`,
`$speckit-implement`, and `$speckit-converge` as retrospective documentation.
