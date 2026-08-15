from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core.hermes_integration import (
    HermesIntegrationError,
    HermesIntegrationRequest,
    MANAGED_EXTERNAL_SKILLS_DIR,
    MANAGED_MCP_URL,
    apply_integration,
    plan_integration,
    rollback_integration,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="規劃、套用或回復 Hermes podcast MCP 與受管 Skills。"
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    plan_parser = subparsers.add_parser("plan", help="驗證並輸出零寫入 redacted 計畫。")
    _add_apply_arguments(plan_parser)

    apply_parser = subparsers.add_parser("apply", help="備份後原子套用設定與 Skills。")
    _add_apply_arguments(apply_parser)

    rollback_parser = subparsers.add_parser("rollback", help="依 manifest 回復同次變更。")
    rollback_parser.add_argument("--manifest", type=Path, required=True)
    rollback_parser.add_argument("--config-path", type=Path, required=True)
    rollback_parser.add_argument("--skills-target", type=Path, required=True)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    try:
        if args.action == "rollback":
            result = rollback_integration(
                args.manifest,
                expected_config_path=args.config_path,
                expected_skills_target=args.skills_target,
            )
        else:
            request = HermesIntegrationRequest(
                config_path=args.config_path,
                mcp_url=args.mcp_url,
                skills_source=args.skills_source,
                skills_target=args.skills_target,
                local_skills_root=args.local_skills_root,
                backup_root=args.backup_root,
                external_skills_dir=args.external_skills_dir,
            )
            result = (
                plan_integration(request)
                if args.action == "plan"
                else apply_integration(request)
            )
    except HermesIntegrationError as exc:
        print(
            json.dumps(
                {"ok": False, "error_code": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(2) from None

    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))


def _add_apply_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config-path", type=Path, required=True)
    parser.add_argument("--skills-source", type=Path, required=True)
    parser.add_argument("--skills-target", type=Path, required=True)
    parser.add_argument("--local-skills-root", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--mcp-url", default=MANAGED_MCP_URL)
    parser.add_argument("--external-skills-dir", default=MANAGED_EXTERNAL_SKILLS_DIR)


if __name__ == "__main__":
    main()
