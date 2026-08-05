"""Read-only CLI for verified report gap backlog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import (
    VerifiedReportGapBacklogInputError,
    list_verified_report_gap_backlog,
    verified_report_gap_backlog_result_to_dict,
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        description="List inventory episodes missing a verified research report bundle."
    )
    parser.add_argument("podcast_id")
    parser.add_argument("--limit", type=int, default=50)
    return parser


def _error() -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "VerifiedReportGapBacklogInputError",
                "message": "verified report gap backlog query failed",
            }
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = list_verified_report_gap_backlog(args.podcast_id, limit=args.limit)
        print(
            json.dumps(
                verified_report_gap_backlog_result_to_dict(result),
                ensure_ascii=False,
            )
        )
        return 0
    except (VerifiedReportGapBacklogInputError, ValueError, TypeError):
        return _error()
    except Exception:
        return _error()


if __name__ == "__main__":
    raise SystemExit(main())
