"""The installed commands must reach a fully registered tool registry.

Tool registration is an import side effect: each ``mcp_tools_*`` group module
calls ``@mcp.tool()`` at import time, and ``mcp_server`` is the only module that
imports the groups. ``mcp_runtime`` owns the bare ``FastMCP`` instance and knows
nothing about tools.

That makes ``[project.scripts]`` a place where the registry can be silently
lost. Pointing an entry point at ``mcp_runtime:run`` yields a server that starts
cleanly, answers the protocol, and advertises nothing -- which is exactly what
0.2.0 shipped in its first draft.

No existing test could catch it. Every in-process test imports ``mcp_server``
somewhere in the session before asserting on the registry, so the groups are
always already loaded by the time the assertion runs. These tests resolve each
entry point the way console-script installation does and load it in a *fresh*
interpreter, where nothing has pre-imported anything.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOL_COUNT = 25


def _declared_entry_points() -> dict[str, str]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["scripts"]


def _tool_count_in_fresh_process(target: str) -> int:
    """Import ``module:attr`` in a new interpreter and count registered tools.

    The child resolves the target exactly as an installed console script does --
    import the module, then get the attribute -- so whatever the import pulls in
    is what the real command would get.
    """

    module, _, attribute = target.partition(":")
    source = (
        "import asyncio, importlib, json\n"
        f"module = importlib.import_module({module!r})\n"
        f"entry = getattr(module, {attribute!r})\n"
        "assert callable(entry)\n"
        "from corpus_ingest_core.mcp_runtime import mcp\n"
        "print(json.dumps(len(asyncio.run(mcp.list_tools()))))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    return json.loads(completed.stdout.strip())


@pytest.mark.parametrize("command", sorted(_declared_entry_points()))
def test_console_entry_point_registers_every_tool(command: str) -> None:
    target = _declared_entry_points()[command]
    count = _tool_count_in_fresh_process(target)
    assert count == EXPECTED_TOOL_COUNT, (
        f"`{command}` resolves to {target}, which registers {count} tools "
        f"instead of {EXPECTED_TOOL_COUNT}. Entry points must target "
        "corpus_ingest_core.mcp_server: importing it is what loads the "
        "mcp_tools_* groups. mcp_runtime alone gives an empty registry."
    )


def test_entry_points_target_the_facade() -> None:
    """Belt and braces: name the requirement, not just its consequence.

    The count assertion above would also pass if some future module happened to
    import the groups as a side effect of something else. The contract is that
    the entry points go through the facade.
    """

    for command, target in _declared_entry_points().items():
        module = target.partition(":")[0]
        assert module == "corpus_ingest_core.mcp_server", (
            f"`{command}` targets {module}. Console scripts must go through "
            "corpus_ingest_core.mcp_server, the module that imports the tool "
            "groups; see the comment above [project.scripts] in pyproject.toml."
        )
