"""Read-only CLI for the verified research report catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import (
    VerifiedResearchReportCatalogInputError,
    inspect_verified_research_report,
    list_verified_research_reports,
    search_verified_research_reports,
    verified_research_report_catalog_result_to_dict,
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="Query the local verified research report catalog.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--podcast-id")
    list_parser.add_argument("--episode-ref")
    list_parser.add_argument("--limit", type=int, default=50)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--podcast-id")
    search_parser.add_argument("--episode-ref")
    search_parser.add_argument("--limit", type=int, default=50)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("podcast_id")
    inspect_parser.add_argument("episode_ref")
    inspect_parser.add_argument("source_digest")
    return parser


def _error() -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "VerifiedResearchReportCatalogInputError",
                "message": "verified research report catalog query failed",
            }
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.action == "list":
            result = list_verified_research_reports(
                podcast_id=args.podcast_id,
                episode_ref=args.episode_ref,
                limit=args.limit,
            )
        elif args.action == "search":
            result = search_verified_research_reports(
                args.query,
                podcast_id=args.podcast_id,
                episode_ref=args.episode_ref,
                limit=args.limit,
            )
        else:
            result = inspect_verified_research_report(
                args.podcast_id,
                args.episode_ref,
                args.source_digest,
            )
    except (ValueError, VerifiedResearchReportCatalogInputError):
        return _error()
    except Exception:
        return _error()
    print(json.dumps({"ok": True, "data": verified_research_report_catalog_result_to_dict(result)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
