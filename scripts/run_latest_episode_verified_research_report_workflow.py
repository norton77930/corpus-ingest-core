"""Thin CLI for the SPEC 018 verified latest-episode report workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import (
    LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError,
    latest_episode_verified_research_report_workflow_result_to_dict as result_to_dict,
    run_latest_episode_verified_research_report_workflow,
)
from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or complete one approved latest verified research report workflow."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--expected-episode-ref")
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--stock-query")
    parser.add_argument("--include-fixture-verification", action="store_true")
    parser.add_argument("--transcription-model")
    parser.add_argument("--transcription-device", default="cpu")
    parser.add_argument("--transcription-compute-type", default="int8")
    parser.add_argument("--transcription-vad-filter", action="store_true")
    parser.add_argument("--semantic-provider", default="openai-compatible")
    parser.add_argument("--semantic-model")
    parser.add_argument("--semantic-chunk-seconds", type=int, default=600)
    parser.add_argument("--semantic-max-segments-per-chunk", type=int, default=120)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.confirm and args.api_cost_ack != SEMANTIC_API_COST_ACK:
        print(
            "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError: exact api_cost_ack is required",
            file=sys.stderr,
        )
        return 1
    try:
        result = run_latest_episode_verified_research_report_workflow(
            args.podcast_id,
            confirm=args.confirm,
            expected_episode_ref=args.expected_episode_ref,
            api_cost_ack=args.api_cost_ack,
            stock_query=args.stock_query,
            include_fixture_verification=args.include_fixture_verification,
            transcription_model=args.transcription_model,
            transcription_device=args.transcription_device,
            transcription_compute_type=args.transcription_compute_type,
            transcription_vad_filter=args.transcription_vad_filter,
            semantic_provider=args.semantic_provider,
            semantic_model=args.semantic_model,
            semantic_chunk_seconds=args.semantic_chunk_seconds,
            semantic_max_segments_per_chunk=args.semantic_max_segments_per_chunk,
        )
    except LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError:
        print(
            "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError: workflow failed",
            file=sys.stderr,
        )
        return 1
    except Exception:  # noqa: BLE001 - keep the CLI output category-only.
        print(
            "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError: workflow failed",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result_to_dict(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
