"""Read-only CLI for historical verified-report next-step suggestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    HistoricalVerifiedReportPathInputError,
    suggest_historical_verified_report_next_step,
    historical_verified_report_path_result_to_dict,
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        description="Suggest one next human-gated step toward a historical verified report."
    )
    parser.add_argument("podcast_id")
    parser.add_argument("episode_ref")
    return parser


def _error() -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "HistoricalVerifiedReportPathInputError",
                "message": "historical verified report path suggestion failed",
            }
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = suggest_historical_verified_report_next_step(
            args.podcast_id, args.episode_ref
        )
        print(
            json.dumps(
                historical_verified_report_path_result_to_dict(result),
                ensure_ascii=False,
            )
        )
        return 0
    except (HistoricalVerifiedReportPathInputError, ValueError, TypeError):
        return _error()
    except Exception:
        return _error()


if __name__ == "__main__":
    raise SystemExit(main())
