from __future__ import annotations

import json
import os
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(storage, "STOCK_LENS_DIR", tmp_path / "stock-lens", raising=False)


def _write_transcript(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    completed=True,
    write_text=True,
    write_srt=True,
    write_json=True,
    json_text=None,
):
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    segments = [
        {
            "id": 1,
            "start": 83.1,
            "end": 90.2,
            "text": "今天聊到台積電、半導體和 AI 需求。",
        },
        {
            "id": 2,
            "start": 305.0,
            "end": 312.0,
            "text": "利率和通膨對估值還是有影響。",
        },
    ]
    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    if write_text:
        paths.text_path.write_text("\n".join(segment["text"] for segment in segments), encoding="utf-8")
    if write_srt:
        paths.srt_path.write_text("1\n00:01:23,000 --> 00:01:30,000\n字幕\n", encoding="utf-8")
    if write_json:
        if json_text is not None:
            paths.json_path.write_text(json_text, encoding="utf-8")
        else:
            payload = {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "language": "zh",
                "segment_count": len(segments),
                "completed": completed,
                "generated_at": "2026-06-28T00:00:00Z",
                "source_audio_path": "data/audio/gooaye/EP672__EP672.mp3",
                "source_audio_size_bytes": 123,
                "segments": segments,
            }
            paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return paths


def _write_mapping_config(tmp_path):
    config_path = tmp_path / "industry_chain_mappings.yaml"
    config_path.write_text(
        """
version: 1
industry_nodes:
  semiconductor:
    label: 半導體
    aliases:
      - 半導體
    candidates:
      - company_name: 台積電
        tickers:
          - 2330.TW
          - TSM
        relation: foundry
      - company_name: NVIDIA
        tickers:
          - NVDA
        relation: accelerator_design
company_aliases:
  台積電:
    company_name: 台積電
    tickers:
      - 2330.TW
      - TSM
    industry_node_ids:
      - semiconductor
""".strip(),
        encoding="utf-8",
    )
    return config_path


def _write_boundary_config(tmp_path):
    config_path = tmp_path / "external_data_boundary.yaml"
    config_path.write_text(
        """
version: 1
required_external_checks:
  - data_type: company_identity
    label: Company identity and legal entity
    requires_source_status: true
    requires_data_date: true
""".strip(),
        encoding="utf-8",
    )
    return config_path


def _patch_configs(monkeypatch, tmp_path):
    import podcast_ingest_core.external_data_boundary as external_data_boundary
    import podcast_ingest_core.industry_mapping as industry_mapping

    monkeypatch.setattr(
        industry_mapping,
        "DEFAULT_MAPPING_CONFIG_PATH",
        _write_mapping_config(tmp_path),
    )
    monkeypatch.setattr(
        external_data_boundary,
        "DEFAULT_BOUNDARY_CONFIG_PATH",
        _write_boundary_config(tmp_path),
    )


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _semantic_asset(tmp_path):
    from podcast_ingest_core.models import SummaryAsset

    summary_path = tmp_path / "summaries" / "gooaye" / "EP672__EP672 title.semantic.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("# semantic", encoding="utf-8")
    return SummaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        summary_path=summary_path,
        transcript_json_path=tmp_path / "transcripts" / "gooaye" / "EP672__EP672 title.json",
        transcript_text_path=tmp_path / "transcripts" / "gooaye" / "EP672__EP672 title.txt",
        segment_count=2,
        summary_mode="semantic-llm",
        generated=True,
        already_exists=False,
        provider="openai-compatible",
        model="test-model",
        chunk_count=1,
        evidence_count=1,
    )


def _synthesis_asset(tmp_path, *, generated=True, already_exists=False):
    from podcast_ingest_core.models import StockLensSynthesisResult

    synthesis_dir = tmp_path / "stock-lens" / "gooaye"
    synthesis_dir.mkdir(parents=True, exist_ok=True)
    json_path = synthesis_dir / "台積電.stock-lens-synthesis.json"
    markdown_path = synthesis_dir / "台積電.stock-lens-synthesis.md"
    if generated or already_exists:
        json_path.write_text("{}", encoding="utf-8")
        markdown_path.write_text("# synthesis", encoding="utf-8")
    return StockLensSynthesisResult(
        podcast_id="gooaye",
        stock_query="台積電",
        synthesis_json_path=json_path,
        synthesis_markdown_path=markdown_path,
        source_stock_lens_json_path=synthesis_dir / "台積電.stock-lens.json",
        synthesis_status="final",
        source_report_status="final",
        dry_run=False,
        requires_confirmation=False,
        requires_api_cost_ack=False,
        required_acknowledgement=None,
        planned_reads=[str(synthesis_dir / "台積電.stock-lens.json")],
        planned_writes=[str(json_path), str(markdown_path)],
        risks=[],
        generated=generated,
        already_exists=already_exists,
        provider="openai-compatible",
        model="test-model",
        prompt_char_count=123,
        warning_count=0,
        not_investment_advice=True,
    )


def _verification_asset(tmp_path, *, generated=True, already_exists=False):
    from podcast_ingest_core.models import ExternalDataVerificationAsset
    from podcast_ingest_core.storage import find_external_data_boundary_asset_paths

    existing_paths = find_external_data_boundary_asset_paths("gooaye", "EP672")
    if existing_paths is not None:
        json_path = existing_paths.json_path
        markdown_path = existing_paths.markdown_path
    else:
        boundary_dir = tmp_path / "external" / "gooaye"
        boundary_dir.mkdir(parents=True, exist_ok=True)
        json_path = boundary_dir / "EP672__EP672 title.external-boundary.json"
        markdown_path = boundary_dir / "EP672__EP672 title.external-boundary.md"
    if (generated or already_exists) and not json_path.exists():
        json_path.write_text("{}", encoding="utf-8")
        markdown_path.write_text("# verification", encoding="utf-8")
    return ExternalDataVerificationAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        boundary_json_path=json_path,
        boundary_markdown_path=markdown_path,
        verification_status="final",
        candidate_count=1,
        verified_candidate_count=1,
        warning_count=0,
        dry_run=False,
        requires_confirmation=False,
        provider="fixture",
        fixture_path=tmp_path / "external_market_data_fixtures.yaml",
        planned_reads=[str(json_path), str(tmp_path / "external_market_data_fixtures.yaml")],
        planned_writes=[str(json_path), str(markdown_path)],
        generated=generated,
        already_exists=already_exists,
        not_investment_advice=True,
    )


def _stock_lens_asset(tmp_path, *, generated=True, already_exists=False):
    from podcast_ingest_core.models import StockLensReportAsset

    stock_dir = tmp_path / "stock-lens" / "gooaye"
    stock_dir.mkdir(parents=True, exist_ok=True)
    json_path = stock_dir / "台積電.stock-lens.json"
    markdown_path = stock_dir / "台積電.stock-lens.md"
    if generated or already_exists:
        json_path.write_text("{}", encoding="utf-8")
        markdown_path.write_text("# stock lens", encoding="utf-8")
    return StockLensReportAsset(
        podcast_id="gooaye",
        stock_query="台積電",
        report_json_path=json_path,
        report_markdown_path=markdown_path,
        report_status="final",
        match_count=1,
        warning_count=0,
        generated=generated,
        already_exists=already_exists,
    )


def test_run_research_workflow_dry_run_does_not_write_artifacts(monkeypatch, tmp_path):
    from podcast_ingest_core.research_workflow import run_research_workflow

    transcript_paths = _write_transcript(monkeypatch, tmp_path)
    result = run_research_workflow("gooaye", "EP672", stock_query="台積電")

    step_names = [step.name for step in result.steps]
    assert result.dry_run is True
    assert result.workflow_status == "planned"
    assert result.requires_confirmation is True
    assert step_names == [
        "extract_mentions",
        "generate_episode_intelligence_report",
        "generate_industry_chain_mapping",
        "generate_external_data_boundary",
        "generate_stock_lens_report",
    ]
    assert result.planned_reads == [str(transcript_paths.json_path)]
    assert (
        "semantic_summarize_episode is not executed unless include_semantic_summary=True "
        "with exact api_cost_ack"
    ) in result.warnings
    assert any("Cache may be stale" in warning for warning in result.warnings)
    assert not (tmp_path / "mentions").exists()
    assert not (tmp_path / "reports").exists()
    assert not (tmp_path / "mappings").exists()
    assert not (tmp_path / "external").exists()
    assert not (tmp_path / "stock-lens").exists()


def test_run_research_workflow_external_verification_dry_run_includes_local_step(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow

    fixture_path = tmp_path / "external_market_data_fixtures.yaml"
    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "verify_external_data_boundary",
        lambda *args, **kwargs: pytest.fail("verification must not run in dry-run"),
        raising=False,
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        include_external_data_verification=True,
        external_fixture_path=fixture_path,
    )

    assert result.dry_run is True
    assert [step.name for step in result.steps] == [
        "extract_mentions",
        "generate_episode_intelligence_report",
        "generate_industry_chain_mapping",
        "generate_external_data_boundary",
        "verify_external_data_boundary",
        "generate_stock_lens_report",
    ]
    verification_step = result.steps[4]
    assert str(fixture_path) in verification_step.planned_reads
    assert "No live market API" in " ".join(verification_step.risks)
    assert "fixture" in " ".join(verification_step.risks)
    assert result.external_api_steps == ["semantic_summarize_episode"]
    assert not (tmp_path / "external").exists()
    assert not (tmp_path / "stock-lens").exists()


def test_run_research_workflow_synthesis_dry_run_requires_ack_and_writes_nothing(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_synthesis_report",
        lambda *args, **kwargs: pytest.fail("synthesis must not run in dry-run"),
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        include_stock_lens_synthesis=True,
    )

    assert result.dry_run is True
    assert result.requires_api_cost_ack is True
    assert result.required_acknowledgement == SEMANTIC_API_COST_ACK
    assert result.steps[-1].name == "generate_stock_lens_synthesis_report"
    assert "external LLM API" in " ".join(result.steps[-1].risks)
    assert "no raw transcript" in " ".join(result.steps[-1].risks)
    assert "cost risk" in " ".join(result.steps[-1].risks)
    assert result.external_api_steps == [
        "semantic_summarize_episode",
        "generate_stock_lens_synthesis_report",
    ]
    assert not (tmp_path / "mentions").exists()
    assert not (tmp_path / "stock-lens").exists()


def test_run_research_workflow_synthesis_requires_stock_query(monkeypatch, tmp_path):
    from podcast_ingest_core.errors import ResearchWorkflowInputError
    from podcast_ingest_core.research_workflow import run_research_workflow

    _write_transcript(monkeypatch, tmp_path)

    with pytest.raises(ResearchWorkflowInputError, match="stock_query"):
        run_research_workflow(
            "gooaye",
            "EP672",
            include_stock_lens_synthesis=True,
        )


def test_run_research_workflow_semantic_dry_run_requires_ack_and_writes_nothing(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("semantic summary must not run in dry-run"),
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        include_semantic_summary=True,
    )

    assert result.dry_run is True
    assert result.requires_api_cost_ack is True
    assert result.required_acknowledgement == SEMANTIC_API_COST_ACK
    assert result.steps[0].name == "semantic_summarize_episode"
    assert "external LLM API" in " ".join(result.steps[0].risks)
    assert "transcript transfer" in " ".join(result.steps[0].risks)
    assert "cost risk" in " ".join(result.steps[0].risks)
    assert not any("not executed unless include_semantic_summary" in warning for warning in result.warnings)
    assert not (tmp_path / "summaries").exists()
    assert not (tmp_path / "mentions").exists()


def test_run_research_workflow_confirm_generates_local_research_artifacts(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.research_workflow import run_research_workflow

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)

    result = run_research_workflow("gooaye", "EP672", confirm=True)

    assert result.dry_run is False
    assert result.workflow_status == "completed"
    assert result.requires_confirmation is False
    assert result.stock_query is None
    assert [step.status for step in result.steps] == ["completed"] * 4
    assert any(path.endswith(".mentions.json") for path in result.written_artifacts)
    assert any(path.endswith(".intelligence.json") for path in result.written_artifacts)
    assert any(path.endswith(".industry-map.json") for path in result.written_artifacts)
    assert any(path.endswith(".external-boundary.json") for path in result.written_artifacts)
    assert all(not path.endswith(".stock-lens.json") for path in result.written_artifacts)
    assert any("Cache may be stale" in warning for warning in result.warnings)


def test_run_research_workflow_synthesis_confirm_requires_ack_before_writes(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.errors import ResearchWorkflowInputError

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_synthesis_report",
        lambda *args, **kwargs: pytest.fail("synthesis must not run without ack"),
    )

    with pytest.raises(ResearchWorkflowInputError, match="api_cost_ack"):
        research_workflow.run_research_workflow(
            "gooaye",
            "EP672",
            stock_query="台積電",
            include_stock_lens_synthesis=True,
            confirm=True,
            api_cost_ack="wrong",
        )

    assert not (tmp_path / "mentions").exists()
    assert not (tmp_path / "reports").exists()
    assert not (tmp_path / "mappings").exists()
    assert not (tmp_path / "stock-lens").exists()


def test_run_research_workflow_semantic_confirm_requires_exact_ack_before_writes(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.errors import ResearchWorkflowInputError

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("semantic summary must not run without ack"),
    )

    with pytest.raises(ResearchWorkflowInputError, match="api_cost_ack"):
        research_workflow.run_research_workflow(
            "gooaye",
            "EP672",
            include_semantic_summary=True,
            confirm=True,
            api_cost_ack="wrong",
        )

    assert not (tmp_path / "summaries").exists()
    assert not (tmp_path / "mentions").exists()
    assert not (tmp_path / "reports").exists()


def test_run_research_workflow_confirm_external_verification_runs_before_stock_lens(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow

    fixture_path = tmp_path / "external_market_data_fixtures.yaml"
    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    calls = []

    def fake_verification(podcast_id, episode_ref, **kwargs):
        calls.append("verify_external_data_boundary")
        assert podcast_id == "gooaye"
        assert episode_ref == "EP672"
        assert kwargs == {
            "confirm": True,
            "force": False,
            "allow_partial": False,
            "provider": "fixture",
            "fixture_path": fixture_path,
        }
        return _verification_asset(tmp_path)

    def fake_stock_lens(*args, **kwargs):
        calls.append("generate_stock_lens_report")
        return _stock_lens_asset(tmp_path)

    monkeypatch.setattr(
        research_workflow,
        "verify_external_data_boundary",
        fake_verification,
        raising=False,
    )
    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_report",
        fake_stock_lens,
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        include_external_data_verification=True,
        external_fixture_path=fixture_path,
        confirm=True,
    )

    assert calls == ["verify_external_data_boundary", "generate_stock_lens_report"]
    assert [step.name for step in result.steps][-2:] == [
        "verify_external_data_boundary",
        "generate_stock_lens_report",
    ]
    assert any(path.endswith(".external-boundary.json") for path in result.written_artifacts)
    assert any(path.endswith(".stock-lens.json") for path in result.written_artifacts)


def test_run_research_workflow_rejects_unsupported_external_provider(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.errors import ResearchWorkflowInputError
    from podcast_ingest_core.research_workflow import run_research_workflow

    _write_transcript(monkeypatch, tmp_path)

    with pytest.raises(ResearchWorkflowInputError, match="unsupported external data provider"):
        run_research_workflow(
            "gooaye",
            "EP672",
            include_external_data_verification=True,
            external_data_provider="live-market-api",
        )


def test_run_research_workflow_external_verification_failure_stops_before_stock(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.errors import ExternalDataVerificationInputError

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)

    def fail_verification(*args, **kwargs):
        raise ExternalDataVerificationInputError("fixture missing")

    monkeypatch.setattr(
        research_workflow,
        "verify_external_data_boundary",
        fail_verification,
        raising=False,
    )
    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_report",
        lambda *args, **kwargs: pytest.fail("stock lens must not run after verification failure"),
    )

    with pytest.raises(ExternalDataVerificationInputError, match="fixture missing"):
        research_workflow.run_research_workflow(
            "gooaye",
            "EP672",
            stock_query="台積電",
            include_external_data_verification=True,
            confirm=True,
        )

    assert (tmp_path / "external" / "gooaye").exists()
    assert not (tmp_path / "stock-lens").exists()


def test_run_research_workflow_semantic_confirm_runs_semantic_first(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    calls = []

    def fake_semantic(**kwargs):
        calls.append(kwargs)
        return _semantic_asset(tmp_path)

    monkeypatch.setattr(
        research_workflow,
        "semantic_summarize_episode",
        fake_semantic,
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        include_semantic_summary=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
        semantic_model="test-model",
        semantic_base_url="https://example.test/v1",
        semantic_api_key_env="TEST_API_KEY",
        semantic_chunk_seconds=300,
        semantic_max_segments_per_chunk=50,
        confirm=True,
    )

    assert calls == [
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP672",
            "provider": "openai-compatible",
            "model": "test-model",
            "base_url": "https://example.test/v1",
            "api_key_env": "TEST_API_KEY",
            "force": False,
            "chunk_seconds": 300,
            "max_segments_per_chunk": 50,
            "allow_partial": False,
        }
    ]
    assert result.steps[0].name == "semantic_summarize_episode"
    assert result.steps[0].status == "completed"
    assert any(path.endswith(".semantic.md") for path in result.written_artifacts)
    assert any(path.endswith(".mentions.json") for path in result.written_artifacts)


def test_run_research_workflow_semantic_failure_fails_fast(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.errors import LLMProviderConfigError
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)

    def fail_semantic(**kwargs):
        raise LLMProviderConfigError("missing model")

    monkeypatch.setattr(research_workflow, "semantic_summarize_episode", fail_semantic)
    monkeypatch.setattr(
        research_workflow,
        "extract_mentions",
        lambda *args, **kwargs: pytest.fail("deterministic steps must not run after semantic failure"),
    )

    with pytest.raises(LLMProviderConfigError, match="missing model"):
        research_workflow.run_research_workflow(
            "gooaye",
            "EP672",
            include_semantic_summary=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
            confirm=True,
        )

    assert not (tmp_path / "mentions").exists()
    assert not (tmp_path / "reports").exists()


def test_run_research_workflow_confirm_with_stock_generates_stock_lens(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.research_workflow import run_research_workflow

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)

    result = run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        confirm=True,
        max_stock_evidence_items=3,
    )

    stock_step = result.steps[-1]
    assert stock_step.name == "generate_stock_lens_report"
    assert stock_step.status == "completed"
    assert any(path.endswith(".stock-lens.json") for path in result.written_artifacts)
    stock_payload = _read_json(tmp_path / "stock-lens" / "gooaye" / "台積電.stock-lens.json")
    assert stock_payload["stock_query"] == "台積電"
    assert stock_payload["not_investment_advice"] is True


def test_run_research_workflow_confirm_with_stock_synthesis_runs_last(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    calls = []

    def fake_synthesis(*args, **kwargs):
        calls.append((args, kwargs))
        return _synthesis_asset(tmp_path)

    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_synthesis_report",
        fake_synthesis,
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        include_stock_lens_synthesis=True,
        include_semantic_context_in_synthesis=True,
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
        synthesis_model="test-model",
        synthesis_base_url="https://example.test/v1",
        synthesis_api_key_env="TEST_API_KEY",
        synthesis_max_prompt_chars=12000,
        synthesis_semantic_context_max_chars=9000,
    )

    assert result.steps[-2].name == "generate_stock_lens_report"
    assert result.steps[-1].name == "generate_stock_lens_synthesis_report"
    assert result.steps[-1].status == "completed"
    assert calls == [
        (
            ("gooaye", "台積電"),
            {
                "confirm": True,
                "force": False,
                "allow_partial": False,
                "api_cost_ack": SEMANTIC_API_COST_ACK,
                "provider": "openai-compatible",
                "model": "test-model",
                "base_url": "https://example.test/v1",
                "api_key_env": "TEST_API_KEY",
                "max_prompt_chars": 12000,
                "include_semantic_context": True,
                "semantic_context_max_chars": 9000,
            },
        )
    ]
    assert any(path.endswith(".stock-lens-synthesis.json") for path in result.written_artifacts)
    assert any(path.endswith(".stock-lens-synthesis.md") for path in result.written_artifacts)


def test_run_research_workflow_synthesis_failure_propagates_after_local_steps(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.errors import LLMProviderConfigError
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)

    def fail_synthesis(*args, **kwargs):
        raise LLMProviderConfigError("missing synthesis model")

    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_synthesis_report",
        fail_synthesis,
    )

    with pytest.raises(LLMProviderConfigError, match="missing synthesis model"):
        research_workflow.run_research_workflow(
            "gooaye",
            "EP672",
            stock_query="台積電",
            include_stock_lens_synthesis=True,
            confirm=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    assert (tmp_path / "stock-lens" / "gooaye" / "台積電.stock-lens.json").exists()
    assert not (
        tmp_path / "stock-lens" / "gooaye" / "台積電.stock-lens-synthesis.json"
    ).exists()


def test_run_research_workflow_rejects_invalid_transcripts(monkeypatch, tmp_path):
    from podcast_ingest_core.errors import ResearchWorkflowInputError
    from podcast_ingest_core.research_workflow import run_research_workflow

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    with pytest.raises(ResearchWorkflowInputError, match="missing"):
        run_research_workflow("gooaye", "EP999", confirm=True)

    _write_transcript(monkeypatch, tmp_path, write_srt=False)
    with pytest.raises(ResearchWorkflowInputError, match="incomplete_outputs"):
        run_research_workflow("gooaye", "EP672", confirm=True)

    _write_transcript(monkeypatch, tmp_path, json_text="{broken")
    with pytest.raises(ResearchWorkflowInputError, match="corrupt"):
        run_research_workflow("gooaye", "EP672", confirm=True)


def test_run_research_workflow_handles_partial_transcript(monkeypatch, tmp_path):
    from podcast_ingest_core.errors import ResearchWorkflowInputError
    from podcast_ingest_core.research_workflow import run_research_workflow

    _write_transcript(monkeypatch, tmp_path, completed=False)
    _patch_configs(monkeypatch, tmp_path)

    dry_run = run_research_workflow("gooaye", "EP672")
    assert dry_run.workflow_status == "blocked"
    assert dry_run.transcript_status == "partial"

    with pytest.raises(ResearchWorkflowInputError, match="partial"):
        run_research_workflow("gooaye", "EP672", confirm=True)

    result = run_research_workflow("gooaye", "EP672", confirm=True, allow_partial=True)

    assert result.workflow_status == "partial-draft"
    assert result.transcript_status == "partial"
    mapping_paths = list((tmp_path / "mappings" / "gooaye").glob("*.industry-map.json"))
    assert mapping_paths
    assert _read_json(mapping_paths[0])["mapping_status"] == "partial-draft"


def test_run_research_workflow_synthesis_allow_partial_passes_through(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path, completed=False)
    _patch_configs(monkeypatch, tmp_path)
    captured = {}

    def fake_synthesis(*args, **kwargs):
        captured.update(kwargs)
        return _synthesis_asset(tmp_path)

    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_synthesis_report",
        fake_synthesis,
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        include_stock_lens_synthesis=True,
        confirm=True,
        allow_partial=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.workflow_status == "partial-draft"
    assert captured["allow_partial"] is True


def test_run_research_workflow_reuses_existing_unless_force(monkeypatch, tmp_path):
    from podcast_ingest_core.research_workflow import run_research_workflow

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)

    first = run_research_workflow("gooaye", "EP672", confirm=True)
    second = run_research_workflow("gooaye", "EP672", confirm=True)
    forced = run_research_workflow("gooaye", "EP672", confirm=True, force=True)

    assert first.generated_artifacts
    assert second.reused_artifacts
    assert not second.generated_artifacts
    assert forced.generated_artifacts
    assert not forced.reused_artifacts


def test_run_research_workflow_tracks_reused_synthesis_artifacts(monkeypatch, tmp_path):
    from podcast_ingest_core import research_workflow
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "generate_stock_lens_synthesis_report",
        lambda *args, **kwargs: _synthesis_asset(
            tmp_path, generated=False, already_exists=True
        ),
    )

    result = research_workflow.run_research_workflow(
        "gooaye",
        "EP672",
        stock_query="台積電",
        include_stock_lens_synthesis=True,
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert any(
        path.endswith(".stock-lens-synthesis.json") for path in result.reused_artifacts
    )


def test_run_research_workflow_dry_run_does_not_call_external_or_cache(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import research_workflow

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        research_workflow,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("semantic summary must not run"),
    )
    monkeypatch.setattr(
        research_workflow,
        "rebuild_cache",
        lambda *args, **kwargs: pytest.fail("rebuild_cache must not run"),
    )

    result = research_workflow.run_research_workflow("gooaye", "EP672")

    assert result.workflow_status == "planned"
    assert result.external_api_steps == ["semantic_summarize_episode"]


def test_run_research_workflow_cli_outputs_json(monkeypatch, tmp_path, capsys):
    import podcast_ingest_core.research_workflow as core_research_workflow
    from scripts import run_research_workflow

    _write_transcript(monkeypatch, tmp_path)
    _patch_configs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_workflow.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--confirm",
            "--force",
            "--allow-partial",
            "--include-semantic-summary",
            "--include-stock-lens-synthesis",
            "--include-semantic-context-in-synthesis",
            "--include-external-data-verification",
            "--api-cost-ack",
            "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.",
            "--semantic-provider",
            "openai-compatible",
            "--semantic-model",
            "test-model",
            "--semantic-base-url",
            "https://example.test/v1",
            "--semantic-api-key-env",
            "TEST_API_KEY",
            "--semantic-chunk-seconds",
            "300",
            "--semantic-max-segments-per-chunk",
            "50",
            "--synthesis-provider",
            "openai-compatible",
            "--synthesis-model",
            "synthesis-model",
            "--synthesis-base-url",
            "https://synthesis.example.test/v1",
            "--synthesis-api-key-env",
            "SYNTHESIS_API_KEY",
            "--synthesis-max-prompt-chars",
            "12000",
            "--synthesis-semantic-context-max-chars",
            "9000",
            "--external-data-provider",
            "fixture",
            "--external-fixture-path",
            str(tmp_path / "external_market_data_fixtures.yaml"),
            "--max-evidence-per-mention",
            "4",
            "--report-window-seconds",
            "120",
            "--max-evidence-per-section",
            "3",
            "--max-candidates-per-node",
            "2",
            "--max-evidence-per-candidate",
            "2",
            "--max-stock-evidence-items",
            "4",
        ],
    )
    monkeypatch.setattr(
        core_research_workflow,
        "semantic_summarize_episode",
        lambda **kwargs: _semantic_asset(tmp_path),
    )
    monkeypatch.setattr(
        core_research_workflow,
        "generate_stock_lens_synthesis_report",
        lambda *args, **kwargs: _synthesis_asset(tmp_path),
    )
    monkeypatch.setattr(
        core_research_workflow,
        "verify_external_data_boundary",
        lambda *args, **kwargs: _verification_asset(tmp_path),
        raising=False,
    )

    run_research_workflow.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["podcast_id"] == "gooaye"
    assert payload["episode_ref"] == "EP672"
    assert payload["stock_query"] == "台積電"
    assert payload["dry_run"] is False
    assert payload["workflow_status"] == "completed"
    assert payload["requires_api_cost_ack"] is False
    assert payload["steps"][0]["name"] == "semantic_summarize_episode"
    assert payload["steps"][-3]["name"] == "verify_external_data_boundary"
    assert payload["steps"][-2]["name"] == "generate_stock_lens_report"
    assert payload["steps"][-1]["name"] == "generate_stock_lens_synthesis_report"


def test_run_research_workflow_cli_loads_env_file(monkeypatch, tmp_path, capsys):
    from podcast_ingest_core.models import ResearchWorkflowResult
    from scripts import run_research_workflow

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nMODEL=file-model\n", encoding="utf-8")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    captured = {}

    def fake_workflow(*args, **kwargs):
        captured["api_key"] = os.environ.get("API_KEY")
        captured["model"] = os.environ.get("MODEL")
        captured["kwargs"] = kwargs
        return ResearchWorkflowResult(
            podcast_id="gooaye",
            episode_ref="EP672",
            stock_query=None,
            workflow_status="planned",
            dry_run=True,
            requires_confirmation=True,
            requires_api_cost_ack=False,
            required_acknowledgement=None,
            transcript_status="valid",
            steps=[],
            planned_reads=[],
            planned_writes=[],
            written_artifacts=[],
            generated_artifacts=[],
            reused_artifacts=[],
            external_api_steps=[],
            warnings=[],
            not_investment_advice=True,
        )

    monkeypatch.setattr(run_research_workflow, "run_research_workflow", fake_workflow)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_workflow.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--env-file",
            str(env_path),
            "--semantic-api-key-env",
            "API_KEY",
        ],
    )

    run_research_workflow.main()

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert captured["api_key"] == "secret-value"
    assert captured["model"] == "file-model"
    assert captured["kwargs"]["semantic_api_key_env"] == "API_KEY"
    assert payload["local_env"]["loaded_env_var_names"] == ["API_KEY", "MODEL"]
    assert "secret-value" not in output
