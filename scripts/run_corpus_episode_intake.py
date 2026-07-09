from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import PodcastIngestCoreError, run_corpus_episode_intake
from podcast_ingest_core.corpus_episode_intake import result_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview or run one bounded corpus episode intake bootstrap."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--episode", default="latest", dest="episode_ref")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = run_corpus_episode_intake(
            args.podcast_id,
            episode_ref=args.episode_ref,
            confirm=args.confirm,
        )
    except (PodcastIngestCoreError, ValueError) as exc:
        print(f"{type(exc).__name__}: episode intake failed", file=sys.stderr)
        return 1

    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
