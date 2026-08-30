from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    CorpusSemanticRemediationRunnerFailedError,
    PodcastIngestCoreError,
    load_llm_profile,
    run_corpus_semantic_remediation,
)
from corpus_ingest_core.corpus_semantic_remediation_runner import result_to_dict
from corpus_ingest_core.llm_profiles import DEFAULT_LLM_PROFILES_CONFIG_PATH
from corpus_ingest_core.local_env import (
    DEFAULT_LOCAL_ENV_PATH,
    empty_local_env_result,
    load_local_env,
)
from corpus_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or run one corpus semantic remediation action.")
    parser.add_argument("--podcast", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--action", default="next")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--llm-profile")
    parser.add_argument(
        "--llm-profile-path",
        default=str(DEFAULT_LLM_PROFILES_CONFIG_PATH),
    )
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--read-timeout-seconds", type=int, default=120)
    parser.add_argument("--env-file", default=str(DEFAULT_LOCAL_ENV_PATH))
    parser.add_argument("--no-env-file", action="store_true")
    parser.add_argument("--chunk-seconds", type=int, default=600)
    parser.add_argument("--max-segments-per-chunk", type=int, default=120)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    action = args.action.strip()

    if args.confirm and action == "semantic_summary" and args.api_cost_ack != SEMANTIC_API_COST_ACK:
        print(
            f"semantic_summary requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    provider = args.provider or "openai-compatible"
    model = args.model
    base_url = args.base_url
    api_key_env = args.api_key_env or "OPENAI_API_KEY"
    if args.confirm and action == "semantic_summary":
        try:
            _load_local_env_from_args(args)
            provider, model, base_url, api_key_env = _resolve_llm_options(args)
        except PodcastIngestCoreError as exc:
            print(
                f"LLM configuration failed: {type(exc).__name__}",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc
        except (OSError, ValueError) as exc:
            print(
                f"LLM configuration failed: {type(exc).__name__}",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc

    try:
        result = run_corpus_semantic_remediation(
            args.podcast,
            episode_ref=args.episode,
            action=action,
            confirm=args.confirm,
            api_cost_ack=args.api_cost_ack,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            reasoning_effort=args.reasoning_effort,
            read_timeout_seconds=args.read_timeout_seconds,
            chunk_seconds=args.chunk_seconds,
            max_segments_per_chunk=args.max_segments_per_chunk,
            progress_callback=(_print_progress if args.confirm and action == "semantic_summary" else None),
        )
    except CorpusSemanticRemediationRunnerFailedError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    except PodcastIngestCoreError as exc:
        print(
            f"corpus semantic remediation command failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    except (OSError, ValueError) as exc:
        print(
            f"corpus semantic remediation command failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001 - CLI must not expose raw diagnostics.
        print(
            f"corpus semantic remediation command failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))


def _resolve_llm_options(
    args: argparse.Namespace,
) -> tuple[str, str | None, str | None, str]:
    profile = load_llm_profile(args.llm_profile, args.llm_profile_path) if args.llm_profile else None
    provider = args.provider or (profile.provider if profile else "openai-compatible")
    model = args.model or (profile.model if profile else None)
    base_url = args.base_url or (profile.base_url if profile else None)
    api_key_env = args.api_key_env or (profile.api_key_env if profile else "OPENAI_API_KEY")
    return provider, model, base_url, api_key_env


def _load_local_env_from_args(args: argparse.Namespace):
    if args.no_env_file:
        return empty_local_env_result(args.env_file)
    return load_local_env(args.env_file)


def _print_progress(event: str, **payload: object) -> None:
    if event == "chunk_count":
        print(
            "semantic_summary_progress: "
            f"chunk_count={payload.get('chunk_count')} "
            f"llm_requests={payload.get('llm_requests')}",
            file=sys.stderr,
        )
    elif event in {"chunk_start", "chunk_done"}:
        status = "start" if event == "chunk_start" else "done"
        print(
            f"semantic_summary_progress: chunk {payload.get('index')}/{payload.get('total')} {status}",
            file=sys.stderr,
        )
    elif event == "final_start":
        print("semantic_summary_progress: final_summary start", file=sys.stderr)
    elif event == "final_done":
        print("semantic_summary_progress: final_summary done", file=sys.stderr)


if __name__ == "__main__":
    main()
