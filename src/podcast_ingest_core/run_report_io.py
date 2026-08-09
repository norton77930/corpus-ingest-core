"""Single source for the historical ``.part``-staged run-report write protocol.

specs/025-core-consolidation FR-004: four runner modules carried byte-identical
copies of the JSON+Markdown staging body, and episode intake a markdown-only
variant; both are reproduced here byte-equivalently. The stronger protocol in
``audit_report_pair`` (which changes artifact bytes) deliberately stays
separate — upgrading weak callers is out of 025 scope. Callers keep their own
``except OSError`` mapping to module-specific error types and message formats;
only the staging mechanics are shared.
"""

from __future__ import annotations

import json
from pathlib import Path


def write_part_staged_report_pair(
    json_path: Path,
    markdown_path: Path,
    payload: dict,
    markdown: str,
) -> None:
    """Historical weak protocol: ``.part`` staging, replace, best-effort cleanup.

    Re-raises the raw ``OSError`` after cleanup; callers map it to their module
    error type without changing message bytes.
    """
    json_part_path = json_path.with_name(f"{json_path.name}.part")
    markdown_part_path = markdown_path.with_name(f"{markdown_path.name}.part")
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_part_path.unlink(missing_ok=True)
        markdown_part_path.unlink(missing_ok=True)
        json_part_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_part_path.write_text(markdown, encoding="utf-8")
        json_part_path.replace(json_path)
        markdown_part_path.replace(markdown_path)
    except OSError:
        for part_path in (json_part_path, markdown_part_path):
            try:
                part_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def write_part_staged_markdown(markdown_path: Path, markdown: str) -> None:
    """Episode-intake variant: markdown-only staging with finally-cleanup."""
    markdown_part = markdown_path.with_name(f"{markdown_path.name}.part")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_part.unlink(missing_ok=True)
    try:
        markdown_part.write_text(markdown, encoding="utf-8")
        markdown_part.replace(markdown_path)
    finally:
        markdown_part.unlink(missing_ok=True)
