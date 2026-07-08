# Research: Corpus Artifact Index

## Decision: Use local artifacts as the only episode source

**Rationale**: The feature is a local corpus status index, and project governance treats local artifacts as the source of truth. Reading RSS would add network variability and show episodes with no local corpus state. Reading SQLite would risk stale cache results and violate the requirement that the index not depend on cache rebuild state.

**Alternatives considered**:

- RSS plus local artifacts: rejected for v1 because feed availability and freshness would change output.
- SQLite cache first: rejected because cache is derived and may be stale.

## Decision: Always regenerate the corpus index

**Rationale**: A corpus status report becomes misleading when reused after local artifact changes. Regeneration is deterministic and cheap enough for local status use. Omitting `generated_at` keeps output stable for unchanged inputs.

**Alternatives considered**:

- Reuse unless `--force`: rejected because it encourages stale status artifacts.
- Require confirmation before writing: rejected because the write is a derived status artifact and performs no expensive or external side effect.

## Decision: Store status, counts, and paths only

**Rationale**: The index must help users understand corpus readiness without copying transcript text, evidence snippets, semantic summary body text, LLM prompt text, or raw LLM output. This preserves secret/no-leak boundaries and keeps the index compact.

**Alternatives considered**:

- Include evidence previews: rejected because it increases raw transcript and LLM-output boundary risk.
- Minimal readiness flags only: rejected because users need counts and paths to locate artifacts.

## Decision: Keep v1 per-episode only

**Rationale**: Audio, transcript, summaries, mentions, reports, mappings, and external boundary artifacts share episode identity. Stock-lens and synthesis artifacts are query-level and would require a separate inventory model.

**Alternatives considered**:

- Add separate stock-lens inventory section: deferred to a future feature after per-episode index shape is stable.
- Scan all `data/**` artifacts: rejected as too broad for a safe v1.

## Decision: Select latest semantic review deterministically

**Rationale**: Semantic review reports already use timestamped names and include review status plus check counts. The index can safely expose only metadata from the latest matching report without reading semantic summary body content.

**Alternatives considered**:

- Report only semantic summary path: rejected because later synthesis readiness depends on review status.
- Read semantic summary content: rejected because body content is not needed for status indexing.

## Decision: Do not add MCP tool in v1

**Rationale**: The current MCP surface is a reviewed 12-tool contract. Adding a corpus tool is useful later, but should follow once the core/CLI artifact contract is proven.

**Alternatives considered**:

- Add MCP tool immediately: rejected because it expands the reviewed MCP registry and documentation surface.
- Add docs-only placeholder: unnecessary for the v1 implementation plan.
