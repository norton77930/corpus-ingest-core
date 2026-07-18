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

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Directory names that are local-only, generated, or out of commit scope.
EXCLUDED_DIR_NAMES = {
    ".git",
    "data",
    ".tmp",
    ".pytest-tmp",
    ".pytest_cache",
    ".venv",
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
    for current_root, directories, filenames in os.walk(ROOT):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in EXCLUDED_DIR_NAMES
        )
        for filename in sorted(filenames):
            path = Path(current_root) / filename
            relative = path.relative_to(ROOT)
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
    return sorted(files)


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
    assert not any(name.startswith(".venv/") for name in files)
    assert not any(name.startswith("evals/research-llm-smoke/raw/") for name in files)


def test_scan_covers_016_core_cli_mcp_and_portable_skill_surface():
    files = {path.relative_to(ROOT).as_posix() for path in _scannable_files()}

    assert "src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py" in files
    assert "scripts/run_corpus_episode_completion_workflow.py" in files
    assert "src/podcast_ingest_core/mcp_server.py" in files
    assert ".agents/skills/corpus-episode-completion/SKILL.md" in files


def test_scan_covers_017_core_cli_mcp_and_portable_skill_surface():
    files = {path.relative_to(ROOT).as_posix() for path in _scannable_files()}

    assert "src/podcast_ingest_core/corpus_latest_episode_deterministic_workflow_runner.py" in files
    assert "scripts/run_corpus_latest_episode_deterministic_workflow.py" in files
    assert "src/podcast_ingest_core/mcp_server.py" in files
    assert ".agents/skills/corpus-latest-episode-processing/SKILL.md" in files


def test_scan_prunes_excluded_directories_before_descending(monkeypatch, tmp_path):
    guard = sys.modules[__name__]
    (tmp_path / ".git" / "objects").mkdir(parents=True)
    (tmp_path / ".git" / "objects" / "unscanned.txt").write_text(
        "must not be traversed",
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "included.py").write_text("pass", encoding="utf-8")
    monkeypatch.setattr(guard, "ROOT", tmp_path)

    visited = []
    original_walk = guard.os.walk

    def tracking_walk(*args, **kwargs):
        for current_root, directories, filenames in original_walk(*args, **kwargs):
            visited.append(Path(current_root))
            yield current_root, directories, filenames

    monkeypatch.setattr(guard.os, "walk", tracking_walk)

    files = _scannable_files()

    assert files == [tmp_path / "src" / "included.py"]
    assert tmp_path / ".git" not in visited


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
