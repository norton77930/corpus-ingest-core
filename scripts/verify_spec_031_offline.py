"""Later-only static verifier for Spec031 offline evidence.

Excluded by design: Docker, Hermes runtime actions, network, inference, C6, and
all credential/config/session/log access. This verifier never imports or calls
the future one-shot executor.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "podcast_ingest_core"
APPROVED_PATHS = frozenset(
    {
        "README.md",
        "docs/roadmap.md",
        "specs/README.md",
        "scripts/validate_hermes_g2_activation.py",
        "scripts/verify_spec_031_offline.py",
        "scripts/run_spec_031_g2_once.py",
        "src/podcast_ingest_core/hermes_g2_activation_observation.py",
        "src/podcast_ingest_core/hermes_g2_activation_runtime.py",
        "tests/test_hermes_g2_activation_observation.py",
        "tests/test_hermes_g2_activation_runtime.py",
        "tests/test_spec_031_hermes_g2_docs.py",
    }
)
APPROVED_PREFIXES = (
    "specs/031-hermes-g2-credentialless-activation-gate/",
    "deploy/hermes/spec031/",
)
OFFLINE_PYTEST_TARGETS = (
    "tests/test_hermes_g2_activation_observation.py",
    "tests/test_spec_031_hermes_g2_docs.py",
    "tests/test_spec_030_g1r_offline_remediation.py",
    "tests/test_spec_029_offline.py",
)


def _safe_result(status: str, step: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "spec_id": "031-hermes-g2-credentialless-activation-gate",
        "status": status,
        "runtime_status": "not_run",
        "live_actions_authorized": False,
        "raw_persisted": False,
    }
    if step is not None:
        result["failed_step"] = step
    return result


def _run(command: tuple[str, ...], step: str) -> str | None:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return None if completed.returncode == 0 else step


def _approved_files() -> tuple[Path, ...]:
    files = [ROOT / relative for relative in APPROVED_PATHS]
    for prefix in APPROVED_PREFIXES:
        files.extend(path for path in (ROOT / prefix).rglob("*") if path.is_file())
    return tuple(files)


def _direct_whitespace_scan() -> bool:
    return all(
        all(
            not line.rstrip("\r\n").endswith((" ", "\t"))
            for line in path.read_text(encoding="utf-8").splitlines(True)
        )
        for path in _approved_files()
    )


def _static_ast_guard() -> bool:
    forbidden_imports = {"socket", "http", "urllib", "requests", "docker"}
    forbidden_names = ("exec", "cp", "retry", "restart", "logs")
    sources = (
        PACKAGE / "hermes_g2_activation_observation.py",
        PACKAGE / ("hermes_g2_activation_" + "runtime.py"),
        ROOT / "scripts" / "validate_hermes_g2_activation.py",
        ROOT / "scripts" / "run_spec_031_g2_once.py",
        ROOT / "deploy" / "hermes" / "spec031" / "probe_contract.py",
    )
    for source in sources:
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports = (
                    [item.name.split(".")[0] for item in node.names]
                    if isinstance(node, ast.Import)
                    else [(node.module or "").split(".")[0]]
                )
                if any(item in forbidden_imports for item in imports):
                    return False
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if any(term in node.name.lower() for term in forbidden_names):
                    return False
    return True


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args:
        print(json.dumps(_safe_result("rejected"), sort_keys=True))
        return 2
    # Run git diff --check -- only for approved tracked paths.
    if _run(("git", "diff", "--check", "--", *sorted(APPROVED_PATHS)), "approved_path_diff_check") is not None:
        print(json.dumps(_safe_result("failed", "approved_path_diff_check"), sort_keys=True))
        return 1
    if not _direct_whitespace_scan():
        print(json.dumps(_safe_result("failed", "approved_untracked_whitespace_scan"), sort_keys=True))
        return 1
    if not _static_ast_guard():
        print(json.dumps(_safe_result("failed", "static_ast_guard"), sort_keys=True))
        return 1
    checks = (
        (
            "focused_and_predecessor_tests",
            (
                sys.executable,
                "-m",
                "pytest",
                *OFFLINE_PYTEST_TARGETS,
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
                "src/podcast_ingest_core/hermes_g2_activation_observation.py",
                "src/podcast_ingest_core/hermes_g2_activation_runtime.py",
                "scripts/validate_hermes_g2_activation.py",
                "scripts/verify_spec_031_offline.py",
                "scripts/run_spec_031_g2_once.py",
                "deploy/hermes/spec031/probe_contract.py",
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
