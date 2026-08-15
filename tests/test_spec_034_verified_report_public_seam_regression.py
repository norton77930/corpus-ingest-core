"""Non-final reuse of Spec034's sealed C6 public workflow scenario."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.product_regression_only
def test_spec034_product_regression_only_preserves_verified_report_safety(monkeypatch, tmp_path: Path):
    from tests.spec034_final_c6_support import run_c6_public_workflow

    run_c6_public_workflow(monkeypatch, tmp_path)
