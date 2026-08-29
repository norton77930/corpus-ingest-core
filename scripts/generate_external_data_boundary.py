from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, generate_external_data_boundary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="產生單一 podcast episode 的 external market data boundary scaffold。"
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    try:
        result = generate_external_data_boundary(
            podcast_id,
            episode_ref,
            force=args.force,
            allow_partial=args.allow_partial,
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
        "boundary_json_path": str(asset.boundary_json_path),
        "boundary_markdown_path": str(asset.boundary_markdown_path),
        "boundary_status": asset.boundary_status,
        "candidate_count": asset.candidate_count,
        "warning_count": asset.warning_count,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
    }


if __name__ == "__main__":
    main()
