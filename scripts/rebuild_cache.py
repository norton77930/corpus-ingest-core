from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, rebuild_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the SQLite metadata cache.")
    parser.add_argument("--podcast")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        result = rebuild_cache(podcast_id=args.podcast, force=args.force)
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2))


def _result_to_dict(result):
    return {
        "db_path": result.db_path,
        "indexed_episode_count": result.indexed_episode_count,
        "skipped_episode_count": result.skipped_episode_count,
        "problems": result.problems,
        "warnings": result.warnings,
    }


if __name__ == "__main__":
    main()
