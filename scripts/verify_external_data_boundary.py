from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import PodcastIngestCoreError, verify_external_data_boundary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="用本機 fixture provider 驗證 external data boundary artifact。"
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--provider", default="fixture")
    parser.add_argument("--fixture-path", type=Path, default=None)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    kwargs = {
        "confirm": args.confirm,
        "force": args.force,
        "allow_partial": args.allow_partial,
        "provider": args.provider,
    }
    if args.fixture_path is not None:
        kwargs["fixture_path"] = args.fixture_path

    try:
        result = verify_external_data_boundary(podcast_id, episode_ref, **kwargs)
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
        "verification_status": asset.verification_status,
        "candidate_count": asset.candidate_count,
        "verified_candidate_count": asset.verified_candidate_count,
        "warning_count": asset.warning_count,
        "dry_run": asset.dry_run,
        "requires_confirmation": asset.requires_confirmation,
        "provider": asset.provider,
        "fixture_path": str(asset.fixture_path),
        "planned_reads": asset.planned_reads,
        "planned_writes": asset.planned_writes,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
        "not_investment_advice": asset.not_investment_advice,
    }


if __name__ == "__main__":
    main()
