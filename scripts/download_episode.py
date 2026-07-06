from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import download_audio


def main() -> None:
    parser = argparse.ArgumentParser(description="下載單一 podcast episode 音檔。")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    print(json.dumps(_asset_to_dict(download_audio(podcast_id, episode_ref)), ensure_ascii=False, indent=2))


def _asset_to_dict(asset):
    return {
        "podcast_id": asset.podcast_id,
        "episode_ref": asset.episode_ref,
        "title": asset.title,
        "source_url": asset.source_url,
        "local_path": str(asset.local_path),
        "content_type": asset.content_type,
        "size_bytes": asset.size_bytes,
        "downloaded": asset.downloaded,
        "already_exists": asset.already_exists,
    }


if __name__ == "__main__":
    main()
