from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    CorpusEpisodeCompletionWorkflowRunnerFailedError,
    run_corpus_episode_completion_workflow,
)
from corpus_ingest_core import (
    corpus_episode_completion_workflow_result_to_dict as result_to_dict,
)
from corpus_ingest_core.corpus_episode_completion_workflow_runner import (
    CONFIRMED_ACTION_MUST_BE_EXPLICIT_MESSAGE,
    CONFIRMED_EPISODE_REF_MUST_BE_CANONICAL_MESSAGE,
    SEMANTIC_SUMMARY_REQUIRES_EXACT_ACK_MESSAGE,
)
from corpus_ingest_core.corpus_semantic_remediation_runner import (
    SEMANTIC_API_COST_ACK,
)
from corpus_ingest_core.local_env import DEFAULT_LOCAL_ENV_PATH, load_local_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or execute one human-approved corpus completion action."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--episode", default="latest", dest="episode_ref")
    parser.add_argument("--action", default="next")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--transcription-model")
    parser.add_argument("--transcription-device", default="cpu")
    parser.add_argument("--transcription-compute-type", default="int8")
    parser.add_argument("--transcription-vad-filter", action="store_true")
    parser.add_argument("--semantic-provider", default="openai-compatible")
    parser.add_argument("--semantic-model")
    parser.add_argument("--semantic-base-url")
    parser.add_argument("--semantic-api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--semantic-chunk-seconds", type=int, default=600)
    parser.add_argument("--semantic-max-segments-per-chunk", type=int, default=120)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    action = args.action.strip() if isinstance(args.action, str) else ""
    episode_ref = args.episode_ref.strip() if isinstance(args.episode_ref, str) else ""

    if args.confirm and action == "next":
        print(CONFIRMED_ACTION_MUST_BE_EXPLICIT_MESSAGE, file=sys.stderr)
        return 1
    if args.confirm and episode_ref == "latest":
        print(CONFIRMED_EPISODE_REF_MUST_BE_CANONICAL_MESSAGE, file=sys.stderr)
        return 1
    if (
        args.confirm
        and action == "semantic_summary"
        and args.api_cost_ack != SEMANTIC_API_COST_ACK
    ):
        print(SEMANTIC_SUMMARY_REQUIRES_EXACT_ACK_MESSAGE, file=sys.stderr)
        return 1
    if args.confirm and action == "semantic_summary":
        try:
            load_local_env(DEFAULT_LOCAL_ENV_PATH)
        except Exception as exc:  # noqa: BLE001 - CLI keeps local configuration bounded.
            print(f"LLM configuration failed: {type(exc).__name__}", file=sys.stderr)
            return 1

    try:
        result = run_corpus_episode_completion_workflow(
            args.podcast_id,
            episode_ref=episode_ref,
            action=action,
            confirm=args.confirm,
            api_cost_ack=args.api_cost_ack,
            transcription_model=args.transcription_model,
            transcription_device=args.transcription_device,
            transcription_compute_type=args.transcription_compute_type,
            transcription_vad_filter=args.transcription_vad_filter,
            semantic_provider=args.semantic_provider,
            semantic_model=args.semantic_model,
            semantic_base_url=args.semantic_base_url,
            semantic_api_key_env=args.semantic_api_key_env,
            semantic_chunk_seconds=args.semantic_chunk_seconds,
            semantic_max_segments_per_chunk=args.semantic_max_segments_per_chunk,
            progress_callback=(
                _print_summary_progress
                if args.confirm and action == "semantic_summary"
                else None
            ),
        )
    except CorpusEpisodeCompletionWorkflowRunnerFailedError as exc:
        print(
            f"{type(exc).__name__}: completion workflow failed",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001 - no raw diagnostics at the CLI boundary.
        print(
            f"{type(exc).__name__}: completion workflow failed",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result_to_dict(result), ensure_ascii=False))
    return 0


def _print_summary_progress(event: str, **payload: object) -> None:
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
            "semantic_summary_progress: "
            f"chunk {payload.get('index')}/{payload.get('total')} {status}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())
