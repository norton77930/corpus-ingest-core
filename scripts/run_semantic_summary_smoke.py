from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    PodcastIngestCoreError,
    load_llm_profile,
    semantic_summarize_episode,
    validate_transcript,
)
from corpus_ingest_core.llm_profiles import DEFAULT_LLM_PROFILES_CONFIG_PATH
from corpus_ingest_core.local_env import (
    DEFAULT_LOCAL_ENV_PATH,
    empty_local_env_result,
    load_local_env,
    local_env_metadata,
)
from corpus_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
from corpus_ingest_core.serialization import to_jsonable

SMOKE_MODE = "semantic-summary-smoke-v1"
LLM_RUNTIME = "openai-compatible /chat/completions"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a dry-run-first semantic summary LLM smoke.")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
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
    parser.add_argument("--chunk-seconds", type=int, default=600)
    parser.add_argument("--max-segments-per-chunk", type=int, default=120)
    args = parser.parse_args()

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("Provide --podcast and --episode, or positional podcast_id episode_ref.")

    try:
        local_env_result = _load_local_env_from_args(args)
        provider, model, base_url, api_key_env = _resolve_llm_options(args)
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    if args.confirm and args.api_cost_ack != SEMANTIC_API_COST_ACK:
        print(
            f"semantic summary smoke requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    try:
        validation = validate_transcript(podcast_id, episode_ref)
        if args.confirm:
            summary = semantic_summarize_episode(
                podcast_id,
                episode_ref,
                api_cost_ack=args.api_cost_ack,
                provider=provider,
                model=model,
                base_url=base_url,
                api_key_env=api_key_env,
                force=args.force,
                chunk_seconds=args.chunk_seconds,
                max_segments_per_chunk=args.max_segments_per_chunk,
                allow_partial=args.allow_partial,
                progress_callback=_print_progress,
            )
        else:
            summary = None
    except PodcastIngestCoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    payload = {
        "smoke_mode": SMOKE_MODE,
        "dry_run": not args.confirm,
        "requires_confirmation": not args.confirm,
        "requires_api_cost_ack": True,
        "required_acknowledgement": SEMANTIC_API_COST_ACK,
        "llm_runtime": LLM_RUNTIME,
        "api_key_value_read": False,
        "transcript_status": validation.status,
        "segment_count": validation.segment_count,
        "transcript_text_length": validation.transcript_text_length,
        "planned_reads": [
            validation.paths.get("json", ""),
            validation.paths.get("text", ""),
        ],
        "planned_writes": [f"data/summaries/{podcast_id}/{episode_ref}__{{safe_title_slug}}.semantic.md"],
        "risks": [
            "Calls an external LLM API when confirmed.",
            "Sends transcript text outside this machine when confirmed.",
            "May incur API cost risk when confirmed.",
        ],
        "provider_config": {
            "llm_profile": args.llm_profile,
            "provider": provider,
            "model": model,
            "base_url_configured": bool(base_url),
            "api_key_env": api_key_env,
            "api_key_value_exposed": False,
        },
        "local_env": local_env_metadata(local_env_result),
        "not_investment_advice": True,
        "cache_stale_warning": "Cache may be stale. Run rebuild_cache manually after semantic summary generation.",
        "raw_transcript_text_returned": False,
    }
    if summary is not None:
        payload["summary"] = to_jsonable(asdict(summary))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_llm_options(args: argparse.Namespace) -> tuple[str, str | None, str | None, str]:
    profile = load_llm_profile(args.llm_profile, args.llm_profile_path) if args.llm_profile else None
    provider = args.provider or (profile.provider if profile else "openai-compatible")
    model = args.model or (profile.model if profile else None)
    base_url = args.base_url or (profile.base_url if profile else None)
    api_key_env = args.api_key_env or (profile.api_key_env if profile else "API_KEY")
    return provider, model, base_url, api_key_env


def _load_local_env_from_args(args: argparse.Namespace):
    if args.no_env_file:
        return empty_local_env_result(args.env_file)
    return load_local_env(args.env_file)


def _print_progress(event: str, **payload) -> None:
    if event == "chunk_count":
        print(
            f"semantic_summary_progress: chunk_count={payload['chunk_count']} llm_requests={payload['llm_requests']}",
            file=sys.stderr,
        )
    elif event in {"chunk_start", "chunk_done"}:
        status = "start" if event == "chunk_start" else "done"
        print(
            f"semantic_summary_progress: chunk {payload['index']}/{payload['total']} {status}",
            file=sys.stderr,
        )
    elif event == "final_start":
        print("semantic_summary_progress: final_summary start", file=sys.stderr)
    elif event == "final_done":
        print("semantic_summary_progress: final_summary done", file=sys.stderr)


if __name__ == "__main__":
    main()
