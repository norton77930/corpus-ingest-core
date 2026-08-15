"""Spec034's verified-byte final-verifier bootstrap.

The reviewed inline launcher reads and validates this bootstrap once, then
compiles those exact bytes.  This module in turn reads and validates final
verifier bytes once and supplies those bytes to an isolated child over stdin.
No trusted program is executed by a post-validation pathname lookup.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/034-hermes-v019-pinned-startup-source-graph"
FINAL_VERIFIER_PATH = ROOT / "scripts/verify_spec_034_offline.py"
REVIEW_ROOT_PATH = SPEC / "contracts/review-root.json"
REVIEWED_MANIFEST_PATH = SPEC / "contracts/reviewed-artifact-manifest.json"
ROOT_SCHEMA = "spec034-detached-review-root-v8"
# H4 reviewers approve these independent final-verifier bytes.  Task #79
# additionally requires the reviewer-rooted capability-manifest identity.
# No value is derived from mutable authority bytes at execution time.
EXPECTED_FINAL_VERIFIER_SHA256 = "0565ea4556933e2843af1b61cf4d5b853c3d91fc9e06269090aa7b9ddaa3bb89"
EXPECTED_FINAL_VERIFIER_LENGTH = 32890
EXPECTED_ISOLATED_PYTEST_RUNNER_SHA256 = "944dd42b79f53ed8490a69dd2823105675d7efd359e4ddff3cbf603d239aa248"
EXPECTED_ISOLATED_PYTEST_RUNNER_LENGTH = 21408
EXPECTED_CAPABILITY_MANIFEST_SHA256 = "5185a9b618dabdbd9bf815a344037b988d8290aef81666a536c838123bbb3173"
EXPECTED_CAPABILITY_DISTRIBUTIONS = ("pytest", "pluggy", "iniconfig", "packaging", "pygments", "colorama", "requests", "urllib3", "certifi", "charset-normalizer", "idna", "pyyaml")


def _is_reparse_point(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _regular_under(path: Path, trusted_root: Path) -> bool:
    try:
        root = trusted_root.absolute()
        candidate = path.absolute()
        relative = candidate.relative_to(root)
        current = root
        root_info = current.lstat()
        if not stat.S_ISDIR(root_info.st_mode) or current.is_symlink() or _is_reparse_point(root_info):
            return False
        for part in relative.parts:
            current /= part
            info = current.lstat()
            if current == candidate:
                if not stat.S_ISREG(info.st_mode):
                    return False
            elif not stat.S_ISDIR(info.st_mode):
                return False
            if current.is_symlink() or _is_reparse_point(info):
                return False
        return True
    except (OSError, ValueError):
        return False


def _read_verified(path: Path, digest: str, length: int) -> bytes | None:
    if not _valid_sha256(digest) or not isinstance(length, int) or length < 0:
        return None
    try:
        if not _regular_under(path, ROOT):
            return None
        before = path.lstat()
        data = path.read_bytes()
        after = path.lstat()
        if not _regular_under(path, ROOT):
            return None
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            return None
        if len(data) != length or hashlib.sha256(data).hexdigest() != digest:
            return None
        return data
    except OSError:
        return None


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _read(path: Path) -> bytes | None:
    """Canonical guarded read for root/manifest authority bytes."""
    try:
        if not _regular_under(path, ROOT):
            return None
        before = path.lstat()
        data = path.read_bytes()
        after = path.lstat()
        stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        )
        return data if stable and _regular_under(path, ROOT) else None
    except OSError:
        return None


def _preflight_bytes(review_root_sha256: str) -> tuple[bytes, bytes] | None:
    """Return the final bytes/root bytes only after exact pre-execution checks."""
    if not _valid_sha256(review_root_sha256):
        return None
    final_bytes = _read_verified(
        FINAL_VERIFIER_PATH,
        EXPECTED_FINAL_VERIFIER_SHA256,
        EXPECTED_FINAL_VERIFIER_LENGTH,
    )
    root_bytes = _read(REVIEW_ROOT_PATH)
    manifest_bytes = _read(REVIEWED_MANIFEST_PATH)
    capability_bytes = _read(SPEC / "contracts/python-test-capability-manifest.json")
    if final_bytes is None or root_bytes is None or manifest_bytes is None or capability_bytes is None:
        return None
    if hashlib.sha256(capability_bytes).hexdigest() != EXPECTED_CAPABILITY_MANIFEST_SHA256:
        return None
    try:
        capability = json.loads(capability_bytes.decode("utf-8"))
        distributions = tuple(item["canonical_name"] for item in capability["distributions"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        return None
    if capability.get("schema_version") != "spec034-python-test-capability-manifest-v1" or distributions != EXPECTED_CAPABILITY_DISTRIBUTIONS:
        return None
    if hashlib.sha256(root_bytes).hexdigest() != review_root_sha256:
        return None
    try:
        root = json.loads(root_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(root, dict):
        return None
    expected = {
        "schema_version": ROOT_SCHEMA,
        "reviewed_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "launcher_contract_sha256": root.get("launcher_contract_sha256"),
        "capability_manifest_sha256": EXPECTED_CAPABILITY_MANIFEST_SHA256,
        "capability_distributions": list(EXPECTED_CAPABILITY_DISTRIBUTIONS),
        "bootstrap": root.get("bootstrap"),
        "final_verifier": {
            "sha256": EXPECTED_FINAL_VERIFIER_SHA256,
            "byte_length": EXPECTED_FINAL_VERIFIER_LENGTH,
        },
        "isolated_pytest_runner": {
            "sha256": EXPECTED_ISOLATED_PYTEST_RUNNER_SHA256,
            "byte_length": EXPECTED_ISOLATED_PYTEST_RUNNER_LENGTH,
        },
    }
    if root != expected:
        return None
    return final_bytes, root_bytes


def _preflight(review_root_sha256: str) -> bool:
    """Boolean compatibility seam; does not execute an entrypoint."""
    return _preflight_bytes(review_root_sha256) is not None


_CHILD_EXECUTE_VERIFIED_STDIN = """
import os, sys
if os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('PYTHONOPTIMIZE is forbidden for Spec034 final verification')
review_root = sys.argv[2]
verified_bytes = sys.stdin.buffer.read()
globals_dict = {
    '__name__': '__main__',
    '__file__': os.path.join(os.getcwd(), 'scripts', 'verify_spec_034_offline.py'),
    '__package__': None,
    '__builtins__': __builtins__,
}
sys.argv = ['verify_spec_034_offline.py', '--review-root-sha256', review_root]
exec(compile(verified_bytes, 'spec034-approved/verify_spec_034_offline.py', 'exec'), globals_dict, globals_dict)
"""


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "--review-root-sha256":
        return 1
    checked = _preflight_bytes(args[1])
    if checked is None:
        return 1
    final_bytes, _root_bytes = checked
    command = (
        sys.executable,
        "-I",
        "-S",
        "-c",
        _CHILD_EXECUTE_VERIFIED_STDIN,
        "--review-root-sha256",
        args[1],
    )
    completed = subprocess.run(command, cwd=ROOT, input=final_bytes, check=False)
    return 0 if completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
