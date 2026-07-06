# Research Workflow Orchestration Data Model

**Status: Backfilled / As-built**

## Entities

- ResearchWorkflowResult: dry-run or confirmed workflow metadata.
- ResearchWorkflowStep: planned or executed step with reads, writes, and risk flags.
- Artifact paths: generated or reused paths from mentions, reports, mappings,
  external boundary, stock lens, and synthesis steps.
- External API step: optional semantic summary or stock lens synthesis requiring acknowledgement.

## Boundaries

- Dry-run contains metadata and planned paths, not raw transcript dumps.
- Optional LLM steps must not construct providers without exact `api_cost_ack`.
- External fixture verification remains local and does not read API keys.
