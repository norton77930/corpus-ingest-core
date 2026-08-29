"""Read-only CLI for exact verified-report source revalidation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import (
    VerifiedResearchReportSourceRevalidationInputError,
    revalidate_verified_research_report_sources,
    verified_research_report_source_revalidation_result_to_dict,
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="Revalidate one exact verified report source locator.")
    parser.add_argument("podcast_id")
    parser.add_argument("episode_ref")
    parser.add_argument("source_digest")
    return parser


def _error() -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "VerifiedResearchReportSourceRevalidationInputError",
                "message": "verified research report source revalidation failed",
            }
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = revalidate_verified_research_report_sources(
            args.podcast_id,
            args.episode_ref,
            args.source_digest,
        )
        payload = verified_research_report_source_revalidation_result_to_dict(result)
    except (ValueError, VerifiedResearchReportSourceRevalidationInputError):
        return _error()
    except Exception:
        return _error()
    print(json.dumps({"ok": True, "data": payload}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
