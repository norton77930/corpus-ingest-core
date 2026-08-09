"""Shared test fixtures for podcast-ingest-core.

Consolidation contract (specs/025-core-consolidation FR-008): tests that need
isolated artifact roots use the opt-in ``tmp_data_dirs`` fixture (or the plain
``use_tmp_data_dirs`` helper when a non-fixture call site needs it) instead of
re-declaring the historical per-file ``_use_tmp_data_dirs`` copies. Coverage of
``storage`` directory constants is reflective so future ``*_DIR`` additions are
patched automatically; the evals reports-dir bypass bindings are enumerated
explicitly so a rename fails loudly here, in one place.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

EVALS_REPORTS_DIR_BINDINGS = (
    ("podcast_ingest_core.corpus_index", "SEMANTIC_REVIEW_REPORTS_DIR"),
    ("podcast_ingest_core.research_llm_smoke_review", "REPORTS_DIR"),
    ("podcast_ingest_core.semantic_summary_smoke_review", "REPORTS_DIR"),
    ("podcast_ingest_core.stock_lens_synthesis", "SEMANTIC_REVIEW_REPORTS_DIR"),
)


def storage_dir_constant_names() -> list[str]:
    from podcast_ingest_core import storage

    return sorted(
        name
        for name, value in vars(storage).items()
        if name.isupper() and name.endswith("_DIR") and isinstance(value, Path)
    )


def use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> Path:
    """Redirect every artifact root to ``tmp_path``; returns the review dir."""
    from podcast_ingest_core import storage

    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    for name in storage_dir_constant_names():
        if name == "DATA_DIR":
            monkeypatch.setattr(storage, name, tmp_path)
            continue
        if name == "EVALS_RESEARCH_SMOKE_REPORTS_DIR":
            monkeypatch.setattr(storage, name, review_dir)
            continue
        leaf = getattr(storage, name).name
        monkeypatch.setattr(storage, name, tmp_path / leaf)
    for module_name, attribute in EVALS_REPORTS_DIR_BINDINGS:
        module = importlib.import_module(module_name)
        monkeypatch.setattr(module, attribute, review_dir)
    return review_dir


@pytest.fixture
def tmp_data_dirs(monkeypatch, tmp_path: Path) -> Path:
    """Opt-in fixture: isolated data/evals roots under ``tmp_path``."""
    use_tmp_data_dirs(monkeypatch, tmp_path)
    return tmp_path
