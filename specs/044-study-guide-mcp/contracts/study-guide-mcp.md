# Contract: generate_study_guide_bundle

**Feature**: 044 | **Target**: appended MCP Tool 26; baseline Tools 1–25 unchanged.

## Input

```python
def generate_study_guide_bundle(
    podcast_id: str = "",
    episode_ref: str = "",
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
) -> dict[str, Any]:
```

Only these five parameters. No provider/model/endpoint/credential, path override, workflow context, retry, batch or latest selector. Use existing slug/episode validation; support underscore episode IDs, but reject whitespace, separators and case-insensitive reserved latest/next without normalization. Require a configured learning-notes source.

Ack is forwarded unchanged on confirm, never validated/synthesized/normalized/echoed by wrapper. Core requires it only for a generating branch. Reuse and cover-only do not need ack.

## Preview: confirm=false

One `run_study_guide_bundle(..., confirm=False, force=force)` call followed by the pure Core projector.

| Key | Value/source |
| --- | --- |
| `ok`, `dry_run`, `requires_confirmation` | true |
| `tool` | `generate_study_guide_bundle` |
| `action` | fixed description, no source body |
| `inputs` | validated `{podcast_id, episode_ref, force}`; no ack |
| `writes`, `reads`, `reuses` | Core planned lists; reads include identity JSON dependency |
| `report_writes` | two report paths from pure projector, plans only |
| `requires_llm` | Core projector boolean |
| `run_mode` | `dry-run`, matching Core |
| `network_read` | false |
| `not_investment_advice` | true, from Core |
| `warnings` | Core warnings unchanged, possibly empty |
| `risks` | fixed no-advice/manual-cache notice and branch-appropriate LLM/ack notice |
| `next_step` | existing action-plan confirmation instruction |

Explain that every successful confirm writes run reports. Do not say every confirm calls an LLM. Preview is a fresh plan, not a durable approval token or digest pin; confirm reevaluates state. Zero `.env`/credential resolution, provider/network calls, mkdir, recovery or report writes. Existing Core preview report-path fields remain None.

## Confirm: confirm=true

Call the existing Core once with podcast/episode/confirm/force/ack. No internal preview call. Success envelope:

```text
{"ok": true, "data": <existing StudyGuideBundleResult serialization>, "warnings": <copy of data.warnings, including []>}
```

Use `mcp_runtime.tool_success(result)` for existing serialization. Data keys retain meanings/schema. No auto Tool25, index/cache rebuild, download, transcription, summary or review. No generated body, prompt or transcript response text.

## Errors: both modes

Use the existing envelope `{"ok": false, "error_type": <fixed known type>, "message": <fixed message>}`. Do not use `_tool_call`'s raw exception passthrough; local catches call `tool_error`. Never append exception text/repr, arbitrary input, filename, provider response or traceback.

| Known reason/type | Required fixed English message |
| --- | --- |
| `invalid_identity` | An explicit configured podcast and canonical episode reference are required; latest/next are unsupported. |
| `unsafe_path` | A study-guide source or destination path is unsafe or unreadable; publication is refused. |
| `recovery_required` | Existing study-guide or derivation staging/backup entries require operator review; no automatic recovery was attempted. |
| `derivation_conflict` | Existing workflow derivations prevent regenerating their lecture; force does not override this protection. |
| `publish_failed` | Study-guide publication failed before commit; the previous public bundle is unchanged or restored. |
| `rollback_failed` | Publication and rollback failed; preserved backup/staging requires operator recovery. |
| `published_cleanup_failed` | The complete study-guide bundle was published, but cleanup failed; review retained recovery entries before another operation. |
| `published_report_failed` | The complete study-guide bundle was published, but its run report could not be completed; do not automatically regenerate. |
| `reused_report_failed` | The existing bundle was reused, but its run report could not be completed; do not automatically regenerate. |
| `StudyGuideBundleError` / unknown state code | Study-guide prerequisites, generated content or local publication could not be validated; check the configured source and bundle state. |
| `LLMProviderConfigError` | Confirmed generation requires the exact API-cost acknowledgement and a valid local provider configuration. |
| other `PodcastIngestCoreError` / `ValueError` | The requested study-guide operation could not be completed with the supplied identifiers or local configuration. |
| unknown exception | Study-guide operation failed; inspect local state before retrying. |

State errors have fixed `error_type="StudyGuideBundleStateError"`; other known classes use their listed fixed base name; unknown exceptions use `InternalError`. Most-specific catch first. Do not expose arbitrary exception class names. Post-commit error messages carry publication state without adding a success data payload. No error authorizes retry or deletion.

## Compatibility

- Registry becomes 26 only when implemented; prefix of 25 names/signatures/defaults/order equals baseline.
- Group imports after Tool25 inside facade's order fence, on the same FastMCP instance for both transports.
- Existing Core/CLI result and report schemas unchanged; projector affects only new MCP preview.
- Existing prompts, artifact ladder and Tool25 behavior unchanged.
- Preserving extra files never registers them as lecture roles.

## Required Offline Cases

Generation, reuse, missing/invalid-UTF8 cover, partial refusal, force with/without each derivation, reserved/unsafe identity, unknown/finance source, identity mismatch, links/reparse, all recovery suffixes, incorrect ack, fake provider failure, staging/rename/rollback/cleanup/report failure, safe metadata responses and no automatic downstream/cache call. Ownership and order are in [tasks.md](../tasks.md).
