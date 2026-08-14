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
    semantic_reasoning_effort: str | None = None,
    semantic_read_timeout_seconds: int = 120,
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
    publish_report: bool = True,
) -> LatestEpisodeVerifiedResearchReportWorkflowRunResult:
```

`confirm=False` is strict zero-write. `publish_report` is a strict boolean and defaults to `True` for full backward compatibility. Confirmed execution requires a non-empty canonical `expected_episode_ref` and exact `api_cost_ack` before RSS, environment/provider, writers, or child stages. With `confirm=True, publish_report=False`, a non-empty `stock_query` is rejected before latest resolution, provider, writer, or claim acquisition. The pinned deterministic workflow, controlled semantic summary generation/regeneration, a fresh semantic review even when the existing review is current/passed, deterministic research, and full current-lineage validation otherwise still run; review, research, or lineage failure is blocked before assembly. A current lineage returns `outcome="ready"` with every bundle/report/manifest result field `None`. This mode does not call bundle adoption, assembly, or publication. Its dry-run plan omits publication. The latest workflow CLI exposes this Core-only choice as `--no-publish`; `--semantic-base-url` remains limited to `localhost` or IPv4 loopback (`127/8`) `http(s)` URLs with no userinfo/query/fragment, routed through fixed `CLI_PROXY_API_KEY`, otherwise fixed `OPENAI_API_KEY`, with no API-key-env flag. `semantic_read_timeout_seconds` is a bounded positive non-boolean integer (default `120`, including `600`); effort and timeout become semantic request identity, while the base URL is represented only by its SHA-256 identity. If the resolved latest episode drifts from approval, it is an approval-boundary rejection with zero owned writes: no expected/latest checkpoint, claim, staging directory, or bundle. It has no live market API and no investment advice.

## MCP

`run_latest_episode_verified_research_report_workflow` is the fifteenth reviewed tool and defaults to `confirm=False`. It exposes only its existing bounded options and returns the existing success/error/dry-run envelopes; `publish_report`/`no_publish`, effort, timeout, overwrite, regeneration, and selection override are not MCP inputs. Invalid confirmed requests return the fixed `LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError` envelope without Core invocation.

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

A semantic smoke-review JSON report has the additive `semantic_summary_sha256` field. SPEC 018 uses one centralized inspector for both workflow gating and assembly: only a timestamped review with matching podcast/episode identity, exact `review_status == "passed"`, and SHA-256 matching current summary bytes is passed. Its public writer holds the same reentrant episode-scoped writer claim as the latest workflow, so a nested same-episode review is safe while external same-episode writers serialize through the shared OS claim. Missing hash, stale hash, unreadable/mismatched payload, or a non-timestamped spoof requires safe re-review or fails closed.

## Controlled Regeneration and Research Supersession

A failed controlled semantic summary regeneration reports where the transaction stopped through an allowlisted constant substage on its plan step, emitted as `controlled_regeneration_{substage}` for exactly `authority`, `pre_state`, `provider_generation`, `child_identity`, `changed_sha_proof`, `transcript_source`, `lineage_record`, `lineage_post_validation`, and `rollback`. The category is a fixed constant and never carries an exception message, endpoint, credential env name, prompt, provider response, or artifact body; anything outside the allowlist falls back to the existing category-only behaviour. `changed_sha_proof` and `provider_generation` are distinct so an identical-bytes provider result is never reported as a transport failure.

A regenerated summary leaves every downstream research role without lineage cover while its output still exists on disk, a state the commit guard refuses both to reuse and to generate over. When the research roles are not already current, the confirmed run therefore forces deterministic research and, inside the episode claim and before the progressive lineage scope opens, moves exactly the tracked research outputs aside as same-directory `.superseded` siblings, so the ordinary generated-over-nothing proof applies unchanged. The previous bytes stay on disk for the whole window: they are discarded only by a research stage that completed with every expected role through the controlled commit seam, and every other exit — child exception, non-completed child status, a success claimed without full commit coverage, interrupt during the move, or a failed lineage commit — renames them back before the terminal result. A successful supersession is reported as a bounded warning naming each superseded role and its pre-SHA-256. Neither commit guard is relaxed and no new blessing path exists.

## Checkpoint and Result Safety

Checkpoint records are metadata only and have validated identity, merged bounded stage history, `terminal_outcome`, bounded bundle references, the highest reserved `invocation_generation`, and `successful_invocation_generation` for a successful bundle. Whenever incoming checkpoint metadata is not a verified bundle and the persisted checkpoint is not a successful bundle, merge clears digest/version/bundle references for all terminal outcomes. A no-publish `ready` result records its research/lineage history with non-bundle `manual` terminal metadata; it preserves digest/version/bundle references only from an existing successful bundle, and clears untrusted references from in-progress, failed, or other non-success checkpoint states. It never claims this invocation published a bundle. After approval drift passes, the episode claim atomically reserves the next integer generation before child stages; every confirmed write carries it. A persistent claim file identifies a process-lifetime OS lock (Windows byte-range lock or POSIX advisory lock), never a liveness signal. The locked write compares generations so stale successes merge history without replacing higher-generation digest/version/references; a legacy checkpoint without generation reads as generation zero. Artifact and final-bundle verification always override checkpoint claims. The one terminal finalizer explicitly skips an approval-boundary drift rejection; other stage-boundary failures return category-only terminal metadata, and a bundle successfully renamed before checkpoint failure remains a successful result with a checkpoint warning.

All public inputs are strictly type/size/secret/path/URI validated. `result_to_dict` recursively emits only JSON-safe sanitized metadata and never reflects credential-like values or arbitrary object representations. Source safety violations (including AWS secret assignments, private key headers, credential/token/password assignments, and unsafe URI data) prohibit final report publication.

## Skill

The portable Skill makes one `confirm=false` preview call, waits for explicit episode-scoped approval with exact `expected_episode_ref` and exact `api_cost_ack`, makes one `confirm=true` call, reports once, and stops. It cannot use CLI, terminal fallback, retry, scheduler, cache rebuild, another side-effect tool, a live provider, or investment advice.
