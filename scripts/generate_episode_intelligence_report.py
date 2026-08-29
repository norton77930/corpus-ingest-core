from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    PodcastIngestCoreError,
    generate_episode_intelligence_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="產生單一 podcast episode 的 deterministic intelligence report。"
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--window-seconds", type=int, default=300)
    parser.add_argument("--max-evidence-per-section", type=int, default=5)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    try:
        result = generate_episode_intelligence_report(
            podcast_id,
            episode_ref,
            force=args.force,
            allow_partial=args.allow_partial,
            window_seconds=args.window_seconds,
            max_evidence_per_section=args.max_evidence_per_section,
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
        "report_json_path": str(asset.report_json_path),
        "report_markdown_path": str(asset.report_markdown_path),
        "transcript_status": asset.transcript_status,
        "segment_count": asset.segment_count,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
        "source_status_warnings": asset.source_status_warnings,
    }


if __name__ == "__main__":
    main()
