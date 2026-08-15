"""MCP tool group: stock lens (Tool 22).

Registration order is import order, and this module is imported last by the
``mcp_server`` facade, so Tools 1-21 keep their existing positions.

``generate_stock_lens_report`` completes Spec 001 User Story 3 over MCP: the
deterministic Core capability already exists and is reachable from the CLI, but
an agent could not call it. The report is built only from local mapping and
external-data-boundary artifacts — no live market API, no LLM, no network — and
it never answers whether to buy or sell.
"""

from __future__ import annotations

from typing import Any

from . import mcp_runtime
from . import stock_lens
from .mcp_runtime import mcp, tool_action_plan


MIN_EVIDENCE_ITEMS = 1
MAX_EVIDENCE_ITEMS = 50
STOCK_LENS_CACHE_STALE_WARNING = (
    "Cache may be stale after completion; run rebuild_cache manually."
)
NOT_INVESTMENT_ADVICE = (
    "Research framework only: no buy/sell/hold, target price, or guaranteed return."
)


@mcp.tool()
def generate_stock_lens_report(
    podcast_id: str = "gooaye",
    stock_query: str = "",
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    max_evidence_items: int = 10,
) -> dict[str, Any]:
    """Side-effect tool：需要 confirm=true 才會寫入 deterministic stock lens report。"""

    clamped_max_evidence = mcp_runtime._clamp(
        max_evidence_items,
        MIN_EVIDENCE_ITEMS,
        MAX_EVIDENCE_ITEMS,
    )
    inputs = {
        "podcast_id": podcast_id,
        "stock_query": stock_query,
        "force": force,
        "allow_partial": allow_partial,
        "max_evidence_items": clamped_max_evidence,
    }
    if not confirm:
        return tool_action_plan(
            tool_name="generate_stock_lens_report",
            action=(
                "Read existing local industry-mapping and external-data-boundary "
                "artifacts and write one deterministic stock lens report."
            ),
            inputs=inputs,
            writes=[
                f"data/stock-lens/{podcast_id}/...",
            ],
            risks=[
                "Writes stock lens JSON and Markdown artifacts under data/stock-lens",
                "Reads only local artifacts: no live market API, no network, no LLM",
                "May overwrite an existing report when force=true",
                "A partial-draft external boundary is refused unless allow_partial=true",
                "Cache may be stale after completion; run rebuild_cache manually",
                NOT_INVESTMENT_ADVICE,
            ],
        )

    return mcp_runtime._tool_call(
        lambda: stock_lens.generate_stock_lens_report(
            inputs["podcast_id"],
            inputs["stock_query"],
            force=inputs["force"],
            allow_partial=inputs["allow_partial"],
            max_evidence_items=inputs["max_evidence_items"],
        ),
        warnings=[STOCK_LENS_CACHE_STALE_WARNING, NOT_INVESTMENT_ADVICE],
    )
