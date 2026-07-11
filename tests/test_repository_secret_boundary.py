"""Repo-wide secret / private endpoint boundary guards (Batch 2, B2-T1).

Invariants protected:
- Committable repo files must not contain real-looking API key values
  (``sk-...`` style), except an explicit allowlist of fake values that
  redaction / leak-detection tests use on purpose.
- Committable repo files must not contain private/internal network endpoints
  (10.x.x.x, 192.168.x.x, 172.16-31.x.x URLs).

The scan walks the repository with pathlib so it does not depend on rg/git
being on PATH. It never opens ``.env`` (local-only secret file) and skips
local-only or generated locations that mirror the .gitignore policy.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Directory names that are local-only, generated, or out of commit scope.
EXCLUDED_DIR_NAMES = {
    ".git",
    "data",
    ".tmp",
    ".pytest-tmp",
    ".pytest_cache",
    "__pycache__",
    ".claude",
    ".codex",
}
# Relative path prefixes (posix style) that are local-only per .gitignore.
EXCLUDED_PREFIXES = ("evals/research-llm-smoke/raw/",)
EXCLUDED_RELATIVE_PATHS = {".specify/feature.json"}
BINARY_SUFFIXES = {".mp3", ".wav", ".sqlite3", ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".zip"}

SECRET_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
# Exact fake values intentionally used by redaction / leak-detection tests.
# Keep this list tight: exact-match only, no prefixes, no broad allow.
ALLOWED_FAKE_SECRETS = {
    "sk-test-secret",
    "sk-test-secret-value",
}
PRIVATE_ENDPOINT_PATTERN = re.compile(
    r"https?://(?:10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)"
)


def _scannable_files() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIR_NAMES for part in relative.parts):
            continue
        posix = relative.as_posix()
        if posix in EXCLUDED_RELATIVE_PATHS:
            continue
        if posix.startswith(EXCLUDED_PREFIXES):
            continue
        # Never read the local-only .env file (or any .env.* variant except
        # the committed sanitized template .env.example).
        if relative.name.startswith(".env") and relative.name != ".env.example":
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        files.append(path)
    return files


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def test_scan_covers_expected_repo_surface():
    files = {path.relative_to(ROOT).as_posix() for path in _scannable_files()}

    # The scan must include the committed template and core source files...
    assert ".env.example" in files
    assert "config/llm_profiles.yaml" in files
    assert "src/podcast_ingest_core/llm_provider.py" in files
    # ...and must never include the local-only .env or data artifacts.
    assert ".env" not in files
    assert not any(name.startswith("data/") for name in files)
    assert ".specify/feature.json" not in files
    assert not any(name.startswith("evals/research-llm-smoke/raw/") for name in files)


def test_no_secret_like_api_key_in_committable_files():
    violations = []
    for path in _scannable_files():
        text = _read_text(path)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in SECRET_KEY_PATTERN.finditer(line):
                if match.group(0) in ALLOWED_FAKE_SECRETS:
                    continue
                # Truncate the match so this guard never reprints a full key.
                violations.append(
                    f"{path.relative_to(ROOT).as_posix()}:{line_number}: {match.group(0)[:8]}..."
                )
    assert not violations, (
        "secret-like API key values found in committable files "
        f"(rotate the key and replace with placeholders): {violations}"
    )


def test_no_private_internal_endpoint_in_committable_files():
    violations = []
    for path in _scannable_files():
        text = _read_text(path)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PRIVATE_ENDPOINT_PATTERN.search(line):
                violations.append(
                    f"{path.relative_to(ROOT).as_posix()}:{line_number}: {line.strip()[:80]}"
                )
    assert not violations, (
        "private/internal network endpoints found in committable files "
        f"(use placeholders such as https://api.example.com/v1): {violations}"
    )
