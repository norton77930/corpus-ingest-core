from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, generate_industry_chain_mapping


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic industry chain mapping for one podcast episode."
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--max-candidates-per-node", type=int, default=5)
    parser.add_argument("--max-evidence-per-candidate", type=int, default=5)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("Provide --podcast and --episode, or positional podcast_id episode_ref.")

    try:
        result = generate_industry_chain_mapping(
            podcast_id,
            episode_ref,
            force=args.force,
            allow_partial=args.allow_partial,
            max_candidates_per_node=args.max_candidates_per_node,
            max_evidence_per_candidate=args.max_evidence_per_candidate,
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
        "mapping_json_path": str(asset.mapping_json_path),
        "mapping_markdown_path": str(asset.mapping_markdown_path),
        "mapping_status": asset.mapping_status,
        "node_count": asset.node_count,
        "candidate_count": asset.candidate_count,
        "warning_count": asset.warning_count,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
    }


if __name__ == "__main__":
    main()
