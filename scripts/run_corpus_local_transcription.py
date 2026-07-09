from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import PodcastIngestCoreError, run_corpus_local_transcription
from podcast_ingest_core.corpus_local_transcription_runner import result_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview or run local corpus transcription for one episode."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--episode", dest="episode_ref")
    parser.add_argument("--model")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8", dest="compute_type")
    parser.add_argument("--vad-filter", action="store_true", dest="vad_filter")
    args = parser.parse_args(argv)

    try:
        result = run_corpus_local_transcription(
            args.podcast_id,
            episode_ref=args.episode_ref,
            confirm=args.confirm,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            vad_filter=args.vad_filter,
        )
    except (PodcastIngestCoreError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
