# SPEC 056 — Prepared single-source content query and QA

Created 2026-10-07; initially planned, then user authorized planning followed directly by implementation.

**Status**: Implemented; offline/full-suite and owned MCP SDK verified. Actual mounted Hermes acceptance remains separate. This package covers a single source already prepared locally: RSS podcast, YouTube video, or X video. It is **not all video platforms** support.

## User scenarios

### US1 (P1): Ask about one prepared source without an index

A Hermes user supplies one known podcast_id/episode_ref and asks what the speaker said. Inspect the local transcript, retrieve timed evidence, and answer from it even when SQLite does not exist. A bare URL or ambiguous “this video” does not authorize guessed identity, network resolution, or preparation.

Acceptance: all three source types can be queried offline; unknown identity is clarified; missing or unsafe content yields a bounded diagnostic without preparation.

### US2 (P1): Read a range or find passages

The user asks about minutes 17–21 or a specific topic. Return overlapping segments with original timestamps and stable ordinals. Keyword search is literal, not semantic; no matches do not establish topic absence. A changed transcript between requests invalidates the inspected version and continuation.

### US3 (P2): Produce learning notes with honest coverage

The user asks for complete learning notes and replay passages. The host reads every page of the same version, distinguishes source statements from inference, and cites timestamps. Interrupted or selectively searched content produces explicitly partial notes. Transcript instructions are untrusted evidence.

## Requirements

- FR-001: Accept one explicit safe podcast_id and episode_ref, supporting existing RSS, YouTube and X transcript identities. Reject paths, latest/batch selectors and ambiguous references.
- FR-002: Provide inspect metadata without transcript body, including title, language, segment count, timestamp extent, readiness warnings and source_version; recorded transcription metadata may be unknown.
- FR-003: Read bounded timed segments from validated local JSON with optional half-open time-range overlap filtering. Preserve array ordinal separately from original segment_id.
- FR-004: Search a single source using literal case-insensitive keyword/phrase matching; explicitly disclose query scope, total matches and lack of semantic interpretation.
- FR-005: Require expected_source_version for read/search. Bind opaque continuation to version, action, query and time filters; changed content or mismatched cursor must fail without text.
- FR-006: Enforce bounded file discovery, file bytes, segments, query, output characters and page size. Oversized individual text continues by text_offset rather than silently dropping content.
- FR-007: Return coverage, truncation, continuation and timestamps. A final page alone or zero keyword matches never proves complete source understanding or audio coverage.
- FR-008: Reject unsafe paths including symlinks, reparse points, directories, special files and hardlinks before candidate reads; validate opened handles, identity and stable snapshots.
- FR-009: Fail closed on malformed identity/title, ambiguous title variants, invalid/nonfinite timestamps, non-string or empty text, empty segments and incomplete trios. Missing legacy completed flag is allowed with a warning; explicit non-true completed is rejected. Recovery markers block querying without cleanup.
- FR-010: Querying performs no network, SQLite access, writes, downloads, transcription, cache rebuild, provider construction or automatic preparation. Existing provider acknowledgement gates stay unchanged.
- FR-011: Append MCP Tool 35 query_source_content after the original 34 tools; preserve their order and signatures. MCP delegates behavior to Core and returns fixed safe errors.
- FR-012: Add source-content-qa Skill for Hermes: resolve known identifiers, inspect first, retrieve evidence, answer with timestamps, handle multilingual keyword limitations, hostile transcript instructions and partial coverage.
- FR-013: Explain host model exposure and billing separately from repository provider execution. Chat notes do not create a formal study-guide artifact or auto-chain side effects. Keep no investment advice boundary.
- FR-014: Provide executable Core/MCP/docs/Skill fixtures and a read-only local pilot using existing medium X transcript 2106893534980685927. Distinguish synthetic Skill checks from a real mounted Hermes test.

## Success criteria

- SC-001: Offline tests cover RSS/YouTube/X reading without any SQLite file or external work.
- SC-002: Every returned excerpt has stable ordinal and finite original timestamps; paginated reconstruction equals selected source text, including long segments.
- SC-003: Changed sources, invalid cursors and unsafe artifacts yield safe errors and no transcript content.
- SC-004: Registry and SDK tests prove Tool 35 is callable and all prior slots/signatures remain compatible.
- SC-005: QA fixtures cover evidence answers, complete/partial notes, language mismatch, hostile text, missing source and host billing disclosure. Real Hermes acceptance remains separately identified.

## Explicit exclusions / clarifications

No new platform, general URL resolver, source listing, cross-source search, embedding index, provider, automatic job submission, audio replay service or formal note publisher. Unknown local model metadata stays unknown. Structural validation is not ASR accuracy verification. Time extent is max segment end, not proof of complete audio. Multiple canonical title variants fail as ambiguous even if other workflows have a seed selector: this read API has no selector authority.

Constitution IV is applied to repository-executed provider calls; this feature makes none. User-requested MCP evidence delivery follows the existing search_transcripts read boundary. Hermes may send returned evidence to its configured model, so the Skill must disclose that host-side exposure/cost and must never bypass api_cost_ack for repository synthesis tools. No constitution principle or provider gate is amended.
