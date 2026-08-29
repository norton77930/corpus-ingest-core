from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, search_transcripts


def main() -> None:
    parser = argparse.ArgumentParser(description="搜尋 SQLite cache 中的 transcript segments。")
    parser.add_argument("--query", required=True)
    parser.add_argument("--podcast")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--search-mode", choices=["auto", "like", "fts"], default="auto")
    parser.add_argument("--context-segments", type=int, default=0)
    parser.add_argument("--case-sensitive", action="store_true")
    args = parser.parse_args()

    try:
        results = search_transcripts(
            args.query,
            podcast_id=args.podcast,
            limit=args.limit,
            search_mode=args.search_mode,
            context_segments=args.context_segments,
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
        "segment_id": result.segment_id,
        "start": result.start,
        "end": result.end,
        "timestamp": result.timestamp,
        "text": result.text,
        "matched_text": result.matched_text,
        "highlighted_text": result.highlighted_text,
        "context_before": result.context_before,
        "context_after": result.context_after,
        "search_mode": result.search_mode,
        "score": result.score,
    }


if __name__ == "__main__":
    main()
