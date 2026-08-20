# Contract: ingest_youtube_video (Tool 24)

```text
ingest_youtube_video(url: str, confirm: bool = False, title: str | None = None, force: bool = False) -> dict
```

Preview (`confirm=false`): standard `tool_action_plan` plus `run_mode=preview`,
`network_read=true`, `network_read_scope=public_metadata_only`,
`not_investment_advice=true`. Zero writes.

Confirm (`confirm=true`): `{"ok": true, "data": ...}` from Core
`YoutubeVideoIngestResult` plus cache-stale and no-advice warnings.

Errors: `{"ok": false, "error_type": "...", "message": "..."}`.
