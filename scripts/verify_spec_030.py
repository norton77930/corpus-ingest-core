"""Later-only final verifier for Spec030's offline static boundary.

Excluded by design: Docker/Hermes/network/inference/C6.  This script has no
runtime remediation mode and must not be used to authorize one.
"""
from __future__ import annotations

from pathlib import Path
import ast
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
APPROVED_PATHS = frozenset(
    {
        "README.md",
        "docs/roadmap.md",
        "specs/README.md",
        "scripts/verify_spec_030.py",
        "scripts/validate_hermes_g1r_offline_remediation.py",
        "src/podcast_ingest_core/hermes_runtime_controller_plan.py",
        "src/podcast_ingest_core/hermes_g1r_offline_remediation.py",
        "tests/test_spec_030_g1r_offline_remediation.py",
    }
)
APPROVED_PREFIXES = ("specs/030-hermes-g1r-offline-remediation/",)
EXCLUDED_OPERATIONS = "Docker/Hermes/network/inference/C6"


def _safe_result(status: str, step: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "spec_id": "030-hermes-g1r-offline-remediation",
        "status": status,
        "runtime_status": "not_run",
        "g2_authorized": False,
        "g3a_authorized": False,
        "live_actions_authorized": False,
        "raw_persisted": False,
        "raw_persisted_scope": "safe_evidence_projection_only",
    }
    if step is not None:
        result["failed_step"] = step
    return result


def _run(command: tuple[str, ...], step: str) -> str | None:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return None if completed.returncode == 0 else step


def _approved_files() -> tuple[Path, ...]:
    files = [ROOT / path for path in APPROVED_PATHS]
    package = ROOT / APPROVED_PREFIXES[0]
    files.extend(path for path in package.rglob("*") if path.is_file())
    return tuple(files)


def _direct_whitespace_scan() -> bool:
    return all(
        all(not line.rstrip("\r\n").endswith((" ", "\t")) for line in path.read_text(encoding="utf-8").splitlines(True))
        for path in _approved_files()
    )


def _static_ast_guard() -> bool:
    """Reject imports and renderer/executor/live transition behavior, not enum text."""
    forbidden_imports = {"subprocess", "socket", "http", "urllib", "requests", "docker"}
    forbidden_names = ("render", "execut", "listen", "connect", "infer", "live_transition", "activate")
    for name in ("hermes_runtime_controller_plan.py", "hermes_g1r_offline_remediation.py"):
        tree = ast.parse((ROOT / "src/podcast_ingest_core" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports = [item.name.split(".")[0] for item in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
                if any(item in forbidden_imports for item in imports): return False
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and any(term in node.name.lower() for term in forbidden_names):
                return False
    return True


def main(argv=None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args:
        print(json.dumps(_safe_result("rejected"), sort_keys=True))
        return 2
    # Only approved tracked paths are passed to git diff --check --; unrelated dirty files never gate Spec030.
    if _run(("git", "diff", "--check", "--", *sorted(APPROVED_PATHS)), "approved_path_diff_check") is not None:
        print(json.dumps(_safe_result("failed", "approved_path_diff_check"), sort_keys=True))
        return 1
    if not _direct_whitespace_scan():
        print(json.dumps(_safe_result("failed", "approved_untracked_whitespace_scan"), sort_keys=True))
        return 1
    if not _static_ast_guard():
        print(json.dumps(_safe_result("failed", "core_static_ast_guard"), sort_keys=True))
        return 1
    checks = (
        (
            "focused_and_predecessor_tests",
            (
                sys.executable,
                "-m",
                "pytest",
                "tests/test_spec_030_g1r_offline_remediation.py",
                "tests/test_spec_029_offline.py",
                "-q",
            ),
        ),
        (
            "compile",
            (
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "src/podcast_ingest_core/hermes_runtime_controller_plan.py",
                "src/podcast_ingest_core/hermes_g1r_offline_remediation.py",
                "scripts/validate_hermes_g1r_offline_remediation.py",
                "scripts/verify_spec_030.py",
            ),
        ),
        (
            "core_static_guard",
            (
                sys.executable,
                "-c",
                "from pathlib import Path; root=Path('src/podcast_ingest_core'); files=('hermes_runtime_controller_plan.py','hermes_g1r_offline_remediation.py'); banned=('import subprocess','import socket','import urllib','import requests','import docker'); assert all(all(term not in (root / name).read_text(encoding='utf-8').lower() for term in banned) for name in files)",
            ),
        ),
    )
    for step, command in checks:
        failed = _run(command, step)
        if failed is not None:
            print(json.dumps(_safe_result("failed", failed), sort_keys=True))
            return 1
    print(json.dumps(_safe_result("passed"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
