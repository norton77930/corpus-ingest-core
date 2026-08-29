from __future__ import annotations

from dataclasses import asdict
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, load_llm_profile, run_research_workflow
from corpus_ingest_core.llm_profiles import DEFAULT_LLM_PROFILES_CONFIG_PATH
from corpus_ingest_core.local_env import (
    DEFAULT_LOCAL_ENV_PATH,
    empty_local_env_result,
    load_local_env,
    local_env_metadata,
)
from corpus_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
from corpus_ingest_core.serialization import to_jsonable
from corpus_ingest_core.stock_lens_synthesis import DEBUG_OUTPUT_PATH_ENV
from corpus_ingest_core.storage import title_slug


SMOKE_MODE = "research-llm-smoke-v1"
LLM_RUNTIME = "openai-compatible /chat/completions"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a dry-run-first LLM research smoke workflow."
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("stock_query", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--stock", dest="stock_option")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--llm-profile")
    parser.add_argument("--llm-profile-path", default=str(DEFAULT_LLM_PROFILES_CONFIG_PATH))
    parser.add_argument("--env-file", default=str(DEFAULT_LOCAL_ENV_PATH))
    parser.add_argument("--no-env-file", action="store_true")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env")
    parser.add_argument("--include-semantic-summary", action="store_true")
    parser.add_argument("--include-semantic-context", action="store_true")
    parser.add_argument("--semantic-context-max-chars", type=int, default=12000)
    parser.add_argument(
        "--include-external-data-verification",
        action="store_true",
        default=True,
    )
    parser.add_argument("--max-prompt-chars", type=int, default=24000)
    parser.add_argument("--debug-llm-output", action="store_true")
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    stock_query = args.stock_option or args.stock_query
    if podcast_id is None or episode_ref is None or stock_query is None:
        parser.error(
            "必須提供 --podcast、--episode 與 --stock，或 positional podcast_id episode_ref stock_query。"
        )

    try:
        local_env_result = _load_local_env_from_args(args)
        provider, model, base_url, api_key_env = _resolve_llm_options(args)
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    debug_output_path = (
        _debug_output_path(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            stock_query=stock_query,
        )
        if args.debug_llm_output
        else None
    )
    if args.confirm and args.api_cost_ack != SEMANTIC_API_COST_ACK:
        if debug_output_path is not None:
            print(f"debug_llm_output_path={debug_output_path}", file=sys.stderr)
        print(
            f"research LLM smoke requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    previous_debug_output_path = os.environ.get(DEBUG_OUTPUT_PATH_ENV)
    if debug_output_path is not None:
        os.environ[DEBUG_OUTPUT_PATH_ENV] = str(debug_output_path)

    try:
        workflow_result = run_research_workflow(
            podcast_id,
            episode_ref,
            stock_query=stock_query,
            confirm=args.confirm,
            force=args.force,
            allow_partial=args.allow_partial,
            include_semantic_summary=args.include_semantic_summary,
            include_stock_lens_synthesis=True,
            include_semantic_context_in_synthesis=args.include_semantic_context,
            include_external_data_verification=args.include_external_data_verification,
            api_cost_ack=args.api_cost_ack,
            semantic_provider=provider,
            semantic_model=model,
            semantic_base_url=base_url,
            semantic_api_key_env=api_key_env,
            synthesis_provider=provider,
            synthesis_model=model,
            synthesis_base_url=base_url,
            synthesis_api_key_env=api_key_env,
            synthesis_max_prompt_chars=args.max_prompt_chars,
            synthesis_semantic_context_max_chars=args.semantic_context_max_chars,
        )
    except PodcastIngestCoreError as exc:
        if debug_output_path is not None:
            print(f"debug_llm_output_path={debug_output_path}", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    except ValueError as exc:
        if debug_output_path is not None:
            print(f"debug_llm_output_path={debug_output_path}", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        if debug_output_path is not None:
            if previous_debug_output_path is None:
                os.environ.pop(DEBUG_OUTPUT_PATH_ENV, None)
            else:
                os.environ[DEBUG_OUTPUT_PATH_ENV] = previous_debug_output_path

    payload = {
        "smoke_mode": SMOKE_MODE,
        "dry_run": not args.confirm,
        "requires_confirmation": not args.confirm,
        "requires_api_cost_ack": True,
        "required_acknowledgement": SEMANTIC_API_COST_ACK,
        "llm_runtime": LLM_RUNTIME,
        "codex_session_backend_supported": False,
        "codex_review_role": "manual_reviewer_only",
        "api_key_value_read": False,
        "provider_config": {
            "llm_profile": args.llm_profile,
            "provider": provider,
            "model": model,
            "base_url_configured": bool(base_url),
            "api_key_env": api_key_env,
            "api_key_value_exposed": False,
        },
        "local_env": local_env_metadata(local_env_result),
        "llm_boundaries": [
            "Stock lens synthesis uses Phase 6F stock lens JSON only unless reviewed semantic context is explicitly included.",
            "Reviewed semantic summary context is an LLM intermediate artifact, not source transcript text or external market data.",
            "Semantic summary sends transcript text only when explicitly included.",
            "The current Codex session is not a direct runtime backend.",
            "No live market data is fetched by this smoke harness.",
            "No investment advice, target price, or guaranteed return is allowed.",
        ],
        "quality_checklist": [
            "Podcast evidence / inference / external status separation",
            "External boundary respected",
            "No not_fetched or not_requested fields turned into market facts",
            "No buy/sell/hold, target price, or guaranteed return",
            "Gooaye Lens dimensions covered",
        ],
        "workflow": to_jsonable(asdict(workflow_result)),
    }
    if debug_output_path is not None:
        payload["debug_llm_output_path"] = str(debug_output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _debug_output_path(*, podcast_id: str, episode_ref: str, stock_query: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = "__".join(
        [
            timestamp,
            title_slug(podcast_id, "podcast"),
            title_slug(episode_ref, "episode"),
            title_slug(stock_query, "stock"),
        ]
    )
    return Path("evals") / "research-llm-smoke" / "raw" / f"{filename}.llm-output.md"


def _resolve_llm_options(args: argparse.Namespace) -> tuple[str, str | None, str | None, str]:
    profile = (
        load_llm_profile(args.llm_profile, args.llm_profile_path)
        if args.llm_profile
        else None
    )
    provider = args.provider or (profile.provider if profile else "openai-compatible")
    model = args.model or (profile.model if profile else None)
    base_url = args.base_url or (profile.base_url if profile else None)
    api_key_env = args.api_key_env or (profile.api_key_env if profile else "API_KEY")
    return provider, model, base_url, api_key_env


def _load_local_env_from_args(args: argparse.Namespace):
    if args.no_env_file:
        return empty_local_env_result(args.env_file)
    return load_local_env(args.env_file)


if __name__ == "__main__":
    main()
