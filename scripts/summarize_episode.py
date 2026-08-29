from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    PodcastIngestCoreError,
    semantic_summarize_episode,
    summarize_episode,
)
from corpus_ingest_core.local_env import (
    DEFAULT_LOCAL_ENV_PATH,
    empty_local_env_result,
    load_local_env,
    local_env_metadata,
)
from corpus_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK


def main() -> None:
    parser = argparse.ArgumentParser(description="摘要單一 podcast episode。")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--mode", choices=["extractive", "semantic"], default="extractive")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-quotes", type=int, default=10)
    parser.add_argument("--window-seconds", type=int, default=300)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--provider", default="openai-compatible")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env", default="API_KEY")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--read-timeout-seconds", type=int, default=120)
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--env-file", default=str(DEFAULT_LOCAL_ENV_PATH))
    parser.add_argument("--no-env-file", action="store_true")
    parser.add_argument("--chunk-seconds", type=int, default=600)
    parser.add_argument("--max-segments-per-chunk", type=int, default=120)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    try:
        local_env_result = _load_local_env_from_args(args)
        if args.mode == "semantic":
            if args.api_cost_ack != SEMANTIC_API_COST_ACK:
                print(
                    f"semantic summary requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
            result = semantic_summarize_episode(
                podcast_id,
                episode_ref,
                api_cost_ack=args.api_cost_ack,
                provider=args.provider,
                model=args.model,
                base_url=args.base_url,
                api_key_env=args.api_key_env,
                reasoning_effort=args.reasoning_effort,
                read_timeout_seconds=args.read_timeout_seconds,
                force=args.force,
                chunk_seconds=args.chunk_seconds,
                max_segments_per_chunk=args.max_segments_per_chunk,
                allow_partial=args.allow_partial,
            )
        else:
            result = summarize_episode(
                podcast_id,
                episode_ref,
                force=args.force,
                max_quotes=args.max_quotes,
                window_seconds=args.window_seconds,
                allow_partial=args.allow_partial,
            )
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    payload = _asset_to_dict(result)
    payload["local_env"] = local_env_metadata(local_env_result)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _asset_to_dict(asset):
    return {
        "podcast_id": asset.podcast_id,
        "episode_ref": asset.episode_ref,
        "title": asset.title,
        "summary_path": str(asset.summary_path),
        "transcript_json_path": str(asset.transcript_json_path),
        "transcript_text_path": str(asset.transcript_text_path),
        "segment_count": asset.segment_count,
        "summary_mode": asset.summary_mode,
        "generated": asset.generated,
        "already_exists": asset.already_exists,
        "provider": asset.provider,
        "model": asset.model,
        "chunk_count": asset.chunk_count,
        "evidence_count": asset.evidence_count,
    }


def _load_local_env_from_args(args: argparse.Namespace):
    if args.no_env_file:
        return empty_local_env_result(args.env_file)
    return load_local_env(args.env_file)


if __name__ == "__main__":
    main()
