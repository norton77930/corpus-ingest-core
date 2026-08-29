from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "evals" / "mcp-tool-use" / "phase-5c-codex-session-template.md"
REPORTS_DIR = PROJECT_ROOT / "evals" / "mcp-tool-use" / "reports"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a timestamped Phase 5C MCP tool-use eval report from the template."
    )
    parser.add_argument(
        "--name",
        default="codex-session",
        help="Short report name. Only letters, digits, '-' and '_' are kept; spaces become '-'.",
    )
    return parser.parse_args(argv)


def create_report(
    name: str = "codex-session",
    *,
    project_root: Path | None = None,
    template_path: Path | None = None,
    reports_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    project_root = project_root or PROJECT_ROOT
    template_path = template_path or TEMPLATE_PATH
    reports_dir = reports_dir or REPORTS_DIR
    timestamp = (now or _now()).strftime("%Y%m%d-%H%M%S")
    safe_name = _sanitize_report_name(name)
    reports_dir.mkdir(parents=True, exist_ok=True)

    content = template_path.read_text(encoding="utf-8")
    target_path = _next_available_path(reports_dir / f"{timestamp}-{safe_name}.md")
    target_path.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "report_path": _relative_report_path(target_path, project_root),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = create_report(args.name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _now() -> datetime:
    return datetime.now()


def _sanitize_report_name(name: str) -> str:
    normalized = re.sub(r"\s+", "-", name.strip())
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-_")
    return normalized or "codex-session"


def _next_available_path(path: Path) -> Path:
    if not path.exists():
        return path

    suffix_index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{suffix_index}{path.suffix}")
        if not candidate.exists():
            return candidate
        suffix_index += 1


def _relative_report_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
