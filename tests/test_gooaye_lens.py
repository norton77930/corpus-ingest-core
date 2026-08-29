from __future__ import annotations

import json
import sys

import pytest


def _write_lens_config(tmp_path, *, incomplete: bool = False):
    config_path = tmp_path / "gooaye_lens.yaml"
    if incomplete:
        config_path.write_text(
            """
version: 1
name: Gooaye Lens
description: incomplete
dimensions:
  - id: industry_chain_position
    label: 產業鏈位置
    description: Locate the company or topic inside the supply chain.
    analysis_questions:
      - What role is implied?
    expected_evidence_sources:
      - podcast_evidence
safety_rules:
  - Do not provide buy/sell/hold advice.
  - Do not provide target price.
  - Do not promise or imply guaranteed returns.
  - Separate podcast evidence, inference, and external-data status.
  - Do not fabricate podcast evidence.
""".strip(),
            encoding="utf-8",
        )
        return config_path

    config_path.write_text(
        """
version: 1
name: Gooaye Lens
description: Deterministic reusable framework for Gooaye-style research.
dimensions:
  - id: industry_chain_position
    label: 產業鏈位置
    description: Locate the company or topic inside the supply chain.
    analysis_questions:
      - What upstream, midstream, downstream, or customer role is implied?
    expected_evidence_sources:
      - podcast_evidence
      - industry_mapping
      - external_data_boundary
    output_guidance: Separate explicit podcast evidence from inferred chain position.
  - id: supply_demand_inventory
    label: 供需與庫存
    description: Frame demand, supply, backlog, and inventory pressure.
    analysis_questions:
      - Is the evidence pointing to tight supply, weak demand, or inventory correction?
    expected_evidence_sources:
      - podcast_evidence
      - external_data_boundary
    output_guidance: Mark missing external data instead of filling gaps.
  - id: cycle
    label: 景氣循環
    description: Place the topic in a cyclical or structural phase.
    analysis_questions:
      - Is the issue cyclical, structural, or mixed?
    expected_evidence_sources:
      - podcast_evidence
      - macro_variables
    output_guidance: Avoid treating one episode as a full cycle diagnosis.
  - id: rates_valuation_sensitivity
    label: 利率與估值敏感度
    description: Identify rate, inflation, duration, and valuation sensitivity.
    analysis_questions:
      - Which variables could change valuation sensitivity?
    expected_evidence_sources:
      - macro_variables
      - external_data_boundary
    output_guidance: Do not produce target prices or valuation calls.
  - id: capex_capacity
    label: 資本支出與產能
    description: Track capex, capacity, and production bottlenecks.
    analysis_questions:
      - Is future supply constrained by capex or capacity timing?
    expected_evidence_sources:
      - industry_mapping
      - external_data_boundary
    output_guidance: Keep capex facts unverified unless external data is fetched.
  - id: geopolitics_uncertainty
    label: 地緣政治與不確定性
    description: Preserve geopolitical, policy, and uncertainty signals.
    analysis_questions:
      - Which uncertainty should remain explicit instead of resolved?
    expected_evidence_sources:
      - podcast_evidence
      - external_data_boundary
    output_guidance: State uncertainty plainly and avoid overconfident conclusions.
safety_rules:
  - Do not provide buy/sell/hold advice.
  - Do not provide target price.
  - Do not promise or imply guaranteed returns.
  - Separate podcast evidence, inference, and external-data status.
  - Do not fabricate podcast evidence.
""".strip(),
        encoding="utf-8",
    )
    return config_path


def test_load_gooaye_lens_model_loads_valid_config(tmp_path):
    from corpus_ingest_core.gooaye_lens import load_gooaye_lens_model
    from corpus_ingest_core.models import GooayeLensModel

    config_path = _write_lens_config(tmp_path)

    model = load_gooaye_lens_model(config_path)

    assert isinstance(model, GooayeLensModel)
    assert model.version == 1
    assert model.name == "Gooaye Lens"
    assert len(model.dimensions) == 6
    assert model.dimensions[0].id == "industry_chain_position"


def test_gooaye_lens_model_contains_expected_core_dimensions():
    from corpus_ingest_core.gooaye_lens import load_gooaye_lens_model

    model = load_gooaye_lens_model()
    dimension_ids = {dimension.id for dimension in model.dimensions}

    assert {
        "industry_chain_position",
        "supply_demand_inventory",
        "cycle",
        "rates_valuation_sensitivity",
        "capex_capacity",
        "geopolitics_uncertainty",
    } <= dimension_ids


def test_gooaye_lens_dimensions_are_complete(tmp_path):
    from corpus_ingest_core.gooaye_lens import load_gooaye_lens_model

    model = load_gooaye_lens_model(_write_lens_config(tmp_path))

    for dimension in model.dimensions:
        assert dimension.id
        assert dimension.label
        assert dimension.description
        assert dimension.analysis_questions
        assert dimension.expected_evidence_sources
        assert dimension.output_guidance


def test_gooaye_lens_safety_rules_cover_research_boundaries(tmp_path):
    from corpus_ingest_core.gooaye_lens import load_gooaye_lens_model

    model = load_gooaye_lens_model(_write_lens_config(tmp_path))
    safety_text = "\n".join(model.safety_rules).lower()

    assert "buy/sell/hold" in safety_text
    assert "target price" in safety_text
    assert "guaranteed returns" in safety_text
    assert "podcast evidence, inference, and external-data status" in safety_text
    assert "do not fabricate podcast evidence" in safety_text


def test_load_gooaye_lens_model_rejects_missing_and_malformed_config(tmp_path):
    from corpus_ingest_core.errors import GooayeLensConfigError
    from corpus_ingest_core.gooaye_lens import load_gooaye_lens_model

    with pytest.raises(GooayeLensConfigError, match="missing"):
        load_gooaye_lens_model(tmp_path / "missing.yaml")

    malformed_path = tmp_path / "malformed.yaml"
    malformed_path.write_text("dimensions: [", encoding="utf-8")
    with pytest.raises(GooayeLensConfigError, match="unreadable"):
        load_gooaye_lens_model(malformed_path)


def test_load_gooaye_lens_model_rejects_incomplete_config(tmp_path):
    from corpus_ingest_core.errors import GooayeLensConfigError
    from corpus_ingest_core.gooaye_lens import load_gooaye_lens_model

    with pytest.raises(GooayeLensConfigError, match="output_guidance"):
        load_gooaye_lens_model(_write_lens_config(tmp_path, incomplete=True))


def test_inspect_gooaye_lens_cli_outputs_json(monkeypatch, capsys, tmp_path):
    from scripts import inspect_gooaye_lens

    config_path = _write_lens_config(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "inspect_gooaye_lens.py",
            "--path",
            str(config_path),
        ],
    )

    inspect_gooaye_lens.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "Gooaye Lens"
    assert payload["version"] == 1
    assert payload["dimension_count"] == 6
    assert payload["dimensions"][0]["id"] == "industry_chain_position"
