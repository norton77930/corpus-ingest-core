from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import validate_transcript


def main() -> None:
    parser = argparse.ArgumentParser(description="檢查 podcast transcript 完整性。")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    result = validate_transcript(podcast_id, episode_ref)
    print(json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2))


def _result_to_dict(result):
    return {
        "podcast_id": result.podcast_id,
        "episode_ref": result.episode_ref,
        "valid": result.valid,
        "status": result.status,
        "segment_count": result.segment_count,
        "last_segment_end_seconds": result.last_segment_end_seconds,
        "transcript_text_length": result.transcript_text_length,
        "problems": result.problems,
        "warnings": result.warnings,
        "paths": result.paths,
    }


if __name__ == "__main__":
    main()
