from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError,
    corpus_latest_episode_deterministic_workflow_result_to_dict as result_to_dict,
    run_corpus_latest_episode_deterministic_workflow,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or process one latest episode through local deterministic stages."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--transcription-model")
    parser.add_argument("--transcription-device", default="cpu")
    parser.add_argument("--transcription-compute-type", default="int8")
    parser.add_argument("--transcription-vad-filter", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_corpus_latest_episode_deterministic_workflow(
            args.podcast_id,
            confirm=args.confirm,
            transcription_model=args.transcription_model,
            transcription_device=args.transcription_device,
            transcription_compute_type=args.transcription_compute_type,
            transcription_vad_filter=args.transcription_vad_filter,
        )
    except CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError:
        print("CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError: workflow failed", file=sys.stderr)
        return 1
    except Exception:  # noqa: BLE001 - keep the CLI boundary metadata-only.
        print("CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError: workflow failed", file=sys.stderr)
        return 1

    print(json.dumps(result_to_dict(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
