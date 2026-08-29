from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    PodcastIngestCoreError,
    run_study_guide_bundle,
    study_guide_bundle_result_to_dict,
)
from corpus_ingest_core.local_env import load_local_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or write one learning-notes study-guide bundle."
    )
    parser.add_argument("--podcast", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--api-cost-ack", default="")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env", default="API_KEY")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--read-timeout-seconds", type=int, default=120)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.confirm:
        load_local_env()
    try:
        result = run_study_guide_bundle(
            args.podcast,
            args.episode,
            confirm=args.confirm,
            force=args.force,
            api_cost_ack=args.api_cost_ack,
            provider=args.provider or "openai-compatible",
            model=args.model,
            base_url=args.base_url,
            api_key_env=args.api_key_env,
            reasoning_effort=args.reasoning_effort,
            read_timeout_seconds=args.read_timeout_seconds,
        )
    except PodcastIngestCoreError as exc:
        print(
            f"study-guide bundle command failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001 - CLI must not expose raw diagnostics.
        print(
            f"study-guide bundle command failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print(json.dumps(study_guide_bundle_result_to_dict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
