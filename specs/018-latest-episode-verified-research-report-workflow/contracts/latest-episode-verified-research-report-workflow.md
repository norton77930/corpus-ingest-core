# Contract: Latest Episode Verified Research Report Workflow

## Core

```python
def run_latest_episode_verified_research_report_workflow(
    podcast_id: str,
    *,
    confirm: bool = False,
    expected_episode_ref: str | None = None,
    api_cost_ack: str = "",
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
) -> LatestEpisodeVerifiedResearchReportWorkflowRunResult:
```

`confirm=False` is strict zero-write. Confirmed execution requires a non-empty canonical `expected_episode_ref` and exact `api_cost_ack` before RSS, environment/provider, writers, or child stages. If the resolved latest episode drifts from approval, it is an approval-boundary rejection with zero owned writes: no expected/latest checkpoint, claim, staging directory, or bundle. It has no live market API and no investment advice.

## MCP

`run_latest_episode_verified_research_report_workflow` is the fifteenth reviewed tool and defaults to `confirm=False`. It exposes only bounded options and returns the existing success/error/dry-run envelopes. Invalid confirmed requests return the fixed `LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError` envelope without Core invocation.

## Bundle

A successful publication has exactly:

```text
data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/report.json
data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/report.md
data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/manifest.json
```

The manifest records canonical assembly options (including `include_fixture_verification`), source digest, source identity/hash/size, quality gates, and file hashes. A reusable destination has exactly these three files. Reuse compares deterministic `report.json` UTF-8 bytes, deterministic Markdown bytes, and the full expected manifest; manifest hashes alone are not trust roots. Publication validates sources both before staging and immediately before rename. If another writer wins a destination race, reuse is permitted only after this same complete comparison; otherwise it fails closed.

## Transcript and Semantic Review Gates

Adoption first requires `validate_transcript(...).status == "valid"`, complete TXT/SRT/JSON outputs, and matching transcript identity. Invalid transcript artifacts cannot be reported as completed/reused and cannot bypass the pinned 017 gate.

A semantic smoke-review JSON report has the additive `semantic_summary_sha256` field. SPEC 018 uses one centralized inspector for both workflow gating and assembly: only a timestamped review with matching podcast/episode identity, exact `review_status == "passed"`, and SHA-256 matching current summary bytes is passed. Missing hash, stale hash, unreadable/mismatched payload, or a non-timestamped spoof requires safe re-review or fails closed.

## Checkpoint and Result Safety

Checkpoint records are metadata only and have validated identity, merged bounded stage history, `terminal_outcome`, bounded bundle references, the highest reserved `invocation_generation`, and `successful_invocation_generation` for a successful bundle. After approval drift passes, the episode claim atomically reserves the next integer generation before child stages; every confirmed write carries it. A persistent claim file identifies a process-lifetime OS lock (Windows byte-range lock or POSIX advisory lock), never a liveness signal. The locked write compares generations so stale successes merge history without replacing higher-generation digest/version/references; a legacy checkpoint without generation reads as generation zero. Artifact and final-bundle verification always override checkpoint claims. The one terminal finalizer explicitly skips an approval-boundary drift rejection; other stage-boundary failures return category-only terminal metadata, and a bundle successfully renamed before checkpoint failure remains a successful result with a checkpoint warning.

All public inputs are strictly type/size/secret/path/URI validated. `result_to_dict` recursively emits only JSON-safe sanitized metadata and never reflects credential-like values or arbitrary object representations. Source safety violations (including AWS secret assignments, private key headers, credential/token/password assignments, and unsafe URI data) prohibit final report publication.

## Skill

The portable Skill makes one `confirm=false` preview call, waits for explicit episode-scoped approval with exact `expected_episode_ref` and exact `api_cost_ack`, makes one `confirm=true` call, reports once, and stops. It cannot use CLI, terminal fallback, retry, scheduler, cache rebuild, another side-effect tool, a live provider, or investment advice.
