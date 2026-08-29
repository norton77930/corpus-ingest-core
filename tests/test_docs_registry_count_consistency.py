"""Registry-derived tool-count consistency across governed docs.

specs/025-core-consolidation FR-007: every explicit tool-count claim
("exact(ly) N tools" / "恰(好) N 個") in the governed docs must either match
the live registry count or carry a historical marker; files named *closeout*
are historical records and exempt as a whole. This is the drift defense the
per-doc literal pins could not provide: the moment the registry changes, any
unmarked stale claim fails here with its file:line, instead of surviving as
a frozen wrong number.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CLAIM_PATTERNS = (
    re.compile(
        r"exact(?:ly)?\s+(\d+)\s+(?:reviewed\s+|MCP\s+)*tools", re.IGNORECASE
    ),
    re.compile(r"恰(?:好)?\s*(?:暴露\s*)?(\d+)\s*個"),
    # "22 個 MCP tools" and "tool registry 完整（22 個）" both survived three
    # tool additions in docs/install-and-porting.md because neither carries
    # "恰"/"恰好". A claim does not need that adverb to be a claim.
    re.compile(r"(\d+)\s*個\s*(?:reviewed\s*)?(?:MCP\s*)?tools?", re.IGNORECASE),
    re.compile(r"registry\s*完整\s*[（(]\s*(\d+)\s*個"),
)

# Feature names that merely contain a marker word. Tool 20 is literally called
# "historical next-step suggestion", so a current-tense count claim sharing that
# line was silently treated as historical and skipped — the exact drift this
# check exists to catch. Strip these before marker matching.
MARKER_FALSE_POSITIVES = (
    "suggest_historical_verified_report_next_step",
    "historical-episode-verified-report-path",
    "historical next-step",
    "historical verified-report path",
    "historical verified report path",
    "historical episode",
)

# A wrong count is acceptable only on a line that explicitly reads as history.
HISTORICAL_MARKERS = (
    "was ",
    "were ",
    "had ",
    "before ",
    "at the time",
    "landed",
    "at closeout",
    "historical",
    "changed the",  # NOT bare "changed": it is a substring of "unchanged"
    "made the",
    "extended",
    "addition set",
    "當時",
    "歷史",
    "曾",
)


def _governed_files() -> list[Path]:
    files = [
        ROOT / "README.md",
        ROOT / "README.zh-TW.md",
        ROOT / "specs" / "README.md",
    ]
    files.extend(sorted((ROOT / "docs").rglob("*.md")))
    return files


def _live_tool_count() -> int:
    from podcast_ingest_core import mcp_server

    return len(asyncio.run(mcp_server.mcp.list_tools()))


def test_every_tool_count_claim_is_current_or_marked_historical():
    expected = _live_tool_count()
    problems = []
    for path in _governed_files():
        if "closeout" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.casefold()
            # Only lines that are about the tool registry are claims; this
            # keeps "恰好 N 個" phrases counting other things (reports,
            # stages, 欄位...) out of the tool-count check.
            if "tool" not in lowered and "mcp" not in lowered and "工具" not in line:
                continue
            counts = [
                int(match.group(1))
                for pattern in CLAIM_PATTERNS
                for match in pattern.finditer(line)
            ]
            if not counts:
                continue
            marker_text = lowered
            for false_positive in MARKER_FALSE_POSITIVES:
                marker_text = marker_text.replace(false_positive, " ")
            marked_historical = any(
                marker in marker_text for marker in HISTORICAL_MARKERS
            )
            for count in counts:
                if count == expected or marked_historical:
                    continue
                problems.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    f"claims {count} tools, live registry has {expected}"
                )
    assert not problems, (
        "tool-count claims drifted from the live registry — update the count "
        "or mark the line as historical (was/had/before/landed/當時/...): "
        + "; ".join(problems)
    )
