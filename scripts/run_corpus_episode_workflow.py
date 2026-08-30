from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import run_corpus_episode_workflow
from corpus_ingest_core.corpus_episode_workflow_runner import result_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview or run the next safe corpus episode workflow stage.")
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--episode", default="latest", dest="episode_ref")
    parser.add_argument("--stage", dest="stage")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8", dest="compute_type")
    parser.add_argument("--vad-filter", action="store_true", dest="vad_filter")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true", dest="allow_partial")
    parser.add_argument("--max-actions", type=int, dest="max_actions")
    args = parser.parse_args(argv)

    if args.confirm and args.stage != "next":
        print("confirmed workflow requires explicit --stage next", file=sys.stderr)
        return 1

    try:
        result = run_corpus_episode_workflow(
            args.podcast_id,
            episode_ref=args.episode_ref,
            stage=args.stage or "next",
            confirm=args.confirm,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            vad_filter=args.vad_filter,
            force=args.force,
            allow_partial=args.allow_partial,
            max_actions=args.max_actions,
        )
        output = json.dumps(result_to_dict(result), ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001 - CLI boundary emits category only.
        print(f"{type(exc).__name__}: workflow failed", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
