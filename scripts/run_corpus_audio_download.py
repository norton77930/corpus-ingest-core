from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, run_corpus_audio_download
from corpus_ingest_core.corpus_audio_download_runner import result_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview or run one bounded corpus audio download."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--episode", dest="episode_ref")
    args = parser.parse_args(argv)

    try:
        result = run_corpus_audio_download(
            args.podcast_id,
            episode_ref=args.episode_ref,
            confirm=args.confirm,
        )
    except (PodcastIngestCoreError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
