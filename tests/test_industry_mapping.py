from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")


def _write_episode_report(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    report_status="final",
    industry_text="半導體",
    include_company=True,
):
    from corpus_ingest_core import storage
    from corpus_ingest_core.storage import episode_intelligence_report_asset_paths

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
    paths = episode_intelligence_report_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    company_mentions = []
    if include_company:
        company_mentions.append(
            {
                "type": "company",
                "text": "台積電",
                "normalized_text": "台積電",
                "count": 1,
                "confidence": "rule",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
            }
        )
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "report_mode": "deterministic-episode-intelligence-v1",
        "report_status": report_status,
        "source_status": {
            "transcript": "valid" if report_status == "final" else "partial",
            "mentions": "available",
        },
        "mentions_by_type": {
            "company": company_mentions,
        },
        "industry_clues": [
            {
                "type": "industry",
                "text": industry_text,
                "normalized_text": industry_text,
                "count": 1,
                "confidence": "rule",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
            }
        ],
        "macro_variables": [],
        "risks_and_uncertainties": [],
        "not_investment_advice": True,
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# report", encoding="utf-8")
    return paths


def _write_mapping_config(tmp_path, *, include_semiconductor=True):
    config_path = tmp_path / "industry_chain_mappings.yaml"
    if include_semiconductor:
        config_path.write_text(
            """
version: 1
industry_nodes:
  semiconductor:
    label: 半導體
    aliases:
      - 半導體
      - 晶片
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
  NVIDIA:
    company_name: NVIDIA
    tickers:
      - NVDA
    industry_node_ids:
      - semiconductor
""".strip(),
            encoding="utf-8",
        )
    else:
        config_path.write_text(
            """
version: 1
industry_nodes: {}
company_aliases: {}
""".strip(),
            encoding="utf-8",
        )
    return config_path


def test_generate_industry_chain_mapping_writes_json_and_markdown(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.industry_mapping as industry_mapping

    config_path = _write_mapping_config(tmp_path)
    monkeypatch.setattr(industry_mapping, "DEFAULT_MAPPING_CONFIG_PATH", config_path)
    _write_episode_report(monkeypatch, tmp_path)

    asset = industry_mapping.generate_industry_chain_mapping("gooaye", "EP672")

    payload = json.loads(asset.mapping_json_path.read_text(encoding="utf-8"))
    markdown = asset.mapping_markdown_path.read_text(encoding="utf-8")
    explicit = [
        candidate
        for candidate in payload["stock_candidates"]
        if candidate["evidence_status"] == "podcast_explicit"
    ]
    inferred = [
        candidate
        for candidate in payload["stock_candidates"]
        if candidate["evidence_status"] == "inferred_from_industry"
    ]
    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.mapping_status == "final"
    assert asset.warning_count == 0
    assert payload["mapping_mode"] == "deterministic-industry-chain-v1"
    assert payload["source_status"]["episode_intelligence_report"] == "available"
    assert payload["industry_chain_nodes"][0]["node_id"] == "semiconductor"
    assert explicit[0]["company_name"] == "台積電"
    assert explicit[0]["verification_status"] == "podcast_evidence"
    assert explicit[0]["evidence"][0]["timestamp"] == "[00:01:23 - 00:01:30]"
    assert any(candidate["company_name"] == "NVIDIA" for candidate in inferred)
    assert {candidate["verification_status"] for candidate in inferred} == {
        "needs_verification"
    }
    assert "# Gooaye 股癌 - EP672 Industry Chain Mapping" in markdown
    assert "podcast_explicit" in markdown
    assert "inferred_from_industry" in markdown
    assert "本檔案不構成投資建議" in markdown


def test_generate_industry_chain_mapping_warns_without_fabricating_candidates(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.industry_mapping as industry_mapping

    monkeypatch.setattr(
        industry_mapping, "DEFAULT_MAPPING_CONFIG_PATH", tmp_path / "missing.yaml"
    )
    _write_episode_report(monkeypatch, tmp_path, include_company=False)

    asset = industry_mapping.generate_industry_chain_mapping("gooaye", "EP672")
    payload = json.loads(asset.mapping_json_path.read_text(encoding="utf-8"))

    assert payload["stock_candidates"] == []
    assert payload["industry_chain_nodes"] == []
    assert "mapping config missing" in payload["warnings"][0]
    assert asset.warning_count == 1

    config_path = _write_mapping_config(tmp_path, include_semiconductor=False)
    monkeypatch.setattr(industry_mapping, "DEFAULT_MAPPING_CONFIG_PATH", config_path)
    _write_episode_report(
        monkeypatch,
        tmp_path,
        episode_ref="EP673",
        industry_text="未知產業",
        include_company=False,
    )

    unmatched = industry_mapping.generate_industry_chain_mapping("gooaye", "EP673")
    unmatched_payload = json.loads(unmatched.mapping_json_path.read_text(encoding="utf-8"))
    assert unmatched_payload["stock_candidates"] == []
    assert "unmatched industry clue: 未知產業" in unmatched_payload["warnings"]


def test_generate_industry_chain_mapping_handles_partial_report(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.industry_mapping as industry_mapping
    from corpus_ingest_core.errors import IndustryMappingInputError

    config_path = _write_mapping_config(tmp_path)
    monkeypatch.setattr(industry_mapping, "DEFAULT_MAPPING_CONFIG_PATH", config_path)
    _write_episode_report(monkeypatch, tmp_path, report_status="partial-draft")

    with pytest.raises(IndustryMappingInputError, match="partial-draft"):
        industry_mapping.generate_industry_chain_mapping("gooaye", "EP672")

    asset = industry_mapping.generate_industry_chain_mapping(
        "gooaye", "EP672", allow_partial=True
    )
    payload = json.loads(asset.mapping_json_path.read_text(encoding="utf-8"))

    assert asset.mapping_status == "partial-draft"
    assert payload["mapping_status"] == "partial-draft"


def test_generate_industry_chain_mapping_reuses_existing_without_force(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.industry_mapping as industry_mapping
    from corpus_ingest_core.storage import industry_chain_mapping_asset_paths

    config_path = _write_mapping_config(tmp_path)
    monkeypatch.setattr(industry_mapping, "DEFAULT_MAPPING_CONFIG_PATH", config_path)
    _write_episode_report(monkeypatch, tmp_path)
    paths = industry_chain_mapping_asset_paths("gooaye", "EP672", "EP672 title")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("existing json", encoding="utf-8")
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")

    asset = industry_mapping.generate_industry_chain_mapping("gooaye", "EP672")

    assert asset.generated is False
    assert asset.already_exists is True
    assert paths.json_path.read_text(encoding="utf-8") == "existing json"

    regenerated = industry_mapping.generate_industry_chain_mapping(
        "gooaye", "EP672", force=True
    )
    assert regenerated.generated is True
    assert "existing json" not in paths.json_path.read_text(encoding="utf-8")


def test_industry_chain_mapping_path_removes_illegal_characters_and_emoji():
    from corpus_ingest_core.storage import industry_chain_mapping_asset_paths

    paths = industry_chain_mapping_asset_paths(
        "gooaye", "EP672", ' bad <title> 🐣 : / \\ | ? * ok '
    )

    assert not any(character in paths.json_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.json_path.name
    assert paths.json_path.name == "EP672__bad_title_ok.industry-map.json"
    assert paths.markdown_path.name == "EP672__bad_title_ok.industry-map.md"


def test_industry_chain_mapping_cli_parses_options_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from corpus_ingest_core.models import IndustryChainMappingAsset
    from scripts import generate_industry_chain_mapping

    asset = IndustryChainMappingAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        mapping_json_path=tmp_path / "mapping.json",
        mapping_markdown_path=tmp_path / "mapping.md",
        mapping_status="final",
        node_count=1,
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
        generate_industry_chain_mapping,
        "generate_industry_chain_mapping",
        fake_generate,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_industry_chain_mapping.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--force",
            "--allow-partial",
            "--max-candidates-per-node",
            "3",
            "--max-evidence-per-candidate",
            "2",
        ],
    )

    generate_industry_chain_mapping.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["mapping_json_path"] == str(tmp_path / "mapping.json")
    assert payload["candidate_count"] == 2
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "force": True,
        "allow_partial": True,
        "max_candidates_per_node": 3,
        "max_evidence_per_candidate": 2,
    }
