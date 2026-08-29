# Ingestion Transcript Core Implementation Plan

**Status: Backfilled / As-built**

## Summary

This package records the current ingestion and transcript foundation. It covers
episode listing, episode lookup, audio download, local transcription, transcript
validation, deterministic extractive summary, and storage contracts.

## Technical Context

- Language: Python package with thin CLI scripts.
- Core modules: `feed_reader.py`, `downloader.py`, `transcriber.py`,
  `validator.py`, `summarizer.py`, `storage.py`, `models.py`, `config.py`,
  `errors.py`.
- CLI/scripts: `list_episodes.py`, `download_episode.py`,
  `transcribe_episode.py`, `validate_transcript.py`, `summarize_episode.py`.
- Tests: `test_feed_reader.py`, `test_downloader.py`, `test_transcriber.py`,
  `test_validator.py`, `test_summarizer.py`, `test_contracts.py`.

## Constitution Check

- dry-run: download and transcription side-effect tools are represented in CLI/MCP planning layers where applicable.
- exact `api_cost_ack`: not applicable; this package does not call LLM providers.
- secret boundary: `.env` is not read for deterministic ingestion and transcript validation.
- external-data boundary: no live market API.
- evidence separation: transcript status and local artifacts are source foundations for later podcast evidence.
- investment safety: no investment advice.
- manual cache rebuild: transcript changes do not automatically rebuild SQLite cache.
- targeted tests: covered by package tests listed above.

## Spec Kit workflow record

The workflow completed constitution review, specify, clarify, plan, checklist,
tasks, analyze, implement, and converge as an as-built documentation pass.

## Structure Decision

No runtime structure change. Existing core modules remain in
`src/corpus_ingest_core`, and scripts remain thin wrappers.
