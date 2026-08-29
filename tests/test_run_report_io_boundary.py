"""Boundary guard: run-report staging is single-sourced in run_report_io.py.

specs/025-core-consolidation FR-004 / FR-010: every ``_write_run_report`` in
``src`` must delegate to a sanctioned writer — the shared weak protocol
(``write_part_staged_report_pair`` / ``write_part_staged_markdown``) or the
strong protocol (``write_atomic_audit_report_pair``) — and must not inline
``.part`` staging in its own body. ``.part`` staging elsewhere in ``src``
(audio downloads, transcript writes, bundle staging) is a different concern
and deliberately not covered here.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "corpus_ingest_core"

SANCTIONED_WRITER_CALLS = (
    "write_part_staged_report_pair(",
    "write_atomic_audit_report_pair(",
    "write_part_staged_markdown(",
)

EXPECTED_WRITER_MODULES = {
    "corpus_audio_download_runner.py",
    "corpus_episode_completion_workflow_runner.py",
    "corpus_episode_intake.py",
    "corpus_episode_workflow_runner.py",
    "corpus_latest_episode_deterministic_workflow_runner.py",
    "corpus_local_transcription_runner.py",
    "corpus_remediation_runner.py",
    "corpus_semantic_remediation_runner.py",
    "study_guide_bundle.py",
    "workflow_derivation.py",
    "x_video_ingest.py",
    "youtube_video_ingest.py",
}


def test_write_run_report_bodies_delegate_to_sanctioned_writers():
    writer_modules = set()
    for path in sorted(SRC_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "def _write_run_report" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_write_run_report":
                segment = ast.get_source_segment(text, node) or ""
                assert any(call in segment for call in SANCTIONED_WRITER_CALLS), (
                    f"{path.name}: _write_run_report must delegate to a "
                    "sanctioned writer from run_report_io or audit_report_pair"
                )
                assert ".part" not in segment, (
                    f"{path.name}: _write_run_report must not inline .part "
                    "staging; use run_report_io"
                )
                writer_modules.add(path.name)
    assert writer_modules == EXPECTED_WRITER_MODULES, (
        f"run-report writer module set changed — update deliberately: "
        f"{sorted(writer_modules)}"
    )
