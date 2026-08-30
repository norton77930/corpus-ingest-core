"""Thin CLI for the SPEC 018 verified latest-episode report workflow."""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError,
    run_latest_episode_verified_research_report_workflow,
)
from corpus_ingest_core import (
    latest_episode_verified_research_report_workflow_result_to_dict as result_to_dict,
)
from corpus_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or complete one approved latest verified research report workflow."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--no-publish", action="store_true")
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
    parser.add_argument("--semantic-base-url")
    parser.add_argument("--semantic-reasoning-effort")
    parser.add_argument("--semantic-read-timeout-seconds", type=int, default=120)
    parser.add_argument("--semantic-chunk-seconds", type=int, default=600)
    parser.add_argument("--semantic-max-segments-per-chunk", type=int, default=120)
    return parser


def _loopback_semantic_routing(value: str | None) -> tuple[str | None, str]:
    """Route a local CLI proxy only through its dedicated credential name."""

    if value is None:
        return None, "OPENAI_API_KEY"
    if not isinstance(value, str) or not value:
        raise ValueError("semantic base URL")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        # Binding ``port`` performs bounded validation of a numeric port; the
        # value itself is unused, only the ValueError it may raise matters.
        _validated_port = parsed.port
    except ValueError as exc:
        raise ValueError("semantic base URL") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or host is None
        or parsed.username is not None
        or parsed.password is not None
        or "?" in value
        or "#" in value
    ):
        raise ValueError("semantic base URL")
    if host.casefold() != "localhost":
        try:
            address = ipaddress.ip_address(host)
            if address.version != 4 or not address.is_loopback:
                raise ValueError("semantic base URL")
        except ValueError as exc:
            raise ValueError("semantic base URL") from exc
    return value, "CLI_PROXY_API_KEY"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        semantic_base_url, semantic_api_key_env = _loopback_semantic_routing(args.semantic_base_url)
    except ValueError:
        print(
            "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError: invalid semantic base URL",
            file=sys.stderr,
        )
        return 1
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
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_reasoning_effort=args.semantic_reasoning_effort,
            semantic_read_timeout_seconds=args.semantic_read_timeout_seconds,
            semantic_chunk_seconds=args.semantic_chunk_seconds,
            semantic_max_segments_per_chunk=args.semantic_max_segments_per_chunk,
            publish_report=not args.no_publish,
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
