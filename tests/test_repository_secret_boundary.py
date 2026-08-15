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

# Specs 033/034 pin an exact third-party bundle (NousResearch/hermes-agent at a
# fixed commit) so an offline audit can hash it. Those files are not ours to
# edit — their bytes are recorded in the spec contracts and any change breaks
# the audit — and the value-shaped hits inside them are the upstream CLI's own
# documentation strings: "sk-..." placeholder examples and setup prompts that
# illustrate a private LAN address. They are not credentials and not our
# endpoints. The bundle stays inside the scan surface; only the two value-shape
# guards below tolerate it, only under these exact prefixes, and
# ``test_pinned_upstream_exemption_stays_third_party_and_digest_pinned`` keeps
# the exemption from widening into a hole.
PINNED_UPSTREAM_PREFIXES = (
    "specs/033-hermes-v019-pinned-source-loader-audit/upstream/",
    "specs/034-hermes-v019-pinned-startup-source-graph/upstream/",
)


def _is_pinned_upstream(path: Path) -> bool:
    return path.relative_to(ROOT).as_posix().startswith(PINNED_UPSTREAM_PREFIXES)


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
        if _is_pinned_upstream(path):
            continue
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
        if _is_pinned_upstream(path):
            continue
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


def test_pinned_upstream_exemption_stays_third_party_and_digest_pinned():
    """The exemption may only cover bundles whose bytes a spec contract pins.

    Without this, ``PINNED_UPSTREAM_PREFIXES`` would be a free-form allowlist:
    anyone could park a first-party file under an ``upstream/`` directory and
    have it skip both value-shape guards. Binding every exempted file to a
    digest recorded in its own spec ``source-bundle-manifest.json`` keeps the
    exemption exactly as wide as the audited third-party bundle, and makes an
    edited or added file fail here instead of silently gaining an exemption.
    """

    import hashlib
    import json

    exempted = [path for path in _scannable_files() if _is_pinned_upstream(path)]
    assert exempted, "pinned upstream prefixes match nothing — drop the exemption"

    problems = []
    for path in exempted:
        relative = path.relative_to(ROOT).as_posix()
        prefix = next(
            candidate
            for candidate in PINNED_UPSTREAM_PREFIXES
            if relative.startswith(candidate)
        )
        spec_root = ROOT / prefix.split("/upstream/")[0]
        manifest_path = spec_root / "contracts" / "source-bundle-manifest.json"
        if not manifest_path.is_file():
            problems.append(f"{relative}: no source-bundle-manifest.json for its spec")
            continue
        records = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", [])
        pinned = {
            record["path"]: record["sha256"]
            for record in records
            if isinstance(record, dict) and "path" in record and "sha256" in record
        }
        bundle_root = ROOT / prefix
        bundle_relative = path.relative_to(
            bundle_root / next(entry.name for entry in bundle_root.iterdir())
        ).as_posix()
        expected = pinned.get(bundle_relative)
        if expected is None:
            problems.append(f"{relative}: not listed in its source-bundle manifest")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            problems.append(f"{relative}: bytes differ from the pinned digest")

    assert not problems, (
        "secret-guard exemption covers files the spec contracts do not pin "
        "byte-for-byte; pin them or remove them from the exemption: "
        + "; ".join(problems)
    )
