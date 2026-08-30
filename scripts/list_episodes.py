from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import get_episode, list_episodes


def main() -> None:
    parser = argparse.ArgumentParser(description="List podcast episodes.")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--episode")
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    if podcast_id is None:
        parser.error("Provide --podcast, or positional podcast_id.")

    if args.episode:
        payload = _episode_to_dict(get_episode(podcast_id, args.episode))
    else:
        payload = [_episode_to_dict(episode) for episode in list_episodes(podcast_id, args.limit)]

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _episode_to_dict(episode):
    return {
        "episode_ref": episode.episode_ref,
        "title": episode.title,
        "published_at": episode.published_at,
        "duration": episode.duration,
        "has_audio_url": episode.audio_url is not None,
        "audio_url": episode.audio_url,
        "guid": episode.guid,
        "link": episode.link,
        "description": episode.description,
    }


if __name__ == "__main__":
    main()
