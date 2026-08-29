"""Regression guard for the verified-report public workflow seam."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.product_regression_only
def test_product_regression_preserves_verified_report_safety(monkeypatch, tmp_path: Path):
    from tests.verified_report_public_seam_support import run_verified_report_public_workflow

    run_verified_report_public_workflow(monkeypatch, tmp_path)
