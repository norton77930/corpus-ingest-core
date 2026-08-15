# Safety Checklist: X Video Corpus Ingestion

Unchecked — v1 is not implemented. Each box is a gate for Phase 2/3.

- [ ] Dry-run-first; no download, no audio extraction, no transcription, no write
      without `confirm=true`
- [ ] yt-dlp uses a guest token only; no login, no cookies, no credential, no
      stored session; refuses rather than prompts when a URL is not publicly
      retrievable
- [ ] No LLM, no `api_cost_ack`, no `.env` read, no secret in logs or output
- [ ] No live market API, no external data provider, no investment advice surface
- [ ] Accepts a source URL plus derived identifiers only; no arbitrary local write
      path; `podcast_id` and `episode_ref` validated by the existing `storage` patterns
- [ ] The source video is not written under `data/`; only the extracted audio is
      a corpus artifact
- [ ] No automatic SQLite cache rebuild; the response carries the stale-cache warning
- [ ] Ingesting an X source leaves every other `podcast_id`'s artifacts unmodified
      (gooaye corpus-index mtime and search output unchanged)
- [ ] Unclear audio keeps the prototype's `[不確定：<guess>]` marking, so evidence
      stays separated from inference
- [ ] Whisper confidence fields never reach the transcript contract
- [ ] Registry stays at exactly 22 tools; `tests/test_mcp_tool_registry_contract.py`
      passes **without modification**
- [ ] No test reaches x.com; yt-dlp and PyAV are stubbed at the acquisition boundary
