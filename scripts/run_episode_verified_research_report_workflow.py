"""Thin CLI for SPEC 019 explicit-episode verified research report workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core.episode_verified_research_report_workflow_runner import (
    result_to_dict,
    run_episode_verified_research_report_workflow,
)

_FAILURE_ENVELOPE = {
    "ok": False,
    "error_type": "episode_verified_research_report_workflow_failed",
}


class _BoundedArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into a caller-owned bounded JSON response."""

    def error(self, message: str) -> None:
        del message
        raise argparse.ArgumentError(None, "invalid arguments")

    def exit(self, status: int = 0, message: str | None = None) -> None:
        del status, message
        raise argparse.ArgumentError(None, "invalid arguments")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _BoundedArgumentParser(
        description="Preview or publish a verified research report for one explicit episode."
    )
    parser.add_argument("podcast_id", help="Configured podcast id")
    parser.add_argument("episode_ref", help="Explicit episode reference (not latest/next)")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Assemble and publish when ready (default: dry-run preview)",
    )
    parser.add_argument("--stock-query", default=None, help="Optional stock appendix query")
    parser.add_argument(
        "--include-fixture-verification",
        action="store_true",
        help="Require fixture lineage in assembly options",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        result = run_episode_verified_research_report_workflow(
            args.podcast_id,
            args.episode_ref,
            confirm=args.confirm,
            stock_query=args.stock_query,
            include_fixture_verification=args.include_fixture_verification,
        )
        payload = {"ok": True, "data": result_to_dict(result)}
    except Exception:
        print(json.dumps(_FAILURE_ENVELOPE))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
