# Feature Specification: Ingestion Transcript Core

**Feature Branch**: `002-ingestion-transcript-core`
**Created**: 2026-06-30
**Status: Backfilled / As-built**

**Input**: Existing implemented behavior for RSS episode listing, episode lookup,
audio download, local transcription, transcript validation, extractive summary,
and storage contracts.

## Spec Kit workflow record

- `$speckit-constitution`: reviewed Phase 7C constitution, no amendment.
- `$speckit-specify`: this file records the as-built user-facing requirements.
- `$speckit-clarify`: no high-impact ambiguity; code, tests, and README are source of truth.
- `$speckit-plan`: design artifacts are captured in this package.
- `$speckit-checklist`: requirements quality checklist is in `checklists/requirements.md`.
- `$speckit-tasks`: retrospective trace tasks are in `tasks.md`.
- `$speckit-analyze`: checked for consistency against modules, scripts, and tests.
- `$speckit-implement`: docs/spec/tests only; no runtime change.
- `$speckit-converge`: package covers the current ingestion and transcript scope.

## User Scenarios & Testing

### User Story 1 - List and identify episodes (Priority: P1)

Users can list podcast episodes from configured feeds and resolve an episode by
reference before downstream processing.

**Independent Test**: `test_feed_reader.py` covers episode listing and lookup.

### User Story 2 - Create local audio and transcript artifacts (Priority: P2)

Users can download episode audio and create transcript artifacts through local
tooling without changing research-layer behavior.

**Independent Test**: `test_downloader.py` and `test_transcriber.py` cover file
paths, dependency errors, and failure cases.

### User Story 3 - Validate and summarize transcripts (Priority: P3)

Users can classify transcript status and create deterministic extractive
summaries from existing transcripts.

**Independent Test**: `test_validator.py` and `test_summarizer.py` cover valid,
missing, corrupt, incomplete, and summary output behavior.

## Functional Requirements

- **FR-001**: System MUST list episodes from configured podcast feeds.
- **FR-002**: System MUST resolve an episode by podcast id and episode reference.
- **FR-003**: System MUST download audio to the configured local artifact path.
- **FR-004**: System MUST transcribe local audio into transcript artifacts.
- **FR-005**: System MUST validate transcript status before summary or research use.
- **FR-006**: System MUST produce deterministic extractive summaries without LLM use.
- **FR-007**: System MUST preserve local artifact paths and source metadata.
- **FR-008**: System MUST surface missing audio, missing transcript, corrupt, or dependency errors clearly.

## Safety and Data Boundaries

- This package is deterministic and does not call LLM providers.
- `.env` is not required for deterministic ingestion, validation, or extractive summary.
- Research outputs that depend on transcripts inherit the transcript status boundary.
- no investment advice is produced by these functions.

## Success Criteria

- **SC-001**: Existing tests for feed reading, downloading, transcription, validation, and summary pass.
- **SC-002**: Users can identify whether a transcript is valid before downstream research steps.
- **SC-003**: Artifact paths remain stable for downstream cache, MCP, and research features.

## Assumptions

- Podcast feed configuration lives in `config/podcasts.yaml`.
- Transcription depends on local environment dependencies and may fail with explicit dependency errors.
- Existing artifacts remain local files under `data/`.
