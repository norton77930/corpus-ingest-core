from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, run_youtube_video_ingest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Acquire one YouTube video as corpus audio and a transcript; dry-run by default."
    )
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--confirm", action="store_true", help="Actually download and transcribe")
    parser.add_argument("--title", help="Override the title from source metadata")
    parser.add_argument("--model", help="faster-whisper model name")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8", dest="compute_type")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing transcript")
    parser.add_argument(
        "--work-dir",
        dest="work_dir",
        help="Scratch directory for the video; defaults to a system temp dir that is removed on exit. The video is never written into data/.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_youtube_video_ingest(
            args.url,
            confirm=args.confirm,
            title=args.title,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            force=args.force,
            work_dir=args.work_dir,
        )
    except (PodcastIngestCoreError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
