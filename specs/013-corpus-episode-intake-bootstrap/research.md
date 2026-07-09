# Research: Corpus Episode Intake Bootstrap

## Decision: Add a dedicated seed-only intake runner

**Decision**: Implement 013 as a separate corpus episode intake bootstrap runner instead of extending 012 audio download.

**Rationale**: The missing capability is corpus discovery, not downloading. 012 intentionally operates only on episodes already visible in local remediation metadata. A seed-only runner preserves 012's bounded audio side-effect contract while adding the upstream bridge from RSS metadata into local corpus state.

**Alternatives considered**:
- Extend 012 with `--episode latest`: faster for manual testing, but would mix RSS discovery and audio download concerns.
- Use `download_episode.py --episode latest`: already possible, but bypasses corpus remediation flow and does not create auditable intake metadata.

## Decision: Dry-run may read RSS but writes nothing

**Decision**: Dry-run resolves `latest` or an explicit episode through the configured feed reader, but does not write seed metadata, run reports, audio, transcripts, downstream artifacts, cache, or provider outputs.

**Rationale**: Intake exists to answer "what does this selector resolve to?" RSS access is necessary for useful preview. Keeping dry-run no-write preserves the side-effect boundary.

**Alternatives considered**:
- Dry-run cache-only: would avoid network but cannot reliably answer latest.
- Confirm-only RSS: would remove preview value and make confirmed execution less inspectable.

## Decision: Seed metadata is safe local metadata only

**Decision**: Seed metadata stores podcast id, episode ref, title, published time, duration, bounded GUID/status metadata, has-audio flag, selector metadata, warnings, and no-investment-advice marker. It omits full source URL, audio URL, query string, raw description, and feed HTML body.

**Rationale**: RSS entries can contain signed media URLs, tracking query strings, user-visible links, and arbitrary descriptions. 008 only needs episode identity and title to discover and render the episode; 012 can later use the existing downloader to resolve the audio URL from RSS at execution time.

**Alternatives considered**:
- Store audio URL for later 012 use: rejected because it creates URL leakage and stale signed URL risk.
- Store raw description: rejected because it may contain URLs, prompts, or unrelated body content and is not needed for discovery.

## Decision: Extend 008 discovery to read seed metadata

**Decision**: 008 corpus index discovers episode refs from `data/corpus/{podcast_id}/episode-seeds/*.episode-seed.json` in addition to existing artifact families.

**Rationale**: This keeps corpus index generation offline and local after intake. Seed files become local artifacts that let 009 plan remediation without reading RSS.

**Alternatives considered**:
- Make 009 read seeds directly: rejected because 008 remains the canonical corpus status source.
- Make 008 read RSS directly: rejected because 008 is explicitly offline/local-only.

## Decision: 009 uses seed-derived feed audio availability for ready audio action

**Decision**: 009 may use seed metadata to distinguish a seeded missing-audio episode with `has_audio_url=true` from an unknown local-only missing audio episode.

**Rationale**: 012 should only select audio actions that can be safely delegated to the existing downloader. A seed with feed audio availability gives enough local metadata for a ready audio action without storing full URLs.

**Alternatives considered**:
- Always make missing audio ready: too broad for seedless local-only episodes with no known feed audio.
- Block all seeded audio: defeats the purpose of intake-to-download flow.

## Decision: No MCP tool in v1

**Decision**: 013 is core + CLI only.

**Rationale**: The current corpus repair chain has stayed CLI/core first, and MCP registry changes require separate contract review. A local CLI is sufficient for validating latest episode intake.

**Alternatives considered**:
- Add MCP intake tool now: rejected to keep v1 scope narrow and preserve current MCP tool count.
