"""Pure byte-trust helpers for Spec034's externally reviewed launcher.

This module is deliberately a testable description of the inline launcher.  It
never resolves an executable pathname after byte verification and never starts
Spec034's bootstrap or final verifier.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
from typing import Any


def _is_reparse_point(info: os.stat_result) -> bool:
    return bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def regular_file_under(path: Path, trusted_root: Path) -> bool:
    """Require a regular leaf and regular non-reparse ancestors under root."""
    try:
        root = trusted_root.absolute()
        candidate = path.absolute()
        relative = candidate.relative_to(root)
        current = root
        info = current.lstat()
        if not stat.S_ISDIR(info.st_mode) or current.is_symlink() or _is_reparse_point(info):
            return False
        for part in relative.parts:
            current /= part
            info = current.lstat()
            expected_directory = current != candidate
            if (expected_directory and not stat.S_ISDIR(info.st_mode)) or (
                not expected_directory and not stat.S_ISREG(info.st_mode)
            ):
                return False
            if current.is_symlink() or _is_reparse_point(info):
                return False
        return True
    except (OSError, ValueError):
        return False


def read_verified_regular_bytes(
    path: Path, trusted_root: Path, expected_sha256: str, expected_length: int
) -> bytes | None:
    """Read once and return only exact trusted bytes with stable identity."""
    if (
        not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(char not in "0123456789abcdef" for char in expected_sha256)
        or not isinstance(expected_length, int)
        or expected_length < 0
    ):
        return None
    try:
        if not regular_file_under(path, trusted_root):
            return None
        before = path.lstat()
        data = path.read_bytes()
        after = path.lstat()
        stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if not stable or not regular_file_under(path, trusted_root):
            return None
        if len(data) != expected_length or hashlib.sha256(data).hexdigest() != expected_sha256:
            return None
        return data
    except OSError:
        return None


def execute_verified_bytes(payload: bytes, approved_logical_filename: str) -> dict[str, Any]:
    """Compile already-verified bytes without a second filesystem lookup.

    The supplied namespace is intentionally minimal and suitable only for inert
    test payloads.  Production inline/bootstrap launchers use the same
    compile/exec operation with an explicitly controlled namespace.
    """
    if not isinstance(payload, bytes) or not isinstance(approved_logical_filename, str):
        raise ValueError("verified byte execution arguments are invalid")
    namespace: dict[str, Any] = {
        "__name__": "__spec034_inert_payload__",
        "__file__": approved_logical_filename,
        "__package__": None,
    }
    exec(compile(payload, approved_logical_filename, "exec"), namespace, namespace)
    return namespace
