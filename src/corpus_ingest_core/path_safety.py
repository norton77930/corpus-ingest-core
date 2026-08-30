"""Single structural source for local-path safety predicates.

specs/025-core-consolidation FR-003: the corpus runner modules keep their own
``_is_safe_local_path`` wrappers — their accepted sets are per-module spec'd
contracts locked by ``tests/test_path_safety_characterization.py`` — while this
module owns the shared structural skeleton and regex constants so the
structure can no longer drift silently between entry points.

Profiles (empirically pinned 2026-08-08):

- ``allow_absolute=True, require_separator=True`` — the 010/015/016-family
  profile: POSIX-absolute and drive-letter paths accepted, a path separator is
  mandatory, ``:`` rejected outside a drive prefix.
- ``allow_absolute=False, require_separator=False`` — the 017 profile: any
  leading separator and any ``:`` rejected, bare filenames accepted.

Callers layer their module-specific conjuncts (forbidden-fragment scans,
sanitizer round-trips) on top; those stay module-local by design.
"""

from __future__ import annotations

import re

URI_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
SAFE_FILENAME_PATTERN = re.compile(r"^[^<>:/\\|?*\x00-\x1f]+\.[A-Za-z0-9]{1,16}$")
# CJK Unified Ideographs (U+4E00-U+9FFF) are allowed to match storage.title_slug,
# which deliberately preserves them; ASCII-only would drop legal CJK artifact paths.
SAFE_PATH_COMPONENT_PATTERN = re.compile(r"^[A-Za-z0-9._一-鿿-]+$")

_DRIVE_PREFIX_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_SEPARATOR_SPLIT_PATTERN = re.compile(r"[\\/]")


def is_safe_local_path_structure(
    value: object,
    *,
    allow_absolute: bool,
    require_separator: bool = True,
) -> bool:
    if not isinstance(value, str):
        return False
    if not value or value != value.strip() or len(value) > 1024:
        return False
    if URI_SCHEME_PATTERN.match(value):
        return False
    if allow_absolute:
        if value.startswith(("\\\\", "//")):
            return False
    elif value.startswith(("/", "\\")):
        return False
    if "?" in value or "#" in value or "|" in value:
        return False
    if require_separator and "/" not in value and "\\" not in value:
        return False
    if any(character.isspace() for character in value):
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    if allow_absolute:
        path_without_drive = value[2:] if _DRIVE_PREFIX_PATTERN.match(value) else value
        if ":" in path_without_drive:
            return False
    elif ":" in value:
        return False
    parts = _SEPARATOR_SPLIT_PATTERN.split(value)
    if allow_absolute and (_DRIVE_PREFIX_PATTERN.match(value) or value.startswith("/")):
        path_parts = parts[1:]
    else:
        path_parts = parts
    if not path_parts or any(
        not part or part in {".", ".."} or not SAFE_PATH_COMPONENT_PATTERN.fullmatch(part) for part in path_parts
    ):
        return False
    return bool(SAFE_FILENAME_PATTERN.fullmatch(path_parts[-1]))
