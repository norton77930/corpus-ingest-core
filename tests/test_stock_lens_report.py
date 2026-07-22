from __future__ import annotations

import json
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(storage, "STOCK_LENS_DIR", tmp_path / "stock-lens", raising=False)


def _write_mapping(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    mapping_status="final",
):
    from podcast_ingest_core.storage import industry_chain_mapping_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = industry_chain_mapping_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "mapping_mode": "deterministic-industry-chain-v1",
        "mapping_status": mapping_status,
        "source_status": {
            "episode_intelligence_report": "available",
            "mapping_config": "available",
        },
        "industry_chain_nodes": [],
        "stock_candidates": [
            {
                "company_name": "台積電",
                "tickers": ["2330.TW", "TSM"],
                "relation": "podcast_mention",
                "relation_type": "podcast_explicit",
                "evidence_status": "podcast_explicit",
                "verification_status": "podcast_evidence",
                "source_terms": ["台積電"],
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
            },
            {
                "company_name": "NVIDIA",
                "tickers": ["NVDA"],
                "relation": "accelerator_design",
                "relation_type": "inferred_from_industry",
                "evidence_status": "inferred_from_industry",
                "verification_status": "needs_verification",
                "source_terms": ["半導體"],
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
            },
        ],
        "warnings": [],
        "not_investment_advice": True,
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# mapping", encoding="utf-8")
    return paths


def _write_external_boundary(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    boundary_status="final",
):
    from podcast_ingest_core.storage import external_data_boundary_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = external_data_boundary_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "boundary_mode": "external-data-boundary-v1",
        "boundary_status": boundary_status,
        "source_status": {
            "industry_mapping": "available",
            "boundary_config": "available",
        },
        "candidate_boundaries": [
            {
                "company_name": "台積電",
                "tickers": ["2330.TW", "TSM"],
                "relation": "podcast_mention",
                "relation_type": "podcast_explicit",
                "evidence_status": "podcast_explicit",
                "verification_status": "podcast_evidence",
                "external_verification_status": "not_requested",
                "source_status": "not_fetched",
                "data_date": None,
                "required_external_checks": [
                    {
                        "data_type": "company_identity",
                        "label": "Company identity and legal entity",
                        "requires_source_status": True,
                        "requires_data_date": True,
                    }
                ],
            },
            {
                "company_name": "NVIDIA",
                "tickers": ["NVDA"],
                "relation": "accelerator_design",
                "relation_type": "inferred_from_industry",
                "evidence_status": "inferred_from_industry",
                "verification_status": "needs_verification",
                "external_verification_status": "not_requested",
                "source_status": "not_fetched",
                "data_date": None,
                "required_external_checks": [
                    {
                        "data_type": "market_snapshot",
                        "label": "Price, market cap, and liquidity snapshot",
                        "requires_source_status": True,
                        "requires_data_date": True,
                    }
                ],
            },
        ],
        "warnings": [],
        "not_investment_advice": True,
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# boundary", encoding="utf-8")
    return paths


def test_generate_stock_lens_report_writes_json_and_markdown(monkeypatch, tmp_path):
    import podcast_ingest_core.stock_lens as stock_lens

    _write_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)

    asset = stock_lens.generate_stock_lens_report("gooaye", "台積電")

    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))
    markdown = asset.report_markdown_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.report_status == "final"
    assert asset.match_count == 1
    assert payload["report_mode"] == "deterministic-stock-lens-v1"
    assert payload["query_match_summary"]["direct_podcast_evidence_count"] == 1
    assert payload["direct_podcast_evidence"][0]["company_name"] == "台積電"
    assert payload["direct_podcast_evidence"][0]["evidence"][0]["timestamp"] == (
        "[00:01:23 - 00:01:30]"
    )
    assert payload["direct_podcast_evidence"][0]["external_boundary"] == {
        "external_verification_status": "not_requested",
        "source_status": "not_fetched",
        "data_date": None,
        "required_external_checks": [
            {
                "data_type": "company_identity",
                "label": "Company identity and legal entity",
                "requires_source_status": True,
                "requires_data_date": True,
            }
        ],
    }
    assert payload["gooaye_lens"]["dimension_count"] == 6
    assert "本報告不構成投資建議" in markdown
    assert "No target price" in markdown


def test_generate_stock_lens_report_matches_ticker_as_inferred_lead(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.stock_lens as stock_lens

    _write_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)

    asset = stock_lens.generate_stock_lens_report("gooaye", "nvda")
    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))

    assert asset.report_status == "no-direct-podcast-evidence"
    assert payload["query_match_summary"]["direct_podcast_evidence_count"] == 0
    assert payload["query_match_summary"]["inferred_research_lead_count"] == 1
    assert payload["inferred_research_leads"][0]["company_name"] == "NVIDIA"
    assert payload["inferred_research_leads"][0]["verification_status"] == "needs_verification"
    assert payload["inferred_research_leads"][0]["evidence_status"] == "inferred_from_industry"


def test_generate_stock_lens_report_without_match_states_no_direct_evidence(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.stock_lens as stock_lens

    _write_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)

    asset = stock_lens.generate_stock_lens_report("gooaye", "不存在公司")
    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))
    markdown = asset.report_markdown_path.read_text(encoding="utf-8")

    assert asset.report_status == "no-direct-podcast-evidence"
    assert payload["direct_podcast_evidence"] == []
    assert payload["inferred_research_leads"] == []
    assert payload["query_match_summary"]["no_direct_podcast_evidence"] is True
    assert "no direct podcast evidence found" in markdown


def test_generate_stock_lens_report_fails_when_external_boundary_missing(
    monkeypatch, tmp_path
):
    """Identity-bound stock-lens lineage requires the mapping's boundary artifact."""

    import podcast_ingest_core.stock_lens as stock_lens
    from podcast_ingest_core.errors import StockLensReportInputError

    _write_mapping(monkeypatch, tmp_path)

    with pytest.raises(StockLensReportInputError, match="external boundary missing"):
        stock_lens.generate_stock_lens_report("gooaye", "台積電")


def test_red_stock_lens_rejects_alpha_boundary_for_corrected_mapping(
    monkeypatch, tmp_path
):
    """A same-episode lexical boundary is never a substitute for mapping title identity."""

    import podcast_ingest_core.stock_lens as stock_lens
    from podcast_ingest_core.errors import StockLensReportInputError

    _write_mapping(monkeypatch, tmp_path, episode_ref="EP672", title="EP672 Corrected")
    _write_external_boundary(monkeypatch, tmp_path, episode_ref="EP672", title="EP672 Alpha")

    with pytest.raises(StockLensReportInputError, match="external boundary missing|identity"):
        stock_lens.generate_stock_lens_report("gooaye", "台積電")


def test_generate_stock_lens_report_handles_partial_matched_artifacts(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.stock_lens as stock_lens
    from podcast_ingest_core.errors import StockLensReportInputError

    _write_mapping(monkeypatch, tmp_path, mapping_status="partial-draft")
    _write_external_boundary(monkeypatch, tmp_path, boundary_status="partial-draft")

    with pytest.raises(StockLensReportInputError, match="partial-draft"):
        stock_lens.generate_stock_lens_report("gooaye", "台積電")

    asset = stock_lens.generate_stock_lens_report(
        "gooaye", "台積電", allow_partial=True
    )
    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))

    assert asset.report_status == "partial-draft"
    assert payload["report_status"] == "partial-draft"


def test_generate_stock_lens_report_reuses_existing_without_force(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.stock_lens as stock_lens
    from podcast_ingest_core.storage import stock_lens_report_asset_paths

    _write_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)
    paths = stock_lens_report_asset_paths("gooaye", "台積電")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("existing json", encoding="utf-8")
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")

    asset = stock_lens.generate_stock_lens_report("gooaye", "台積電")

    assert asset.generated is False
    assert asset.already_exists is True
    assert paths.json_path.read_text(encoding="utf-8") == "existing json"

    regenerated = stock_lens.generate_stock_lens_report("gooaye", "台積電", force=True)
    assert regenerated.generated is True
    assert "existing json" not in paths.json_path.read_text(encoding="utf-8")


def test_stock_lens_report_path_removes_illegal_characters_and_emoji():
    from podcast_ingest_core.storage import stock_lens_report_asset_paths

    paths = stock_lens_report_asset_paths("gooaye", ' bad <stock> 🐣 : / \\ | ? * ok ')

    assert not any(character in paths.json_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.json_path.name
    assert paths.json_path.name == "bad_stock_ok.stock-lens.json"
    assert paths.markdown_path.name == "bad_stock_ok.stock-lens.md"


def test_stock_lens_report_cli_parses_options_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import StockLensReportAsset
    from scripts import generate_stock_lens_report

    asset = StockLensReportAsset(
        podcast_id="gooaye",
        stock_query="台積電",
        report_json_path=tmp_path / "report.json",
        report_markdown_path=tmp_path / "report.md",
        report_status="final",
        match_count=1,
        warning_count=0,
        generated=True,
        already_exists=False,
    )
    captured = {}

    def fake_generate(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(
        generate_stock_lens_report,
        "generate_stock_lens_report",
        fake_generate,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_stock_lens_report.py",
            "--podcast",
            "gooaye",
            "--stock",
            "台積電",
            "--force",
            "--allow-partial",
            "--max-evidence-items",
            "5",
        ],
    )

    generate_stock_lens_report.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["report_json_path"] == str(tmp_path / "report.json")
    assert payload["match_count"] == 1
    assert captured["args"] == ("gooaye", "台積電")
    assert captured["kwargs"] == {
        "force": True,
        "allow_partial": True,
        "max_evidence_items": 5,
    }
