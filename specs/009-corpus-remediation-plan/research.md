# Research: Corpus Remediation Plan

## Decision: Refresh the 008 corpus index before planning

**Rationale**: The corpus index already centralizes deterministic local artifact discovery, missing artifact families, unreadable JSON warnings, duplicate candidate selection, and latest semantic review metadata. Refreshing it first prevents remediation planning from using stale status.

**Alternatives considered**:

- Scan every artifact family directly again in the remediation module. Rejected because it would duplicate 008 discovery logic and create drift risk.
- Read the existing corpus index without refreshing. Rejected because the user explicitly wants fresh status before action planning.
- Use SQLite cache or RSS to find episodes. Rejected because v1 must be local artifact only and cache independent.

## Decision: Use a full-ladder per-episode remediation action model

**Rationale**: The requested scope includes upstream and downstream gaps. A single ordered ladder makes blockers explainable and keeps action generation deterministic: audio, transcript, extractive summary, mentions, semantic summary, semantic review, episode intelligence, industry mapping, external boundary.

**Alternatives considered**:

- Downstream-only planning after transcript. Rejected because the user chose Full Ladder.
- Research-only planning. Rejected because it would hide audio/transcript gaps that explain downstream blockers.
- Query-level stock-lens planning. Rejected because stock-lens artifacts are not per-episode remediation targets in v1.

## Decision: Advisory action text only, no execution

**Rationale**: The remediation plan is a derived planning artifact. It may show factual command examples or dry-run-style suggestions, but the feature itself must not download, transcribe, generate summaries, call workflow steps, call LLM providers, invoke MCP tools, or rebuild cache.

**Alternatives considered**:

- Execute the first available repair step. Rejected because it would violate the no-execution boundary and require confirmation semantics outside v1.
- Use confirmed research workflow from this feature. Rejected because v1 is plan-only and must not perform side effects.
- Hide command examples entirely. Rejected because the user requested command-oriented next actions.

## Decision: Keep semantic remediation optional and gated

**Rationale**: Semantic summary can involve transcript transfer to an external LLM in existing flows, and review artifacts contain LLM output quality metadata. The plan should show semantic gaps without making those actions appear deterministic or immediately safe.

**Alternatives considered**:

- Treat semantic summary like a deterministic artifact. Rejected because it has LLM cost and privacy boundaries.
- Omit semantic actions. Rejected because 008 already reports semantic summary and semantic review status.
- Include exact runnable LLM commands with acknowledgement text. Rejected because plan output should not encourage accidental provider calls.

## Decision: Core plus CLI only

**Rationale**: Existing project rules keep runtime behavior in `corpus_ingest_core` and keep CLI wrappers thin. v1 has no MCP surface change, and the reviewed MCP tool count must remain unchanged.

**Alternatives considered**:

- Add an MCP tool for remediation planning. Rejected because v1 explicitly excludes MCP changes.
- Implement only a script. Rejected because the repository requires thick core and thin interface.

## Decision: Deterministic JSON and Markdown with no timestamp

**Rationale**: Users need to compare remediation plans across runs. Omitting `generated_at` and sorting rows/actions deterministically keeps unchanged corpus state diff-stable.

**Alternatives considered**:

- Include generation timestamp metadata. Rejected because the user explicitly requested no timestamp content.
- Markdown-only output. Rejected because the feature needs machine-readable and human-readable artifacts.
