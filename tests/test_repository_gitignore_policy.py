"""Gitignore / local-only file protection guards (Batch 2, B2-T2).

Invariants protected:
- Local-only files (.env, .env.*, local LLM profiles), raw LLM debug output,
  pytest/local temp directories, and generated data artifacts must never
  become committable.
- ``.env.example`` stays a committed, sanitized placeholder template.

The checks use ``git check-ignore`` (pattern matching only; it never reads
file contents, so ``.env`` is not opened). When git is unavailable or the
repo is not a work tree, the tests skip instead of failing on an unrelated
environment problem.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _git_work_tree_available() -> bool:
    if shutil.which("git") is None:
        return False
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


requires_git = pytest.mark.skipif(
    not _git_work_tree_available(),
    reason="git is unavailable or the repo is not a git work tree",
)


def _is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", path],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if result.returncode not in (0, 1):
        pytest.fail(f"git check-ignore failed for {path}: {result.stderr!r}")
    return result.returncode == 0


def _ignore_pattern_source(path: str) -> str | None:
    result = subprocess.run(
        ["git", "check-ignore", "-v", "--no-index", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode not in (0, 1):
        pytest.fail(f"git check-ignore failed for {path}: {result.stderr!r}")
    if result.returncode == 1:
        return None
    return result.stdout.partition(":")[0].replace("\\", "/")


def _is_tracked(path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if result.returncode not in (0, 1):
        pytest.fail(f"git ls-files failed for {path}: {result.stderr!r}")
    return result.returncode == 0


IGNORED_LOCAL_ONLY_PATHS = [
    # local secrets
    ".env",
    ".env.local",
    ".env.backup",
    # local Spec Kit active-feature selection
    ".specify/feature.json",
    # local-only LLM provider profiles (endpoints must not be committed)
    "config/llm_profiles.local.yaml",
    "config/anything.local.yaml",
    # raw LLM debug output
    "evals/research-llm-smoke/raw/output.llm-output.md",
    # pytest / local temp
    ".pytest-tmp/run/probe.txt",
    ".tmp/probe.txt",
    ".pytest_cache/v/cache/nodeids",
    ".venv/Lib/site-packages/example.py",
    # generated data artifacts (SQLite cache is derived data; research
    # artifacts embed transcript-derived text and stay local)
    "data/audio/gooaye/EP1.mp3",
    "data/transcripts/gooaye/EP1.txt",
    "data/summaries/gooaye/EP1.md",
    "data/mentions/gooaye/EP1.mentions.json",
    "data/cache/podcast_ingest.sqlite3",
    "data/reports/gooaye/EP1.intelligence.json",
    "data/mappings/gooaye/EP1.industry-map.json",
    "data/external/gooaye/EP1.external-boundary.json",
    "data/stock-lens/gooaye/q.stock-lens.json",
    "data/notes/gooaye/EP1-analysis.md",
    "data/study-guides/x-raytar/ep/00_video_info.md",
    "data/research-reports/gooaye/EP1/manifest.json",
    # locally generated package metadata
    "src/corpus_ingest_core.egg-info/PKG-INFO",
]

COMMITTED_TEMPLATE_PATHS = [
    ".env.example",
    "config/llm_profiles.yaml",
    "README.md",
]


@requires_git
@pytest.mark.parametrize("path", IGNORED_LOCAL_ONLY_PATHS)
def test_local_only_path_is_ignored(path):
    assert _is_ignored(path), f"{path} must be gitignored (local-only or generated)"


@requires_git
def test_virtualenv_path_is_ignored_by_repository_policy():
    path = ".venv/Lib/site-packages/example.py"

    assert path in IGNORED_LOCAL_ONLY_PATHS
    assert _ignore_pattern_source(path) == ".gitignore"


@requires_git
def test_specify_feature_selection_file_is_untracked():
    assert not _is_tracked(".specify/feature.json")


@requires_git
@pytest.mark.parametrize("path", COMMITTED_TEMPLATE_PATHS)
def test_committed_template_is_not_ignored(path):
    assert not _is_ignored(path), f"{path} must stay committable"
