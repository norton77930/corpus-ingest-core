# Research: Corpus Local Transcription Runner

## Decision: Dry-run is selection-only and writes no artifacts

**Rationale**: The project constitution requires side-effect workflows to expose planned reads/writes and risks before execution. Dry-run report artifacts would be write side effects, and dry-run must not load transcription models.

**Alternatives considered**:

- Write dry-run report artifacts for audit: rejected because it violates dry-run no-write behavior.
- Load transcription model during dry-run to validate readiness: rejected because model loading is expensive and not needed to inspect local artifact state.

## Decision: Selection is local-audio and transcript-missing only

**Rationale**: The feature's goal is to safely unlock downstream 010 deterministic remediation by filling missing transcripts when audio already exists. Corrupt, unreadable, partial, or incomplete transcript states need overwrite/repair policy and are out of scope.

**Alternatives considered**:

- Include corrupt transcripts with `force`: rejected for v1 because it risks overwriting user-managed files.
- Include partial/incomplete transcripts: rejected because completion semantics and backup behavior need a separate feature.

## Decision: Confirmed execution requires one episode reference

**Rationale**: Transcription may be long-running and hardware-dependent. Requiring one explicit episode keeps blast radius, runtime, and failure analysis bounded.

**Alternatives considered**:

- Allow `max_actions` batches: rejected for v1 because it introduces batch policy and resource scheduling questions.
- Allow action-family execution for all transcripts: rejected because it is too close to full corpus auto-repair.

## Decision: Confirmed execution passes explicit local audio path

**Rationale**: Existing `transcribe_episode()` falls back to audio resolution/download when no `audio_path` is provided. Passing the refreshed local audio path preserves the no-download boundary.

**Alternatives considered**:

- Call existing CLI script: rejected because repository architecture requires thin CLI and thick core.
- Call `transcribe_episode()` without `audio_path`: rejected because it could trigger download behavior.

## Decision: Rejected episode requests are auditable after selection

**Rationale**: If a user confirms a specific episode that is not eligible, returning a metadata-only result with a rejected/skipped row is more useful than a generic error. Missing episode filter remains a hard error because no bounded target exists.

**Alternatives considered**:

- Raise for every non-selected episode: rejected because it hides refreshed selection context.
- Write reports for dry-run rejections: rejected because dry-run must not write.

## Decision: CLI/core only, no MCP in v1

**Rationale**: Transcription is a side-effectful, potentially long-running local process. Keeping v1 local CLI/core avoids changing reviewed MCP tool counts and response envelopes.

**Alternatives considered**:

- Add MCP tool immediately: rejected because MCP side-effect policy and long-running process behavior need separate review.
- Embed in 010 runner: rejected because 010 intentionally promises deterministic-only execution and excludes transcription.
