from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, extract_mentions


def main() -> None:
    parser = argparse.ArgumentParser(description="擷取單一 podcast episode 的 deterministic mentions。")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--max-evidence-per-mention", type=int, default=5)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    try:
        result = extract_mentions(
            podcast_id,
            episode_ref,
            force=args.force,
            allow_partial=args.allow_partial,
            max_evidence_per_mention=args.max_evidence_per_mention,
        )
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(_asset_to_dict(result), ensure_ascii=False, indent=2))


def _asset_to_dict(asset):
    return {
        "podcast_id": asset.podcast_id,
        "episode_ref": asset.episode_ref,
        "title": asset.title,
        "source_transcript_json_path": str(asset.source_transcript_json_path),
        "mentions_json_path": str(asset.mentions_json_path),
        "mentions_markdown_path": str(asset.mentions_markdown_path),
        "mention_count": asset.mention_count,
        "segment_count": asset.segment_count,
        "extraction_mode": asset.extraction_mode,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
    }


if __name__ == "__main__":
    main()
