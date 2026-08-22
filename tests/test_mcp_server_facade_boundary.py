"""Boundary guard: the MCP server facade split stays single-instance and acyclic.

specs/025-core-consolidation FR-005 / FR-006 / FR-010:

1. Exactly one ``FastMCP(`` construction in ``src`` — in ``mcp_runtime.py``.
2. Every ``@mcp.tool()`` decoration lives in the ``mcp_tools_*`` group
   modules; the facade itself registers nothing.
3. Group modules and ``mcp_runtime`` never import ``mcp_server`` (cycle ban).
4. The facade re-exports every dependency alias and tool name that tests and
   clients reach through ``mcp_server.<attr>`` — a missing alias makes
   monkeypatching silently miss, so the list is asserted explicitly.
5. The completion confirmed-request rejection messages are defined in exactly
   one ``src`` module (the Core runner); MCP and CLI reuse them.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "podcast_ingest_core"
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

GROUP_MODULES = (
    "mcp_tools_stock_lens.py",
    "mcp_tools_read.py",
    "mcp_tools_side_effect.py",
    "mcp_tools_corpus_workflows.py",
    "mcp_tools_verified_report_queries.py",
    "mcp_tools_x_video.py",
    "mcp_tools_youtube_video.py",
    "mcp_tools_workflow_derivation.py",
)

FACADE_EXPORTS = (
    # runtime surface
    "mcp",
    "run",
    "run_streamable_http",
    "StreamableHttpConfig",
    "tool_success",
    "tool_error",
    "tool_action_plan",
    "SEMANTIC_API_COST_ACK",
    # dependency-module aliases used by tests' monkeypatching
    "cache_module",
    "completion_workflow_runner",
    "downloader",
    "entity_extractor",
    "feed_reader",
    "latest_deterministic_workflow_runner",
    "research_workflow",
    "search_module",
    "semantic_summarizer",
    "summarizer",
    "transcriber",
    "validator",
    "stock_lens",
    "x_video_ingest",
    "youtube_video_ingest",
    "verified_research_report_workflow_runner",
    "mcp_episode_verified_research_report",
    "mcp_verified_research_report_catalog",
    "mcp_historical_verified_report_path",
    "mcp_verified_report_gap_backlog",
    "mcp_verified_research_report_coverage",
    "mcp_verified_research_report_source_revalidation",
)

REJECTION_MESSAGES = (
    "confirmed action must be explicit",
    "confirmed episode_ref must be canonical",
    "semantic_summary requires exact api_cost_ack",
)


def test_exactly_one_fastmcp_construction_in_src():
    constructors = []
    for path in sorted(SRC_DIR.glob("*.py")):
        if re.search(r"FastMCP\(", path.read_text(encoding="utf-8")):
            constructors.append(path.name)
    assert constructors == ["mcp_runtime.py"], (
        f"FastMCP may be constructed only in mcp_runtime.py; found: {constructors}"
    )


def test_all_tool_decorations_live_in_group_modules():
    offenders = []
    for path in sorted(SRC_DIR.glob("*.py")):
        if "@mcp.tool()" not in path.read_text(encoding="utf-8"):
            continue
        if path.name not in GROUP_MODULES:
            offenders.append(path.name)
    assert not offenders, (
        f"@mcp.tool() registrations belong in the mcp_tools_* groups: {offenders}"
    )


def test_group_modules_never_import_the_facade():
    offenders = []
    for name in GROUP_MODULES + ("mcp_runtime.py",):
        text = (SRC_DIR / name).read_text(encoding="utf-8")
        if re.search(r"^\s*from\s+\.\s*import\s+.*\bmcp_server\b", text, re.M) or re.search(
            r"^\s*from\s+\.mcp_server\s+import", text, re.M
        ):
            offenders.append(name)
    assert not offenders, f"import cycle ban violated by: {offenders}"


def test_group_modules_do_not_value_bind_private_runtime_helpers():
    """Private runtime helpers stay patchable through the runtime module."""

    offenders = []
    for name in GROUP_MODULES:
        tree = ast.parse((SRC_DIR / name).read_text(encoding="utf-8"))
        private_imports = sorted(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "mcp_runtime"
            for alias in node.names
            if alias.name.startswith("_")
        )
        if private_imports:
            offenders.append(f"{name}: {private_imports}")
    assert not offenders, (
        "mcp_tools_* modules must access private runtime helpers through "
        f"mcp_runtime.<name> so monkeypatching remains live: {offenders}"
    )


def test_group_modules_are_imported_only_via_the_facade():
    """Registration order (Tools 1-25) is defined by the facade's group-import
    order; a direct group import in a fresh process (or earlier in the pytest
    session) would register its tools first. Ban direct imports everywhere
    except the facade itself."""
    import_pattern = re.compile(
        r"(?:from|import)\s+(?:podcast_ingest_core\.|\.)?\s*mcp_tools_"
    )
    self_name = Path(__file__).name
    offenders = []
    for root in (SRC_DIR, SCRIPTS_DIR, Path(__file__).resolve().parent):
        for path in sorted(root.glob("*.py")):
            if path.name == self_name or (
                root == SRC_DIR and path.name == "mcp_server.py"
            ):
                continue
            if import_pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(f"{root.name}/{path.name}")
    assert not offenders, (
        "mcp_tools_* group modules must be imported only by the mcp_server "
        f"facade (import order = registration order): {offenders}"
    )


def test_facade_exposes_every_contracted_alias():
    from podcast_ingest_core import mcp_server

    missing = [name for name in FACADE_EXPORTS if not hasattr(mcp_server, name)]
    assert not missing, (
        "facade re-export list drifted — monkeypatching would silently miss: "
        f"{missing}"
    )


def test_registered_tools_are_reexported_by_the_facade():
    import asyncio

    from podcast_ingest_core import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    missing = [tool.name for tool in tools if not hasattr(mcp_server, tool.name)]
    assert not missing, f"registered tools missing from facade exports: {missing}"


def test_completion_rejection_messages_have_one_defining_module():
    defining = set()
    for path in sorted(SRC_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(f'"{message}"' in text for message in REJECTION_MESSAGES):
            defining.add(path.name)
    assert defining == {"corpus_episode_completion_workflow_runner.py"}, (
        "completion rejection messages must be defined once in Core: "
        f"{sorted(defining)}"
    )
    cli_text = (SCRIPTS_DIR / "run_corpus_episode_completion_workflow.py").read_text(
        encoding="utf-8"
    )
    assert not any(f'"{message}"' in cli_text for message in REJECTION_MESSAGES), (
        "the CLI must import the canonical message constants, not re-type them"
    )
