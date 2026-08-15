# Quickstart: Stock Lens MCP Tool

```text
# Dry-run: plan only, writes nothing.
generate_stock_lens_report(podcast_id="gooaye", stock_query="台積電")

# Confirmed: writes data/stock-lens/gooaye/台積電.stock-lens.{json,md}
generate_stock_lens_report(podcast_id="gooaye", stock_query="台積電", confirm=true)
```

Same seam from the CLI:

```powershell
python scripts/generate_stock_lens_report.py gooaye 台積電
```

Index the new artifact for search (never automatic):

```powershell
python scripts/rebuild_cache.py --podcast gooaye
```

Mapping and external-boundary artifacts must already exist for the episodes you
expect to match; this tool does not generate them. A stock with no podcast
evidence yields an explicit absence, not an invented link.
