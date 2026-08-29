from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, generate_stock_lens_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="產生 podcast-wide deterministic stock lens report。"
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("stock_query", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--stock", dest="stock_option")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--max-evidence-items", type=int, default=10)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    stock_query = args.stock_option or args.stock_query
    if podcast_id is None or stock_query is None:
        parser.error("必須提供 --podcast 與 --stock，或 positional podcast_id stock_query。")

    try:
        result = generate_stock_lens_report(
            podcast_id,
            stock_query,
            force=args.force,
            allow_partial=args.allow_partial,
            max_evidence_items=args.max_evidence_items,
        )
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(_asset_to_dict(result), ensure_ascii=False, indent=2))


def _asset_to_dict(asset):
    return {
        "podcast_id": asset.podcast_id,
        "stock_query": asset.stock_query,
        "report_json_path": str(asset.report_json_path),
        "report_markdown_path": str(asset.report_markdown_path),
        "report_status": asset.report_status,
        "match_count": asset.match_count,
        "warning_count": asset.warning_count,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
    }


if __name__ == "__main__":
    main()
