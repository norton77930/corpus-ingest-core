# Research Notes: Latest Episode Verified Research Report Workflow

## Decisions

1. **Reuse pinned 017 work**. The package-private `_resolve_latest_episode` and `_run_pinned_deterministic_workflow` avoid duplicate stage ladders while retaining the 017 public contract.
2. **Approval precedes dependency access**. A confirmed request cannot use RSS, environment/provider, writer, or child stage before exact `expected_episode_ref` and exact `api_cost_ack` validation. Preview remains strict zero-write.
3. **Semantic gate is artifact-driven and summary-bound**. The centralized inspector accepts a review only when its timestamped JSON has matching identity, exact `passed`, and additive `semantic_summary_sha256` equal to current summary bytes. One missing/stale/spoofed review may be safely regenerated; normal non-passed reviews remain blocked.
4. **Research is deliberately constrained**. `run_research_workflow` receives `force=False`, `allow_partial=False`, `include_semantic_summary=False`, and `include_stock_lens_synthesis=False`. `include_external_data_verification` is optional only for local fixture verification. No live market API is available.
5. **Artifacts establish resume truth**. Adoption first verifies valid transcript readiness plus TXT/SRT/JSON and identity. Checkpoint metadata is safely read/merged/validated with terminal outcome and bundle references, but source artifact identity and final bundle validation decide whether work resumes, adopts, reuses, or fails closed.
6. **Digest represents source content and canonical options**. The digest includes source role/hash/size plus canonical identity, normalized stock query, `include_fixture_verification`, and verification scope. It is independent of wall-clock time.
7. **Atomic directory publication avoids partial final truth**. Staging and final directory share a parent filesystem. Validate staging, reread sources immediately before rename, and reuse only an exact three-file final bundle whose JSON/Markdown bytes and complete expected manifest match. A destination race uses this same independent match or fails closed.
8. **Evidence must remain classified**. Timeline facts require valid timestamp and segment ID. Reviewed narrative is labeled as LLM-generated, inference is deterministic, external status stays status-only, and any stock appendix is podcast-wide. The report provides no investment advice.

## Rejected Alternatives

- Re-resolving latest after confirmation: rejected because it permits target drift.
- Calling semantic summary/review from preview: rejected because preview must be strict zero-write and not access provider configuration.
- Passing force/partial/synthesis options through the public surfaces: rejected because it broadens side effects and the LLM boundary.
- File-by-file publication: rejected because readers could observe a partial bundle.
- Treating a checkpoint as authoritative despite missing/mutated sources: rejected because verified report identity must fail closed.

All decisions preserve exact `api_cost_ack`, `expected_episode_ref`, no live market API, and no investment advice.
