# Contract: Tool 25 Safety and Publication

## Stable surface

`derive_workflow_bundle(podcast_id="", episode_ref="", confirm=False, force=False, api_cost_ack="")` remains Tool 25 at index 24 in the existing 26 tools. Core run_workflow_derivation signature, WorkflowDerivationResult and CLI arguments remain unchanged. Preview keeps run_mode=preview, existing inputs/reads/writes/reuses/warnings/risks and zero network. Do not add requires_llm/report_writes. Success remains existing data plus top-level warnings. Error remains ok=false, message, error_type; no reason_code key.

MCP error content changes intentionally. LLM risk prose should describe generation conditionally and disclose reuse report writes; callers must use writes/reuses for cost. No new plan projection API is necessary.

## Path and input policy

Validate identity before any profile/source/context read. Reject empty/non-string/padded IDs, separator-bearing or reserved latest/next episode refs; preserve case and underscores. Use existing storage validators, not copied regex. Canonical JSON identity must match request and contain nonblank title. Select only the title-derived summary/lecture. Transcript JSON cap 64 MiB; lecture 00/03/04/07 cap 2 MiB each, UTF-8. Summary must be a safe regular canonical file but its body is not sent/read as a new derivation input.

Managed path checks run from existing storage roots downward; do not resolve links before inspecting them. Missing required source is a prerequisite error; failed lstat/listing/unsafe entry is unsafe_path. Reject symlinks, dangling links, Windows reparse, special files, nested directories and non-directory ancestors. Inspect report roots/ancestors/final JSON/Markdown and their .part targets without following links. Report ordinary .part overwrite semantics remain those of the existing shared writer.

Context override remains Core/CLI-only. Accept local absolute or cwd-relative paths, including paths outside repository; reject raw .. components before normalization, reject Windows drive-relative paths (for example C:context.yaml), UNC/network paths and device namespaces, then convert lexically with abspath. Do not dereference with resolve. Reject link/reparse components, nondirectory ancestors and nonregular leaves. Check absolute ancestors from filesystem anchor, then read at most 2 MiB + 1 bytes, reject oversized/non-UTF-8. YAML allowed_tools validation stays unchanged. This introduces explicit unsafe/oversized context refusal, not a new path parameter. Context is not a secure_local_snapshot root chosen by the caller. No hostile-race guarantee for it.

## Recovery and ownership

Recovery siblings are exact destination basename + .part/.old/.wfderive.part/.wfderive.old. Presence of any type refuses preview, reuse, force and generation. Only FileNotFoundError means absent; inspection failures refuse. No pre-existing remnant is deleted/restored. Recheck before staging. Newly created stage uses exclusive mkdir; an unexpected collision is refused and must not be cleaned as owned.

05/06 are the only replaceable roles. Partial pair + force=false still refuses; force=true with exact ack may replace ordinary pair entries only. Empty/binary regular existing 05/06 retain existing presence-based reuse semantics; semantic validation of reused content is excluded. Every non-pair regular extra is streamed byte-for-byte, without requiring UTF-8 or applying lecture-size caps. File permissions, timestamps and inode are not promised identical.

Transaction commit = successful stage-to-live rename, after old-live-to-backup rename. No mixed 05/06 pair is installed by sequential file copies. This is not continuous availability, multiwriter isolation or power-loss durability. Before commit, copy/write/rename failures leave the old public tree unchanged or restore it. Failed restoration retains backup/staging. After commit, cleanup failure never reverts the new pair. Only positively identified attempt-owned temporary entries can be cleaned; unknown ownership/type is retained.

## Finite errors

Add WorkflowDerivationStateError(WorkflowDerivationError), with internal reason_code and these fixed messages. The MCP mapper selects the table, not str(exc), even if exception args are altered. Unknown reason uses the base generic message and the fixed state-error type.

| Reason | Fixed message |
| --- | --- |
| invalid_identity | An explicit configured podcast and canonical episode reference are required; latest/next are unsupported. |
| unsafe_path | A workflow-derivation source or destination path is unsafe or unreadable; publication is refused. |
| recovery_required | Existing study-guide or derivation staging/backup entries require operator review; no automatic recovery was attempted. |
| publish_failed | Workflow-derivation publication failed before commit; the previous public bundle is unchanged or restored. |
| rollback_failed | Workflow-derivation publication and rollback failed; preserved backup/staging requires operator recovery. |
| published_cleanup_failed | The complete workflow-derivation pair was published, but cleanup failed; review retained recovery entries before another operation. |
| published_report_failed | The complete workflow-derivation pair was published, but its run report could not be completed; do not automatically regenerate. |
| reused_report_failed | The existing workflow-derivation pair was reused, but its run report could not be completed; do not automatically regenerate. |

| Exception category | Public error_type | Fixed message |
| --- | --- | --- |
| State subclass | WorkflowDerivationStateError | Table above, otherwise generic below |
| Base derivation error | WorkflowDerivationError | Workflow-derivation prerequisites, generated content or local publication could not be validated; check the configured source and bundle state. |
| LLMProviderConfigError | LLMProviderConfigError | Confirmed generation requires the exact API-cost acknowledgement and a valid local provider configuration. |
| Other PodcastIngestCoreError | PodcastIngestCoreError | The requested workflow-derivation operation could not be completed with the supplied identifiers or local configuration. |
| ValueError | ValueError | The requested workflow-derivation operation could not be completed with the supplied identifiers or local configuration. |
| Any other Exception | InternalError | Workflow-derivation operation failed; inspect local state before retrying. |

Catch order: state, provider-config, base derivation, other Core, ValueError, unknown. Do not expose exception causes, repr, dynamic subclass names, local paths or provider details in failure responses. Successful path metadata and known cache warnings remain allowed. Fixed messages do not promise zero writes for unknown or generic errors. Reports can fail partly under their existing protocol.

## Acceptance matrix

| Case | Required coverage |
| --- | --- |
| C01 | Invalid IDs before profile/context/provider access; case/underscore valid |
| C02 | Canonical metadata mismatch, invalid JSON/title, stale-title neighbors and bounded read |
| C03 | Every recovery suffix x preview/confirm x force false/true, on generation and reuse trees |
| C04 | Recovery entry directory/file/broken link/reparse; failed lstat, unchanged bytes |
| C05 | Source/ancestor/destination/pair/extra/context/report link or special path; directory and listing failure |
| C06 | Context relative/absolute override, default, raw parent traversal/drive-relative/device namespace refusal before normalization, malformed/oversized UTF-8/YAML, same allowed_tools behavior |
| C07 | No-pair generation; CRLF/LF/BOM lecture and binary/large extras retained |
| C08 | Complete reuse with empty ack, no provider, reports written, all artifact bytes identical |
| C09 | Partial-pair refusal without force; partial/full force replacement preserves non-pair bytes |
| C10 | Copy failure, generated-file write failure, backup rename failure: no partial public pair |
| C11 | Stage-to-live failure + successful rollback: exact old tree restored |
| C12 | Rollback failure: evidence retained, no cleanup; next call refuses recovery |
| C13 | Postcommit backup stat/type/delete failure: new pair retained, cleanup status |
| C14 | Generated/reused report failure: inject failure in actual write_part_staged_report_pair path (not only mocked _write_run_report), distinct status, artifact state retained, no rollback |
| C15 | Stage collision/listed entry disappears/metadata OSError: never infer absent or own unknown entry |
| C16 | Both MCP branches: every fixed error category, unknown reason/subclass, injected body/instruction text absent |
| C17 | Registry/signatures/facade/success/warnings and Tool 26 contracts unchanged |
| C18 | Updated derivation Skill/oracles retain consent/stop; no automatic recovery/retry; offline-only claims |

Use public Core/MCP calls for observable assertions, with private seam injection only to select a fault. Native symlink cases may skip only on actual OSError; simulated reparse/stat/special-file tests always run. Do not assert live model obedience from text/oracle tests.
