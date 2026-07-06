from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import PodcastIngestCoreError, search_mentions


def main() -> None:
    parser = argparse.ArgumentParser(description="搜尋 SQLite cache 中的 mentions。")
    parser.add_argument("--query", required=True)
    parser.add_argument("--podcast")
    parser.add_argument("--type", dest="type_option")
    parser.add_argument("--mention-type", dest="mention_type")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--case-sensitive", action="store_true")
    args = parser.parse_args()

    try:
        results = search_mentions(
            args.query,
            podcast_id=args.podcast,
            mention_type=args.mention_type or args.type_option,
            limit=args.limit,
            case_sensitive=args.case_sensitive,
        )
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps([_result_to_dict(result) for result in results], ensure_ascii=False, indent=2))


def _result_to_dict(result):
    return {
        "podcast_id": result.podcast_id,
        "episode_ref": result.episode_ref,
        "title": result.title,
        "mention_type": result.mention_type,
        "text": result.text,
        "normalized_text": result.normalized_text,
        "count": result.count,
        "evidence_timestamp": result.evidence_timestamp,
        "evidence_text": result.evidence_text,
        "highlighted_text": result.highlighted_text,
        "search_mode": result.search_mode,
    }


if __name__ == "__main__":
    main()
