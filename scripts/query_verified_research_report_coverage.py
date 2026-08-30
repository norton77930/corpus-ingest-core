"""Read-only CLI for verified research report episode coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    VerifiedResearchReportCoverageInputError,
    list_verified_research_report_coverage,
    verified_research_report_coverage_result_to_dict,
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="List episode coverage of local verified research report bundles.")
    parser.add_argument("podcast_id")
    parser.add_argument(
        "--has-bundle",
        choices=("true", "false"),
        default=None,
        help="Optional filter: only episodes with or without a bundle.",
    )
    parser.add_argument("--limit", type=int, default=50)
    return parser


def _error() -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "VerifiedResearchReportCoverageInputError",
                "message": "verified research report coverage query failed",
            }
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        has_bundle: bool | None
        if args.has_bundle is None:
            has_bundle = None
        else:
            has_bundle = args.has_bundle == "true"
        result = list_verified_research_report_coverage(
            args.podcast_id,
            has_bundle=has_bundle,
            limit=args.limit,
        )
        print(json.dumps(verified_research_report_coverage_result_to_dict(result), ensure_ascii=False))
        return 0
    except (VerifiedResearchReportCoverageInputError, ValueError, TypeError):
        return _error()
    except Exception:
        return _error()


if __name__ == "__main__":
    raise SystemExit(main())
