from __future__ import annotations

import json
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external", raising=False)


def _write_industry_mapping(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    mapping_status="final",
    corrupt=False,
):
    from corpus_ingest_core import storage
    from corpus_ingest_core.storage import industry_chain_mapping_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    transcript = storage.transcript_asset_paths(podcast_id, episode_ref, title)
    transcript.json_path.parent.mkdir(parents=True, exist_ok=True)
    transcript.json_path.write_text(
        json.dumps(
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "segments": [],
            }
        ),
        encoding="utf-8",
    )
    transcript.text_path.write_text("fixture", encoding="utf-8")
    transcript.srt_path.write_text("fixture", encoding="utf-8")
    paths = industry_chain_mapping_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    if corrupt:
        paths.json_path.write_text("{not-json", encoding="utf-8")
    else:
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


def _write_boundary_config(tmp_path):
    config_path = tmp_path / "external_data_boundary.yaml"
    config_path.write_text(
        """
version: 1
external_data_checks:
  - data_type: company_identity
    label: Company identity and legal entity
  - data_type: ticker_listing
    label: Ticker listing and exchange
  - data_type: sector_industry
    label: Sector and industry classification
  - data_type: market_snapshot
    label: Price, market cap, and liquidity snapshot
  - data_type: financial_snapshot
    label: Revenue, margin, and balance sheet snapshot
  - data_type: news_events
    label: Recent news and event verification
""".strip(),
        encoding="utf-8",
    )
    return config_path


def test_generate_external_data_boundary_writes_json_and_markdown(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.external_data_boundary as external_data_boundary

    config_path = _write_boundary_config(tmp_path)
    monkeypatch.setattr(external_data_boundary, "DEFAULT_BOUNDARY_CONFIG_PATH", config_path)
    _write_industry_mapping(monkeypatch, tmp_path)

    asset = external_data_boundary.generate_external_data_boundary("gooaye", "EP672")

    payload = json.loads(asset.boundary_json_path.read_text(encoding="utf-8"))
    markdown = asset.boundary_markdown_path.read_text(encoding="utf-8")
    explicit = [
        candidate
        for candidate in payload["candidate_boundaries"]
        if candidate["evidence_status"] == "podcast_explicit"
    ][0]
    inferred = [
        candidate
        for candidate in payload["candidate_boundaries"]
        if candidate["evidence_status"] == "inferred_from_industry"
    ][0]

    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.boundary_status == "final"
    assert asset.candidate_count == 2
    assert asset.warning_count == 0
    assert payload["boundary_mode"] == "external-data-boundary-v1"
    assert payload["source_status"]["industry_mapping"] == "available"
    assert payload["source_status"]["boundary_config"] == "available"
    assert explicit["company_name"] == "台積電"
    assert explicit["verification_status"] == "podcast_evidence"
    assert explicit["external_verification_status"] == "not_requested"
    assert explicit["source_status"] == "not_fetched"
    assert explicit["data_date"] is None
    assert {check["data_type"] for check in explicit["required_external_checks"]} == {
        "company_identity",
        "ticker_listing",
        "sector_industry",
        "market_snapshot",
        "financial_snapshot",
        "news_events",
    }
    assert all(
        check["requires_source_status"] is True and check["requires_data_date"] is True
        for check in explicit["required_external_checks"]
    )
    assert inferred["relation_type"] == "inferred_from_industry"
    assert inferred["verification_status"] == "needs_verification"
    assert inferred["external_verification_status"] == "not_requested"
    assert "# Gooaye 股癌 - EP672 External Data Boundary" in markdown
    assert "not_requested" in markdown
    assert "not_fetched" in markdown
    assert "本檔案不構成投資建議" in markdown


def test_generate_external_data_boundary_warns_when_config_missing(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.external_data_boundary as external_data_boundary

    monkeypatch.setattr(
        external_data_boundary,
        "DEFAULT_BOUNDARY_CONFIG_PATH",
        tmp_path / "missing.yaml",
    )
    _write_industry_mapping(monkeypatch, tmp_path)

    asset = external_data_boundary.generate_external_data_boundary("gooaye", "EP672")
    payload = json.loads(asset.boundary_json_path.read_text(encoding="utf-8"))

    assert payload["source_status"]["boundary_config"] == "missing_or_empty"
    assert "external data boundary config missing" in payload["warnings"][0]
    assert payload["candidate_boundaries"][0]["required_external_checks"] == []
    assert payload["candidate_boundaries"][0]["source_status"] == "not_fetched"
    assert payload["candidate_boundaries"][0]["data_date"] is None
    assert asset.warning_count == 1


def test_generate_external_data_boundary_rejects_missing_and_corrupt_mapping(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.external_data_boundary as external_data_boundary
    from corpus_ingest_core.errors import ExternalDataBoundaryInputError

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    with pytest.raises(ExternalDataBoundaryInputError, match="industry chain mapping"):
        external_data_boundary.generate_external_data_boundary("gooaye", "EP999")

    _write_industry_mapping(monkeypatch, tmp_path, corrupt=True)
    with pytest.raises(ExternalDataBoundaryInputError, match="JSON"):
        external_data_boundary.generate_external_data_boundary("gooaye", "EP672")


def test_generate_external_data_boundary_handles_partial_mapping(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.external_data_boundary as external_data_boundary
    from corpus_ingest_core.errors import ExternalDataBoundaryInputError

    config_path = _write_boundary_config(tmp_path)
    monkeypatch.setattr(external_data_boundary, "DEFAULT_BOUNDARY_CONFIG_PATH", config_path)
    _write_industry_mapping(monkeypatch, tmp_path, mapping_status="partial-draft")

    with pytest.raises(ExternalDataBoundaryInputError, match="partial-draft"):
        external_data_boundary.generate_external_data_boundary("gooaye", "EP672")

    asset = external_data_boundary.generate_external_data_boundary(
        "gooaye", "EP672", allow_partial=True
    )
    payload = json.loads(asset.boundary_json_path.read_text(encoding="utf-8"))

    assert asset.boundary_status == "partial-draft"
    assert payload["boundary_status"] == "partial-draft"


def test_generate_external_data_boundary_reuses_existing_without_force(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.external_data_boundary as external_data_boundary
    from corpus_ingest_core.storage import external_data_boundary_asset_paths

    config_path = _write_boundary_config(tmp_path)
    monkeypatch.setattr(external_data_boundary, "DEFAULT_BOUNDARY_CONFIG_PATH", config_path)
    _write_industry_mapping(monkeypatch, tmp_path)
    paths = external_data_boundary_asset_paths("gooaye", "EP672", "EP672 title")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("existing json", encoding="utf-8")
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")

    asset = external_data_boundary.generate_external_data_boundary("gooaye", "EP672")

    assert asset.generated is False
    assert asset.already_exists is True
    assert paths.json_path.read_text(encoding="utf-8") == "existing json"

    regenerated = external_data_boundary.generate_external_data_boundary(
        "gooaye", "EP672", force=True
    )
    assert regenerated.generated is True
    assert "existing json" not in paths.json_path.read_text(encoding="utf-8")


def test_external_data_boundary_path_removes_illegal_characters_and_emoji():
    from corpus_ingest_core.storage import external_data_boundary_asset_paths

    paths = external_data_boundary_asset_paths(
        "gooaye", "EP672", ' bad <title> 🐣 : / \\ | ? * ok '
    )

    assert not any(character in paths.json_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.json_path.name
    assert paths.json_path.name == "EP672__bad_title_ok.external-boundary.json"
    assert paths.markdown_path.name == "EP672__bad_title_ok.external-boundary.md"


def test_external_data_boundary_cli_parses_options_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from scripts import generate_external_data_boundary

    from corpus_ingest_core.models import ExternalDataBoundaryAsset

    asset = ExternalDataBoundaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        boundary_json_path=tmp_path / "boundary.json",
        boundary_markdown_path=tmp_path / "boundary.md",
        boundary_status="final",
        candidate_count=2,
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
        generate_external_data_boundary,
        "generate_external_data_boundary",
        fake_generate,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_external_data_boundary.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--force",
            "--allow-partial",
        ],
    )

    generate_external_data_boundary.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["boundary_json_path"] == str(tmp_path / "boundary.json")
    assert payload["candidate_count"] == 2
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "force": True,
        "allow_partial": True,
    }
