# Feature Specification: Latest Episode Verified Research Report Workflow

**Feature Branch**: `018-latest-episode-verified-research-report-workflow`

**Created**: 2026-07-21

**Status**: Implemented; post-review controls specified below and verified by repository tests.

**Input**: Complete one verified research report for a configured podcast's latest episode only after an episode-scoped confirmation.

## User Scenarios & Testing

### User Story 1 — Safe Preview and Approval (P1)

An operator previews the current latest episode. Preview resolves it once and returns a strict zero-write plan, canonical reference, risks, and the required acknowledgement. A confirmed request must supply that exact `expected_episode_ref` and exact `api_cost_ack` before RSS, environment/provider access, writers, or child stages.

**Acceptance scenarios**:

1. Given `confirm=False`, when preview runs, then it writes no checkpoint, staging directory, report bundle, or child artifact.
2. Given a missing, altered, or drifted `expected_episode_ref`, or a non-exact acknowledgement, when confirmation is requested, then the request is rejected before any owned side effect. A latest-reference drift is an approval-boundary rejection: it creates or updates no expected/latest checkpoint, claim, staging, or bundle path.

### User Story 2 — Produce One Reviewed Report (P1)

After confirmation, the Core reuses the 017 pinned deterministic ladder, creates a semantic summary only when missing, requires deterministic semantic review status exactly `passed`, and calls the deterministic research workflow with fixed safe options. It then publishes one deterministic report bundle.

**Acceptance scenarios**:

1. Given valid pinned artifacts and a passed review, when research completes, then `report.json`, `report.md`, and `manifest.json` publish atomically under the digest-versioned destination.
2. Given summary/review is absent, the required single child action runs; given a non-passed review, research and publishing do not run.

### User Story 3 — Resume Without Repeating Work (P2)

A later explicit confirmation inspects canonical artifacts and its checkpoint. It adopts a complete matching bundle, resumes only incomplete safe stages, and never reuses conflicting or stale content.

**Acceptance scenarios**:

1. Given identical sources and an existing valid manifest, the bundle is reused without a second publication.
2. Given changed sources or a conflicting final directory, publication fails closed.
3. Given a later authentic timestamped semantic review with identical bytes but a different canonical review path, assembly records that path provenance, produces a new digest-versioned bundle, and does not conflict forever with the earlier bundle.

## Safety and Data Boundaries

- Preview is strict zero-write: it creates, modifies, and deletes zero files.
- Confirmed work is episode-scoped through exact `expected_episode_ref` and exact `api_cost_ack`; acknowledgement validation occurs before RSS, environment, provider, writer, or child-stage access.
- The workflow uses no live market API. Optional external verification is local fixture verification only.
- Verified facts require a valid timestamp and non-null segment identifier. Reviewed narrative, deterministic inference, external status, and podcast-wide stock appendix remain separately classified.
- Report output excludes raw transcript bodies, secrets, credential assignments, URI query/fragment data, and traceback text.
- There is no retry, scheduler, batch, force, output-path override, automatic cache rebuild, or investment advice.

## Requirements

- **FR-001**: The Core MUST expose `run_latest_episode_verified_research_report_workflow` with `confirm=False` default.
- **FR-002**: Preview MUST resolve latest at most once and be strict zero-write.
- **FR-003**: Confirmed execution MUST reject missing, mismatched, or drifted `expected_episode_ref` and non-exact `api_cost_ack` before protected access. A drift rejection is outside the approval boundary and MUST make zero owned writes, including no checkpoint, claim, staging, or bundle for either expected or resolved episode.
- **FR-004**: The workflow MUST reuse the package-private pinned 017 deterministic helper and preserve the 017 public contract.
- **FR-005**: Semantic summary MAY run once only when missing; semantic review MUST have exact `passed` status before research or publication.
- **FR-006**: Research MUST use `force=False`, `allow_partial=False`, `include_semantic_summary=False`, and `include_stock_lens_synthesis=False`; fixture verification is the only optional external path.
- **FR-007**: The assembler MUST validate source identity and timestamp/segment provenance, calculate a source digest that includes each source's canonical normalized path and immutable bytes, and set report version `v1-{source_digest}`. Manifest provenance MUST retain the selected source path so a path-distinct authentic review creates an auditable new version rather than a permanent destination conflict.
- **FR-008**: Publication MUST write `report.json`, `report.md`, and `manifest.json` in a same-filesystem staging directory, verify hashes, then atomically rename; identical bundles are reused and conflicts fail closed.
- **FR-009**: Checkpoints MUST be metadata-only, bounded to the canonical episode, and support artifact-driven resumption/adoption without overriding source truth.
- **FR-010**: The CLI, fifteenth MCP tool, portable Skill, setup validator, registry, and governance documentation MUST preserve dry-run-first, manual approval, no live market API, and no investment advice boundaries.
- **FR-011**: Existing 015, 016, 017, and research workflow contracts MUST remain compatible.
- **FR-012**: A reusable final directory MUST contain exactly `report.json`, `report.md`, and `manifest.json`; each report file MUST equal the deterministic assembly bytes and the manifest MUST equal the full expected identity, options, sources, quality gates, and file metadata. Coordinated report/manifest tampering and destination races fail closed unless the raced directory independently satisfies this full comparison.
- **FR-013**: Adoption MUST first require `validate_transcript(...).status == "valid"`, all TXT/SRT/JSON outputs, and transcript identity. Invalid artifacts cannot yield `completed` or `reused` and proceed through the pinned 017 gate instead.
- **FR-014**: Semantic review artifacts MUST include additive `semantic_summary_sha256` for the reviewed summary bytes. A passed review is current only when its timestamped artifact has matching identity and SHA-256; missing, mismatched, or non-timestamped review artifacts require one safe re-review or fail closed.
- **FR-015**: Source text and public result metadata MUST reject or omit AWS credential assignments, private-key headers, credential/token/password assignments, unsafe URI data, and non-serializable values. A source safety violation prevents final report publication.
- **FR-016**: The publisher MUST revalidate every source after staging validation and immediately before rename. Checkpoints MUST be safely read/validated/merged, use invocation-unique temporary names, record bounded terminal outcome and bundle references, and remain subordinate to artifact truth.
- **FR-017**: Every public input MUST have strict type, size, secret, path, and URI validation. `include_fixture_verification` MUST be represented in canonical assembly options, source digest, and manifest.
- **FR-018**: Timeline and stock appendix output MUST preserve sanitized readable evidence with classification and provenance; stage/inspection/checkpoint/child failures MUST be bounded terminal metadata with category-only failures.
- **FR-019**: Assembly MUST acquire each report source as one immutable byte snapshot. Parsing, source safety, semantic-review hash binding, rendering, source digesting, and manifest provenance MUST derive from that snapshot; any final publish, reuse, or destination-race success MUST first prove each on-disk source still equals its snapshot.
- **FR-020**: Semantic review authenticity belongs to the neutral artifact domain shared by the 015 writer, corpus index, and 018. A usable artifact MUST have the fixed review mode and boundary, canonical identity, current summary hash, expected unique check set, status/count consistency, and a canonical timestamped or timestamped collision filename. A matching hash alone is insufficient.
- **FR-021**: Checkpoint readers MUST retain validated source digest, report version, and bundle references during intermediate stage merges. Every confirmed canonical terminal outcome (`completed`, `reused`, `blocked`, `failed`, `rejected`, or `manual`) MUST use the common checkpoint finalizer, except an approval-boundary drift rejection, which the finalizer MUST explicitly recognize as zero-write; persistence failure remains a bounded warning only.
- **FR-022**: Source safety MUST reject quoted JSON/YAML credential assignments. Stock appendix direct evidence, inferred leads, and verification details MUST retain sanitized structured production-schema fields; in particular `required_external_checks` is rendered as readable labels/structured values, never `str(dict)`.
- **FR-023**: The neutral semantic-review inspector MUST recompute the exact canonical checks, messages, status, and counts from immutable current canonical-summary bytes. A payload with correct identity, mode, boundary, and hash but forged all-pass results is not authentic. `Bearer <token>` (case-insensitive standard token syntax) is unsafe source text.
- **FR-024**: Semantic summary identity MUST use the sole path constructed from the title in the identity-validated transcript. Same-episode title variants are stale candidates, not lexicographic fallbacks, across 015, corpus index, and 018.
- **FR-025**: Reuse and destination-race success MUST remain inside a per-bundle exclusive claim and revalidate canonical bundle bytes, manifest, and immutable sources again before success returns. Bundle and checkpoint claims MUST be process-lifetime OS locks (Windows byte-range locking; POSIX advisory locking or an equivalent portable abstraction); their lockfiles may persist after close/crash and MUST NOT be reclaimed by unconditional mtime deletion. Checkpoint read/validate/merge/replace MUST use the per-episode claim; a late old failure cannot downgrade completed/reused bundle metadata.
- **FR-026**: Reserved latest selectors are casefold-rejected at confirmed 016 and 018 Core/MCP early gates before RSS, snapshot, checkpoint, writer, executor, or child dispatch.
- **FR-027**: After canonical drift approval succeeds and before child stages, the Core MUST reserve an episode-local monotonic integer `invocation_generation` under the checkpoint OS claim. Every confirmed checkpoint write MUST carry that reservation. Inside the checkpoint critical section, an older successful generation may merge bounded history but MUST NOT overwrite digest, version, references, or successful-terminal metadata from a higher successful generation. Legacy checkpoints without generation remain readable as generation zero.
- **FR-028**: Neutral semantic-review evaluation and verified-report assembly MUST share only lower-level deterministic safety policy and storage domains. They MUST NOT import stock-lens synthesis, providers, or LLM modules. The common advice guard rejects direct personalized English/Chinese buying, selling, or holding recommendations (including `You should`, `I recommend`, `consider buying`, `推薦/建議/值得買進或賣出` variants), while allowing an explicitly attributed same-line quoted historical transcript reference only when an attribution precedes a matching quote pair.
- **FR-029**: 018 reuse/adoption/assembly MUST pass an explicit lineage-quality gate stored in its owned sidecar. Each required derived role records its canonical direct-upstream path and SHA-256, its own canonical path and SHA-256, and output-affecting mode/options. Lineage MUST never be inferred from mtime or artifact existence. A missing, legacy, mismatched, or ambiguous lineage record MUST block or safely regenerate at the first affected stage; it MUST NOT be adopted through force, partial mode, or retry.
- **FR-030**: The required chain is transcript → semantic summary → semantic review; transcript → mentions → intelligence → industry mapping → external boundary; plus optional fixture verification and stock lens. A transcript-byte mutation at the same path invalidates every dependent role. A fixture marker MUST bind current fixture path/SHA-256 and pre-verification boundary path/SHA-256. A stock-lens record MUST bind the complete canonical mapping/boundary corpus input set. Fixture-enabled assembly, adoption, and publication require a current valid fixture record and MUST block stale boundary/fixture lineage.
- **FR-031**: Lineage recording MAY progress only for source artifacts generated or independently validated during the current controlled workflow. It enables safe resumption after an incomplete later stage, but MUST NOT retroactively bless pre-existing derived artifacts. A complete current new-schema sidecar/manifest/source chain may be adopted without a checkpoint.
- **FR-032**: Before provider construction, LLM access, or fixed-path child writes, confirmed same-episode work MUST acquire one process-lifetime episode-workflow OS claim and re-inspect artifacts inside that claim. The claim MUST close same-process thread re-entry as well as cross-process contention; different episodes remain parallel, and the per-bundle claim remains required.
- **FR-033**: A corrupt, unreadable, or identity-invalid checkpoint is untrusted subordinate metadata. It MUST NOT veto valid complete artifact/bundle adoption. When no valid artifact truth is available, the workflow MAY atomically replace it with bounded generation-zero recovery state under the episode claim without retaining untrusted references/history.
- **FR-034**: Lineage-sensitive 017/018, semantic identity, and assembly selection MUST use a shared strict canonical transcript resolver. It accepts one identity-valid transcript or an explicit trusted external corpus episode seed. Multiple identity-valid same-episode title variants without that unique seed selector are ambiguous and fail closed; 018 lineage and bundle manifests are derived outputs and MUST NOT select a transcript; lower-level lexical storage discovery remains backward compatible.

## Key Entities

- **Canonical episode snapshot**: The latest episode reference resolved once for preview or a confirmed request.
- **Workflow checkpoint**: Metadata-only stage history at `data/corpus/{podcast_id}/verified-research/{episode_ref}.checkpoint.json`.
- **Verified report assembly**: Identity-validated source artifacts, classified report payload, source digest, and report version.
- **Verified report bundle**: The atomic JSON, Markdown, and manifest directory under `data/research-reports/{podcast_id}/{episode_ref}/`.

## Success Criteria

- A valid preview makes zero writes and a malformed confirmation reaches no protected dependency.
- Every report fact with podcast timeline evidence contains a valid timestamp and segment ID.
- Identical input produces identical report content/version and reuses an existing valid bundle.
- A changed source or conflicting final bundle fails closed.
- The MCP registry contains exactly 15 reviewed tools with the prior fourteen contracts and order preserved.
- The workflow provides no investment advice and uses no live market API.
