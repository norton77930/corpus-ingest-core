from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import PodcastIngestCoreError, run_research_workflow
from podcast_ingest_core.local_env import (
    DEFAULT_LOCAL_ENV_PATH,
    empty_local_env_result,
    load_local_env,
    local_env_metadata,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute the local deterministic research workflow."
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--stock", dest="stock_query")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--include-semantic-summary", action="store_true")
    parser.add_argument("--include-stock-lens-synthesis", action="store_true")
    parser.add_argument("--include-semantic-context-in-synthesis", action="store_true")
    parser.add_argument("--include-external-data-verification", action="store_true")
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--semantic-provider", default="openai-compatible")
    parser.add_argument("--semantic-model")
    parser.add_argument("--semantic-base-url")
    parser.add_argument("--semantic-api-key-env", default="API_KEY")
    parser.add_argument("--semantic-chunk-seconds", type=int, default=600)
    parser.add_argument("--semantic-max-segments-per-chunk", type=int, default=120)
    parser.add_argument("--synthesis-provider", default="openai-compatible")
    parser.add_argument("--synthesis-model")
    parser.add_argument("--synthesis-base-url")
    parser.add_argument("--synthesis-api-key-env", default="API_KEY")
    parser.add_argument("--synthesis-max-prompt-chars", type=int, default=24000)
    parser.add_argument("--synthesis-semantic-context-max-chars", type=int, default=12000)
    parser.add_argument("--env-file", default=str(DEFAULT_LOCAL_ENV_PATH))
    parser.add_argument("--no-env-file", action="store_true")
    parser.add_argument("--external-data-provider", default="fixture")
    parser.add_argument(
        "--external-fixture-path",
        type=Path,
        default=Path("config/external_market_data_fixtures.yaml"),
    )
    parser.add_argument("--max-evidence-per-mention", type=int, default=5)
    parser.add_argument("--report-window-seconds", type=int, default=300)
    parser.add_argument("--max-evidence-per-section", type=int, default=5)
    parser.add_argument("--max-candidates-per-node", type=int, default=5)
    parser.add_argument("--max-evidence-per-candidate", type=int, default=5)
    parser.add_argument("--max-stock-evidence-items", type=int, default=10)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    try:
        local_env_result = _load_local_env_from_args(args)
        result = run_research_workflow(
            podcast_id,
            episode_ref,
            stock_query=args.stock_query,
            confirm=args.confirm,
            force=args.force,
            allow_partial=args.allow_partial,
            include_semantic_summary=args.include_semantic_summary,
            include_stock_lens_synthesis=args.include_stock_lens_synthesis,
            include_semantic_context_in_synthesis=args.include_semantic_context_in_synthesis,
            include_external_data_verification=args.include_external_data_verification,
            api_cost_ack=args.api_cost_ack,
            semantic_provider=args.semantic_provider,
            semantic_model=args.semantic_model,
            semantic_base_url=args.semantic_base_url,
            semantic_api_key_env=args.semantic_api_key_env,
            semantic_chunk_seconds=args.semantic_chunk_seconds,
            semantic_max_segments_per_chunk=args.semantic_max_segments_per_chunk,
            synthesis_provider=args.synthesis_provider,
            synthesis_model=args.synthesis_model,
            synthesis_base_url=args.synthesis_base_url,
            synthesis_api_key_env=args.synthesis_api_key_env,
            synthesis_max_prompt_chars=args.synthesis_max_prompt_chars,
            synthesis_semantic_context_max_chars=args.synthesis_semantic_context_max_chars,
            external_data_provider=args.external_data_provider,
            external_fixture_path=args.external_fixture_path,
            max_evidence_per_mention=args.max_evidence_per_mention,
            report_window_seconds=args.report_window_seconds,
            max_evidence_per_section=args.max_evidence_per_section,
            max_candidates_per_node=args.max_candidates_per_node,
            max_evidence_per_candidate=args.max_evidence_per_candidate,
            max_stock_evidence_items=args.max_stock_evidence_items,
        )
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    payload = asdict(result)
    payload["local_env"] = local_env_metadata(local_env_result)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_local_env_from_args(args: argparse.Namespace):
    if args.no_env_file:
        return empty_local_env_result(args.env_file)
    return load_local_env(args.env_file)


if __name__ == "__main__":
    main()
