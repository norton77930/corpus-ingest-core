# Research: Multi-Document Study Guide

## Decision: one family, not four

- **Rationale**: a cover sheet must not look like a finished lecture. Index family counts have no `partial` bucket; per-episode `partial` maps to `unreadable` so it cannot become `available`.
- **Alternatives**: four families (rejected — 00 alone would count as progress); a single concatenated file (rejected — user target is the reading sequence).

## Decision: read the semantic summary, not the transcript

- **Rationale**: Principle IV names semantic summary as the only transcript-to-LLM path. The 037 run already extracted concepts, quotes, and uncertainties. A second transcript pass is a constitution change the operator declined.
- **Alternatives**: deterministic heading split (rejected — prototype 03/04/07 layouts do not match FR-014 1:1); second transcript pass (rejected).

## Decision: `complete()`, not a new protocol method

- **Rationale**: `SemanticSummaryProvider` already exposes `complete`. Adding `summarize_study_guide` would break the five fakes. Building a second factory would bypass `_PROVIDER_FACTORY_TOKEN`.
- **Alternatives**: extend `summarize_final` (rejected — wrong meaning); call `requests` directly (rejected — ack/token bypass).

## Decision: do not add `study_guide` to `ARTIFACT_LADDER`

- **Rationale**: 009/010 would otherwise invent a generate action and then fail or call the wrong function. v1 is a standalone runner.
- **Alternatives**: optional gated ladder entry (successor spec, if operators want remediation to propose it).

## Decision: `STUDY_GUIDES_DIR`, not `data/notes/`

- **Rationale**: `data/notes/gooaye/EP678-analysis.md` is an unrelated hand file. Reusing `notes` would mix identities.
- **Alternatives**: live under `summaries/` with extra suffixes (rejected — glob rules for `.semantic.md` are already delicate).

## Decision: one LLM call emitting three Markdown bodies as JSON

- **Rationale**: keeps cost to one completion; lets the runner validate headings and refuse 05/06 leakage before any write.
- **Alternatives**: three calls (higher cost, partial-write risk); one concatenated Markdown with sentinels (weaker validation).
