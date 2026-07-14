"""Cache source-of-truth / no automatic cache rebuild guards (B2-T6).

Invariants protected:
- SQLite cache is derived data; rebuilding it stays an explicit, manual
  action (CLI ``rebuild_cache.py`` or the MCP ``rebuild_cache`` tool).
- Confirmed side-effect paths (research workflow, MCP side-effect tools)
  never call ``rebuild_cache`` implicitly; they only warn that the cache may
  be stale.
- No new core module starts referencing ``rebuild_cache`` without review.

No download/transcription/LLM call happens here: every step operation is
monkeypatched.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_research_workflow import _write_transcript


ROOT = Path(__file__).resolve().parents[1]


def _fail_rebuild(*args, **kwargs):
    pytest.fail("rebuild_cache must remain a manual, explicit action")


def test_confirmed_research_workflow_never_auto_rebuilds_cache(monkeypatch, tmp_path):
    from podcast_ingest_core import cache, research_workflow

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(cache, "rebuild_cache", _fail_rebuild)

    def _fake_step_asset(**paths):
        return SimpleNamespace(generated=True, already_exists=False, **paths)

    monkeypatch.setattr(
        research_workflow,
        "extract_mentions",
        lambda *args, **kwargs: _fake_step_asset(
            mentions_json_path=tmp_path / "m.mentions.json",
            mentions_markdown_path=tmp_path / "m.mentions.md",
        ),
    )
    monkeypatch.setattr(
        research_workflow,
        "generate_episode_intelligence_report",
        lambda *args, **kwargs: _fake_step_asset(
            report_json_path=tmp_path / "r.intelligence.json",
            report_markdown_path=tmp_path / "r.intelligence.md",
        ),
    )
    monkeypatch.setattr(
        research_workflow,
        "generate_industry_chain_mapping",
        lambda *args, **kwargs: _fake_step_asset(
            mapping_json_path=tmp_path / "i.industry-map.json",
            mapping_markdown_path=tmp_path / "i.industry-map.md",
        ),
    )
    monkeypatch.setattr(
        research_workflow,
        "generate_external_data_boundary",
        lambda *args, **kwargs: _fake_step_asset(
            boundary_json_path=tmp_path / "e.external-boundary.json",
            boundary_markdown_path=tmp_path / "e.external-boundary.md",
        ),
    )

    result = research_workflow.run_research_workflow("gooaye", "EP672", confirm=True)

    assert result.workflow_status == "completed"
    assert research_workflow.CACHE_STALE_WARNING in result.warnings


def test_mcp_confirmed_side_effect_tools_never_auto_rebuild_cache(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import MentionExtractionAsset, SummaryAsset

    monkeypatch.setattr(mcp_server.cache_module, "rebuild_cache", _fail_rebuild)

    monkeypatch.setattr(
        mcp_server.summarizer,
        "summarize_episode",
        lambda **kwargs: SummaryAsset(
            podcast_id=kwargs["podcast_id"],
            episode_ref=kwargs["episode_ref"],
            title="Summary",
            summary_path=Path("data/summaries/gooaye/EP672.md"),
            transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            transcript_text_path=Path("data/transcripts/gooaye/EP672.txt"),
            segment_count=1,
            summary_mode="extractive-template",
            generated=True,
        ),
    )
    summary_response = mcp_server.summarize_episode_extractive(
        podcast_id="gooaye", episode_ref="EP672", confirm=True
    )
    assert summary_response["ok"] is True
    assert any("Cache may be stale" in warning for warning in summary_response["warnings"])

    monkeypatch.setattr(
        mcp_server.entity_extractor,
        "extract_mentions",
        lambda **kwargs: MentionExtractionAsset(
            podcast_id=kwargs["podcast_id"],
            episode_ref=kwargs["episode_ref"],
            title="Mentions",
            source_transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            mentions_json_path=Path("data/mentions/gooaye/EP672.mentions.json"),
            mentions_markdown_path=Path("data/mentions/gooaye/EP672.mentions.md"),
            mention_count=1,
            segment_count=1,
            extraction_mode="deterministic-rules",
            generated=True,
            already_exists=False,
        ),
    )
    mentions_response = mcp_server.extract_mentions(
        podcast_id="gooaye", episode_ref="EP672", confirm=True
    )
    assert mentions_response["ok"] is True
    assert any("Cache may be stale" in warning for warning in mentions_response["warnings"])


def test_rebuild_cache_references_stay_in_reviewed_modules():
    # cache.py defines rebuild_cache; __init__.py re-exports it; mcp_server.py
    # exposes the explicit maintenance tool; research_workflow.py only mentions
    # it inside the CACHE_STALE_WARNING message string (the F-18 unused import
    # was removed in Batch 3B, so the module stays allowlisted for that literal,
    # not for any callable reference). Any other core module referencing
    # rebuild_cache is an unreviewed auto-rebuild risk.
    allowed = {"__init__.py", "cache.py", "mcp_server.py", "research_workflow.py"}
    src_dir = ROOT / "src" / "podcast_ingest_core"
    offenders = sorted(
        path.name
        for path in src_dir.glob("*.py")
        if "rebuild_cache" in path.read_text(encoding="utf-8") and path.name not in allowed
    )
    assert not offenders, (
        "unexpected rebuild_cache reference in core modules (auto-rebuild is "
        f"forbidden; see constitution principle VIII): {offenders}"
    )


def test_completion_workflow_has_no_automatic_cache_rebuild_path():
    completion_source = (
        ROOT
        / "src"
        / "podcast_ingest_core"
        / "corpus_episode_completion_workflow_runner.py"
    ).read_text(encoding="utf-8")

    assert "rebuild_cache" not in completion_source
