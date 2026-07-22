# Data Model: Latest Episode Verified Research Report Workflow

## Input

`LatestEpisodeVerifiedResearchReportWorkflowRunFilter` captures only bounded controls: optional podcast-wide `stock_query`, optional local fixture verification, local transcription settings, and existing semantic settings. It never accepts a path override, force, partial mode, retry, scheduler, or live provider control.

A confirmed request additionally carries `expected_episode_ref` and exact `api_cost_ack`. The acknowledgement is validated before protected dependencies; no live market API and no investment advice are permitted.

## Run Result

`LatestEpisodeVerifiedResearchReportWorkflowRunResult` is immutable metadata containing podcast ID, run mode, canonical episode reference, expected reference, outcome, required acknowledgement, source digest/version, bundle and checkpoint paths, ordered plan, warnings, and explicit no-investment-advice marker.

## Checkpoint

The metadata-only checkpoint is `data/corpus/{podcast_id}/verified-research/{episode_ref}.checkpoint.json`. It records canonical identity, validated/merged bounded stage history, source digest/version when known, `terminal_outcome`, bounded bundle references, `invocation_generation`, and the highest successful generation. It uses an invocation-unique temporary name and a process-lifetime OS episode claim; its persistent lockfile is not a liveness marker. Generation comparison occurs while that claim is held, so a late older success can add history but cannot replace newer successful bundle metadata. Artifact inspection, sidecar lineage validation, and manifest verification precede checkpoint reservation and override stale/corrupt checkpoint claims. An unreadable, identity-invalid, or malformed checkpoint is replaced only with bounded generation-zero recovery state when valid artifact truth is unavailable. An approval-boundary drift creates no checkpoint. The checkpoint contains no raw transcript, source body, secret, URI query/fragment, traceback, or provider credential.

## Source Artifact

Each `VerifiedResearchSourceArtifact` includes role, local path, SHA-256, size, and identity-valid flag. Roles are limited to transcript identity, semantic summary, semantic review, mentions, intelligence, industry mapping, external boundary, optional fixture, and optional stock lens. Canonical podcast/episode identity must match. A source digest is calculated from schema version, canonical identity, normalized stock query, `include_fixture_verification`, verification scope, and each source role/canonical-normalized-path/hash/size. The manifest retains the selected safe source path as auditable provenance, so a path-distinct authentic semantic re-review receives a distinct version even when bytes are identical. A review artifact additionally binds `semantic_summary_sha256` to the current semantic-summary bytes.

## Verified Research Lineage

`data/corpus/{podcast_id}/verified-research/{episode_ref}.lineage.json` is the 018-owned provenance sidecar using schema `latest-episode-verified-research-lineage-v2`. It has canonical podcast/episode identity, explicit no-investment-advice marker, and one entry per trusted role. Each entry contains the canonical local artifact path, SHA-256, direct-upstream path/SHA-256 references, meaningful mode/options, and the controlled generation proof (`expected_path`, pre/post SHA-256, and execution kind). Semantic options record the actual provider/model declared by immutable summary metadata and a SHA-256 base-URL identity rather than the raw URL. It is not a legacy schema migration and does not change lower-level storage contracts.

The transcript is the canonical root. Semantic summary references transcript; semantic review references semantic summary; mentions reference transcript; intelligence references transcript and mentions; mapping references intelligence; and boundary references mapping. Fixture verification references a pre-verification boundary snapshot and records canonical current fixture path/SHA-256 plus fixture verification mode. Stock lens references a sorted canonical SHA-256 mapping/boundary corpus input set. The report manifest copies the validated sidecar view and records `lineage_quality_gate: "passed"` and the sidecar schema version.

A role may be recorded progressively only after controlled generation or independent validation. Validation recomputes the role and its direct upstreams; any missing/mismatched path, bytes, mode/options, identity, fixture, stock input, or canonical transcript selection fails closed. Legacy artifacts with no entry are not trusted merely because they exist.

## Assembly and Bundle

`VerifiedResearchReportAssembly` contains a deterministic payload, Markdown rendering, manifest metadata, source digest, report version `v1-{source_digest}`, and final paths. `VerifiedResearchReportBundle` records the published/reused directory and the three verified files:

```text
data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/
  report.json
  report.md
  manifest.json
```

`report.json` separates `verified_podcast_fact`, reviewed LLM narrative, deterministic inference, external status, and a podcast-wide appendix. A source digest changes when source content or canonical normalized source provenance changes. Timeline facts require a valid `[HH:MM:SS - HH:MM:SS]` timestamp and non-null segment ID.

`manifest.json` records schema/report version, safe source metadata, quality gates, verification scope, and bundle hashes, not artifact bodies. Atomic publication reuses only hashes matching the same source digest; conflicts fail closed. This preserves no live market API and no investment advice.
