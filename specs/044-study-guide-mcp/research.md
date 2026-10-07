# Research: Safe Study-guide MCP Access

**Date**: 2026-10-02 | **Baseline**: `b42b5a2` | **Method**: repository-local source inspection; two read-only research roles, one document writer. No external research, real corpus writes or provider calls.

## R1 — Expose the existing Core, one operation at a time

**Decision**: Tool 26 is `generate_study_guide_bundle`; it delegates exactly once to `run_study_guide_bundle`. It does not generate a missing summary or call Tool 25.

**Evidence**: `study_guide_bundle.py:46` already owns generation; `mcp_tools_workflow_derivation.py:30` and `mcp_server.py` demonstrate the append-only group pattern. Live registry was inspected at 25 with no study-guide tool.

**Rationale**: Close the missing agent entry point without introducing orchestration or another artifact family.

**Alternatives rejected**: a single ingest→summary→lecture→derivation tool changes approval and cost boundaries; a Skill calling CLI would not expose the missing MCP capability.

## R2 — Preserve schema; project plan metadata inside Core

**Decision**: Keep `StudyGuideBundleResult`, `result_to_dict`, CLI success output and report schemas unchanged. Add a Core-module pure `describe_study_guide_plan(result)` projector returning `requires_llm` and `report_writes`. It intersects full paths from `planned_writes` with the canonical `03/04/07` paths under `result.bundle_dir`; storage computes the two report paths. It reads no files and resolves no provider.

**Evidence**: `study_guide_bundle.py:87–111` already decides full reuse, cover-only and generation; `models.py:1447` has the established result; `storage.py:606` computes report paths without I/O.

**Rationale**: Metadata is derived from the existing authoritative plan. The wrapper does not duplicate readiness checks or infer work from independent filesystem probes.

**Alternative rejected**: additive dataclass fields would also change CLI and report serialization for a feature that only needs new MCP metadata. Basename-only matching is too weak; compare the full Core-derived paths.

## R3 — Cover-only is a byte-preserving operation

**Decision**: Snapshot/preserve safe regular files as bytes; overlay only `00` for cover-only, and the four owned lecture files for an allowed generation. Never decode/re-encode files selected for reuse. Reject unsafe entries rather than silently skipping them.

**Evidence**: `_atomic_write_bundle` at `study_guide_bundle.py:395` stages only supplied files; existing cover-only reads `03/04/07` as text at line 139 and later rewrites all four. `workflow_derivation.py:276` is a directory-swap precedent, but its `is_file()/copy2()` loop is not a no-follow safety policy. The initial isolated probe lost both derivation sentinels.

**Rationale**: Keeping text semantically equal is insufficient when the acceptance criterion is byte preservation. The directory is shared by two artifact families.

**Alternative rejected**: blindly copying all directory entries could follow links; keeping only known lecture files deletes unrelated content; updating individual live files exposes a mixed set on partial failure.

## R4 — Refuse upstream generation while derivations exist

**Decision**: Any exact `05_prompt_examples.md` or `06_apply_to_my_workflow.md` entry blocks a branch that would regenerate `03/04/07`, including force. Reuse and cover-only remain allowed after safety checks. No automatic deletion, renaming, invalidation or regeneration of derivations.

**Evidence**: `storage.py:569,584` puts both families in the same directory; no source-digest relationship currently validates derivation freshness.

**Rationale**: Preserving obsolete downstream bytes and presenting them as current would replace data loss with a false lineage claim.

**Alternative rejected**: adding digest manifests or versioned directories is separate lifecycle work, not required to expose one tool safely.

## R5 — Recovery remnants block entry; publication has a commit point

**Decision**: Pre-existing sibling `.part`, `.old`, `.wfderive.part`, `.wfderive.old` entries cause zero-write refusal in every mode. Use lstat/existence-without-following so dangling links count. A complete staging-to-destination rename is the commit point. Before it, restore old bytes if rollback succeeds; if rollback fails preserve recoverable old/staging. After it, cleanup/report failure leaves the complete published bundle and emits a fixed stage-specific error. No automatic retries.

**Evidence**: `study_guide_bundle.py:400–419` performs recovery only inside the publisher, after generation; that is too late to see `05/06` in an old directory. `run_report_io.py:24,40–41` deliberately uses a weak two-file report protocol, separate from bundle publication.

**Rationale**: The original draft's unconditional rollback wording was impossible after commit or when rollback itself fails. This plan preserves those facts instead of promising a filesystem transaction across bundle and reports.

**Alternative rejected**: recovering before preview violates zero-write; deleting pre-existing staging loses history; redesigning shared recovery is outside scope. The low-level legacy helper need not become a general recovery manager.

## R6 — Use safe identity reads locally, keep shared resolvers unchanged

**Decision**: In study-guide Core only, reuse `resolve_canonical_transcript_asset_paths`, securely snapshot its selected JSON under `TRANSCRIPTS_DIR` with the existing 64 MiB canonical bound, validate identity/title, then call `canonical_semantic_summary_path_for_title`. Read the summary through `secure_read_bytes` under `SUMMARIES_DIR` with the existing 2 MiB summary bound. Reject invalid/unsafe candidates; never retry with plain text reads. Only title/identity is consumed from transcript metadata; transcript text is never sent to the provider.

**Evidence**: `canonical_transcript.py:65–83` has secure selection plus a malformed single-candidate fallback; `semantic_summary_identity.py:32` rereads the selected JSON with plain `read_text`. `secure_local_snapshot.py:44,106,207,273` supplies no-follow snapshot/listing, ancestor and reparse checks.

**Rationale**: Preflight followed by the old unsafe reread would not satisfy FR-013. A small local adapter preserves selection rules without changing other workflows.

**Alternative rejected**: changing the shared resolver changes other tools; reimplementing selection with glob can choose a stale title. No new shared API or changes to `models.py`, `canonical_transcript.py`, `semantic_summary_identity.py` or `secure_local_snapshot.py` are planned.

## R7 — Safe errors are local to the new tool

**Decision**: New state/publication failures use a `StudyGuideBundleStateError` subclass carrying a finite `reason_code`; MCP maps known codes and known exception classes to literal messages. It never returns `str(exc)` or repr. Unknown codes/exceptions use a fixed generic response. Existing Tool 1–25 error handling stays unchanged.

**Evidence**: `mcp_runtime.py:163–174` passes exception messages through; `_redact_text(text, None)` at line 197 does not redact. Existing Core validation/provider exceptions can contain source-derived text.

**Rationale**: Redacting recognizable credentials is not sufficient to remove arbitrary summary/prompt bodies. A finite mapping can be tested with hostile marker strings.

**Alternative rejected**: replacing global `_tool_call` would alter unrelated public contracts; classifying failures by parsing exception text is fragile and may leak content.

## R8 — Integration is broader than one registry assertion

**Decision**: Append the group/export; update the setup validator, installed command count, fixed-slot Tool25 tests and live documentation together. Preserve historical counts and old tool order. Use the exact inventory in plan.md.

**Evidence**: `validate_mcp_setup.py:230`, `test_console_entry_points.py:31`, `test_mcp_workflow_derivation.py:206–215` each have an independent pin. `test_docs_registry_count_consistency.py` derives the count dynamically and should not be weakened.

**Rationale**: A server that works in-process but exposes the wrong installed registry is not a finished entry point.

## Resolved Limits

No new dependencies, provider configuration, network preview, Skill, background work, lineage manifest or concurrent-writer guarantee. Operations are serialized for one episode. Native filesystem failures and runtime semantic quality remain limitations; synthetic tests prove contracts, not real-provider output quality.
