from __future__ import annotations

import argparse
import asyncio
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
COMPLETION_TOOL_NAME = "run_corpus_episode_completion_workflow"
COMPLETION_SKILL_PATH = (
    PROJECT_ROOT / ".agents" / "skills" / "corpus-episode-completion" / "SKILL.md"
)


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
        _check_completion_surface(checks, mcp_server)
    else:
        _add_check(checks, "side_effect_dry_run_protection", False, message="mcp_server import failed.")
        _add_check(checks, "semantic_ack_guard", False, message="mcp_server import failed.")
        _add_check(checks, "completion_tool_registry", False, message="mcp_server import failed.")
        _add_check(checks, "completion_skill_metadata", False, message="mcp_server import failed.")
        _add_check(
            checks,
            "completion_confirmed_next_guard",
            False,
            message="mcp_server import failed.",
        )

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


def _check_completion_surface(checks: list[dict[str, Any]], mcp_server) -> None:
    """Check only locally discoverable 016 agent-surface safety boundaries."""

    try:
        tools = asyncio.run(mcp_server.mcp.list_tools())
        tool_names = {tool.name for tool in tools}
        _add_check(
            checks,
            "completion_tool_registry",
            len(tool_names) == 13 and COMPLETION_TOOL_NAME in tool_names,
            tool_count=len(tool_names),
            tool=COMPLETION_TOOL_NAME,
        )
    except Exception:
        _add_check(
            checks,
            "completion_tool_registry",
            False,
            message="completion tool registry discovery failed.",
        )

    try:
        skill_text = COMPLETION_SKILL_PATH.read_text(encoding="utf-8")
        _add_check(
            checks,
            "completion_skill_metadata",
            _has_completion_skill_metadata(skill_text),
            path=str(COMPLETION_SKILL_PATH),
        )
    except OSError:
        _add_check(
            checks,
            "completion_skill_metadata",
            False,
            message="completion skill metadata is unavailable.",
        )

    try:
        rejected = mcp_server.run_corpus_episode_completion_workflow(
            podcast_id="unsafe/podcast",
            episode_ref="latest",
            action="next",
            confirm=True,
        )
        _add_check(
            checks,
            "completion_confirmed_next_guard",
            rejected.get("ok") is False
            and rejected.get("error_type")
            == "CorpusEpisodeCompletionWorkflowRunnerFailedError",
            tool=COMPLETION_TOOL_NAME,
        )
    except Exception:
        _add_check(
            checks,
            "completion_confirmed_next_guard",
            False,
            message="completion confirmed-next guard failed.",
        )


def _has_completion_skill_metadata(skill_text: str) -> bool:
    lines = skill_text.splitlines()
    return (
        len(lines) >= 4
        and lines[0] == "---"
        and lines[1] == "name: corpus-episode-completion"
        and lines[2]
        == "description: Safely preview and advance one podcast episode by one explicit MCP-managed action with human approval."
        and lines[3] == "---"
    )


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
