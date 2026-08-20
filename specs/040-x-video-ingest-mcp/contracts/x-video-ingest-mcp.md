# Contract: ingest_x_video (Tool 23)

## Signature

```text
ingest_x_video(
    url: str,
    confirm: bool = False,
    title: str | None = None,
    force: bool = False,
) -> dict
```

Not accepted: `work_dir`, `device`, `compute_type`, `model`, cookies, credentials,
arbitrary local paths.

## Preview (`confirm=false`)

- Calls Core `run_x_video_ingest(..., confirm=False)`.
- Zero writes.
- Resolves public metadata (network read).
- Envelope MUST include:

```json
{
  "ok": true,
  "dry_run": true,
  "requires_confirmation": true,
  "tool": "ingest_x_video",
  "run_mode": "preview",
  "network_read": true,
  "network_read_scope": "public_metadata_only",
  "not_investment_advice": true
}
```

plus `action`, `inputs`, `writes`, `risks`, `next_step`.

`risks` MUST state that preview reads public metadata and writes nothing, and
that this is not a corpus zero-network dry-run.

## Confirm (`confirm=true`)

- Calls Core `run_x_video_ingest(..., confirm=True)` with default
  `device=cpu`, `compute_type=int8`, Core-owned `work_dir`.
- Success envelope is the standard `{"ok": true, "data": ...}` plus warnings
  that include the cache-stale sentence and no-advice statement.
- `data` includes result paths, `run_mode=confirmed`, `not_investment_advice=true`.
- Failure is `{"ok": false, "error_type": "...", "message": "..."}`.

## Thin wrapper

The tool module parses arguments, calls Core, and formats the envelope.
It does not download, extract, transcribe, or write reports itself.
