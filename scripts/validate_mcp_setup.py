from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import storage
from podcast_ingest_core.errors import PodcastIngestCoreError
from podcast_ingest_core.search import search_mentions, search_transcripts


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_mcp_server.py"
DEFAULT_QUERY = "台積電"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="驗證本機 MCP server setup readiness。")
    parser.add_argument("--podcast", default="gooaye", help="Podcast ID，預設 gooaye。")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Search smoke query。")
    return parser.parse_args(argv)


def run_validation(podcast_id: str = "gooaye", query: str = DEFAULT_QUERY) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    next_steps = [
        "Configure Codex ~/.codex/config.toml with the stdio server command.",
        "Run /mcp in Codex TUI to confirm the server is active.",
        "For Claude-style clients, configure a stdio MCP server pointing to scripts/run_mcp_server.py.",
    ]

    _add_check(
        checks,
        "python_version",
        sys.version_info >= (3, 11),
        version=platform.python_version(),
    )

    mcp_server = None
    try:
        import podcast_ingest_core  # noqa: F401

        _add_check(checks, "package_import", True)
    except Exception as exc:
        _add_check(checks, "package_import", False, message=str(exc))

    try:
        from podcast_ingest_core import mcp_server as imported_mcp_server

        mcp_server = imported_mcp_server
        _add_check(checks, "mcp_server_import", True)
    except Exception as exc:
        _add_check(checks, "mcp_server_import", False, message=str(exc))

    if mcp_server is not None:
        server_name = getattr(getattr(mcp_server, "mcp", None), "name", None)
        _add_check(
            checks,
            "mcp_server_object",
            server_name == "podcast-ingest-core",
            server_name=server_name,
        )
    else:
        _add_check(checks, "mcp_server_object", False, message="mcp_server import failed.")

    _add_check(
        checks,
        "run_mcp_server_exists",
        RUNNER_PATH.exists(),
        path=str(RUNNER_PATH),
    )

    cache_path = storage.cache_db_path()
    cache_exists = cache_path.exists()
    _add_check(checks, "cache_db_exists", cache_exists, path=str(cache_path))
    if not cache_exists:
        warnings.append(
            f"Run python scripts/rebuild_cache.py --podcast {podcast_id} --force before using search tools."
        )
    else:
        _check_search_tools(checks, warnings, podcast_id=podcast_id, query=query)

    if mcp_server is not None:
        _check_mcp_guards(checks, mcp_server, podcast_id=podcast_id)
    else:
        _add_check(checks, "side_effect_dry_run_protection", False, message="mcp_server import failed.")
        _add_check(checks, "semantic_ack_guard", False, message="mcp_server import failed.")

    ok = all(check["ok"] for check in checks)
    return {
        "ok": ok,
        "checks": checks,
        "warnings": warnings,
        "next_steps": next_steps,
    }


def main() -> None:
    args = parse_args()
    payload = run_validation(podcast_id=args.podcast, query=args.query)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _check_search_tools(
    checks: list[dict[str, Any]],
    warnings: list[str],
    *,
    podcast_id: str,
    query: str,
) -> None:
    try:
        transcript_results = search_transcripts(
            query,
            podcast_id=podcast_id,
            limit=5,
            search_mode="auto",
        )
        _add_check(
            checks,
            "search_transcripts",
            bool(transcript_results),
            result_count=len(transcript_results),
        )
        if not transcript_results:
            warnings.append(f"Transcript search returned no results for query: {query}")
    except PodcastIngestCoreError as exc:
        _add_check(checks, "search_transcripts", False, message=str(exc))
    except Exception as exc:
        _add_check(checks, "search_transcripts", False, message=str(exc))

    try:
        mention_results = search_mentions(query, podcast_id=podcast_id, limit=5)
        _add_check(
            checks,
            "search_mentions",
            bool(mention_results),
            result_count=len(mention_results),
        )
        if not mention_results:
            warnings.append(f"Mention search returned no results for query: {query}")
    except PodcastIngestCoreError as exc:
        _add_check(checks, "search_mentions", False, message=str(exc))
    except Exception as exc:
        _add_check(checks, "search_mentions", False, message=str(exc))


def _check_mcp_guards(checks: list[dict[str, Any]], mcp_server, *, podcast_id: str) -> None:
    try:
        dry_run = mcp_server.transcribe_episode(
            podcast_id=podcast_id,
            episode_ref="latest",
            confirm=False,
        )
        _add_check(
            checks,
            "side_effect_dry_run_protection",
            dry_run.get("ok") is True and dry_run.get("dry_run") is True,
            tool="transcribe_episode",
        )
    except Exception as exc:
        _add_check(checks, "side_effect_dry_run_protection", False, message=str(exc))

    try:
        rejected = mcp_server.semantic_summarize_episode(
            podcast_id=podcast_id,
            episode_ref="latest",
            confirm=True,
            api_cost_ack="",
        )
        _add_check(
            checks,
            "semantic_ack_guard",
            rejected.get("ok") is False and rejected.get("error_type") == "ValueError",
            tool="semantic_summarize_episode",
        )
    except Exception as exc:
        _add_check(checks, "semantic_ack_guard", False, message=str(exc))


def _add_check(
    checks: list[dict[str, Any]],
    name: str,
    ok: bool,
    **metadata: Any,
) -> None:
    check = {"name": name, "ok": bool(ok)}
    check.update(metadata)
    checks.append(check)


if __name__ == "__main__":
    main()
