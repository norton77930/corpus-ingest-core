# Quickstart: X Video Ingest MCP (Tool 23)

Active feature:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/040-x-video-ingest-mcp"
```

Preview first (zero-write, metadata network read):

The MCP tool is `ingest_x_video` with `confirm=false`. The CLI equivalent remains:

```powershell
python scripts/run_x_video_ingest.py --url "https://x.com/<handle>/status/<id>"
```

Confirmed ingest (writes audio, seed, transcript, run report; no cache rebuild):

```powershell
python scripts/run_x_video_ingest.py --url "https://x.com/<handle>/status/<id>" --confirm
```

Then rebuild cache yourself if the episode must be searchable:

```powershell
python scripts/rebuild_cache.py --podcast x-<handle>
```

Boundaries: guest token only, no cookies, no LLM, no investment advice, registry
exactly 23 after this package. Preview is not a corpus zero-network dry-run.
