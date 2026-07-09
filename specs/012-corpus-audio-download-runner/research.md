# Research: Corpus Audio Download Runner

## Decision: Dry-run never reads RSS or calls network

**Rationale**: The feature's main value is safely previewing network side effects before they happen. Existing `download_audio()` calls `get_episode()` and may call network, so dry-run must derive candidates only from refreshed 009 remediation metadata.

**Alternatives considered**:
- Probe RSS in dry-run to confirm remote availability. Rejected because it violates dry-run no-provider behavior.
- Call `download_audio()` with a fake/no-write mode. Rejected because the existing core capability has no no-network preview contract.

## Decision: Confirmed execution is single-episode only

**Rationale**: Audio download is a remote/network side effect and may use bandwidth or remote provider resources. One explicit episode keeps execution auditable and bounded.

**Alternatives considered**:
- Allow `--action-family audio --confirm` batch execution. Rejected for v1 due to larger blast radius.
- Plan-only runner with no confirmed execution. Rejected because it would not close the upstream audio gap.

## Decision: Reuse existing `download_audio()` directly

**Rationale**: The existing downloader already handles episode lookup, extension/content-type selection, deterministic local audio paths, streaming writes, `.part` cleanup, and existing-file reuse. The runner should orchestrate selection and reporting, not duplicate download logic.

**Alternatives considered**:
- Shell out to `scripts/download_episode.py`. Rejected because repository rules require thin CLI and thick core.
- Add a new downloader implementation. Rejected because it would duplicate tested behavior and increase side-effect risk.

## Decision: Omit full source URLs from all runner outputs

**Rationale**: Audio enclosure URLs can contain signed query strings, tracking parameters, or provider tokens. The run report only needs local path, content type, size, and downloaded/reused status for audit.

**Alternatives considered**:
- Include full source URL for audit completeness. Rejected due to leakage risk.
- Include host-only source metadata. Deferred because v1 does not need remote provenance in corpus run reports.

## Decision: Confirmed run reports are latest deterministic artifacts

**Rationale**: This matches 010 and 011 runner patterns: dry-run has no artifact side effect, confirmed execution writes latest JSON/Markdown reports without timestamps.

**Alternatives considered**:
- Timestamped run history. Rejected because corpus runners currently use latest deterministic artifacts.
- Dry-run report artifacts. Rejected because dry-run should remain no-write.

## Decision: No MCP exposure in v1

**Rationale**: Network side effects are riskier than deterministic artifact generation. The v1 surface remains core + CLI only, and MCP registry count stays unchanged.

**Alternatives considered**:
- Add MCP audio download runner immediately. Rejected because MCP side-effect exposure needs its own approval and contract review.
