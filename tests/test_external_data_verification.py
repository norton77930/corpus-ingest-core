from __future__ import annotations

import json
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")


def _write_boundary(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    boundary_status="final",
    boundary_mode="external-data-boundary-v1",
    corrupt=False,
    verified=False,
):
    from podcast_ingest_core.storage import external_data_boundary_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = external_data_boundary_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    if corrupt:
        paths.json_path.write_text("{not-json", encoding="utf-8")
    else:
        payload = {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "boundary_mode": boundary_mode,
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
        if verified:
            payload["external_data_verification"] = {
                "verification_mode": "fixture-external-data-v1",
                "provider": "fixture",
                "verified_candidate_count": 1,
            }
            payload["candidate_boundaries"][0]["external_verification_status"] = "verified"
            payload["candidate_boundaries"][0]["source_status"] = "fixture_available"
            payload["candidate_boundaries"][0]["data_date"] = "2026-06-28"
        paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# boundary", encoding="utf-8")
    return paths


def _write_fixture(tmp_path, *, include_nvidia=True):
    fixture_path = tmp_path / "external_market_data_fixtures.yaml"
    nvidia = """
  - company_name: NVIDIA
    tickers:
      - NVDA
    data_date: "2026-06-28"
    source_status: fixture_available
    source_name: local fixture
    external_data:
      market_snapshot:
        snapshot_label: Fixture-only market snapshot
        source_note: local fixture data
""" if include_nvidia else ""
    fixture_path.write_text(
        f"""
version: 1
candidates:
  - company_name: 台積電
    tickers:
      - 2330.TW
      - TSM
    data_date: "2026-06-28"
    source_status: fixture_available
    source_name: local fixture
    external_data:
      company_identity:
        legal_name: Taiwan Semiconductor Manufacturing Company Limited
        source_note: local fixture data
{nvidia}
""".strip(),
        encoding="utf-8",
    )
    return fixture_path


def test_verify_external_data_boundary_dry_run_writes_nothing(monkeypatch, tmp_path):
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    paths = _write_boundary(monkeypatch, tmp_path)
    fixture_path = _write_fixture(tmp_path)
    before_json = paths.json_path.read_text(encoding="utf-8")
    before_markdown = paths.markdown_path.read_text(encoding="utf-8")

    asset = verify_external_data_boundary(
        "gooaye",
        "EP672",
        fixture_path=fixture_path,
    )

    assert asset.dry_run is True
    assert asset.requires_confirmation is True
    assert asset.provider == "fixture"
    assert asset.candidate_count == 2
    assert asset.verified_candidate_count == 0
    assert asset.planned_reads == [str(paths.json_path), str(fixture_path)]
    assert asset.planned_writes == [str(paths.json_path), str(paths.markdown_path)]
    assert paths.json_path.read_text(encoding="utf-8") == before_json
    assert paths.markdown_path.read_text(encoding="utf-8") == before_markdown


def test_verify_external_data_boundary_confirm_updates_fixture_matches(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    paths = _write_boundary(monkeypatch, tmp_path)
    fixture_path = _write_fixture(tmp_path)

    asset = verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        fixture_path=fixture_path,
    )
    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    markdown = paths.markdown_path.read_text(encoding="utf-8")
    explicit = payload["candidate_boundaries"][0]
    inferred = payload["candidate_boundaries"][1]

    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.verified_candidate_count == 2
    assert payload["external_data_verification"]["provider"] == "fixture"
    assert payload["external_data_verification"]["verified_candidate_count"] == 2
    assert explicit["external_verification_status"] == "verified"
    assert explicit["source_status"] == "fixture_available"
    assert explicit["data_date"] == "2026-06-28"
    assert explicit["external_data"]["company_identity"]["legal_name"].startswith("Taiwan")
    assert explicit["external_data_source"]["provider"] == "fixture"
    assert inferred["relation_type"] == "inferred_from_industry"
    assert inferred["evidence_status"] == "inferred_from_industry"
    assert inferred["verification_status"] == "needs_verification"
    assert inferred["external_verification_status"] == "verified"
    assert "External data verification" in markdown
    assert "not investment advice" in markdown


def test_verify_external_data_boundary_missing_fixture_warns_without_fabricating(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    paths = _write_boundary(monkeypatch, tmp_path)

    asset = verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        fixture_path=tmp_path / "missing.yaml",
    )
    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))

    assert asset.generated is True
    assert asset.verified_candidate_count == 0
    assert asset.warning_count >= 1
    assert "fixture config missing" in payload["warnings"][0]
    assert payload["candidate_boundaries"][0]["source_status"] == "not_fetched"
    assert payload["candidate_boundaries"][0]["data_date"] is None
    assert "external_data" not in payload["candidate_boundaries"][0]


def test_verify_external_data_boundary_unmatched_candidate_warns(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    paths = _write_boundary(monkeypatch, tmp_path)
    fixture_path = _write_fixture(tmp_path, include_nvidia=False)

    asset = verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        fixture_path=fixture_path,
    )
    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    inferred = payload["candidate_boundaries"][1]

    assert asset.verified_candidate_count == 1
    assert any("no fixture match for NVIDIA" in warning for warning in payload["warnings"])
    assert inferred["source_status"] == "not_fetched"
    assert inferred["data_date"] is None


def test_verify_external_data_boundary_rejects_missing_corrupt_and_unsupported(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.errors import ExternalDataVerificationInputError
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    with pytest.raises(ExternalDataVerificationInputError, match="external boundary"):
        verify_external_data_boundary("gooaye", "EP999", confirm=True)

    _write_boundary(monkeypatch, tmp_path, corrupt=True)
    with pytest.raises(ExternalDataVerificationInputError, match="JSON"):
        verify_external_data_boundary("gooaye", "EP672", confirm=True)

    _write_boundary(monkeypatch, tmp_path, boundary_mode="unsupported-mode")
    with pytest.raises(ExternalDataVerificationInputError, match="mode"):
        verify_external_data_boundary("gooaye", "EP672", confirm=True)


def test_verify_external_data_boundary_handles_partial_boundary(monkeypatch, tmp_path):
    from podcast_ingest_core.errors import ExternalDataVerificationInputError
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    _write_boundary(monkeypatch, tmp_path, boundary_status="partial-draft")
    fixture_path = _write_fixture(tmp_path)

    with pytest.raises(ExternalDataVerificationInputError, match="partial-draft"):
        verify_external_data_boundary("gooaye", "EP672", confirm=True, fixture_path=fixture_path)

    asset = verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        allow_partial=True,
        fixture_path=fixture_path,
    )

    assert asset.verification_status == "partial-draft"


def test_verify_external_data_boundary_reuses_verified_artifact_unless_force(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    paths = _write_boundary(monkeypatch, tmp_path, verified=True)
    fixture_path = _write_fixture(tmp_path)
    before = paths.json_path.read_text(encoding="utf-8")

    asset = verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        fixture_path=fixture_path,
    )

    assert asset.generated is False
    assert asset.already_exists is True
    assert paths.json_path.read_text(encoding="utf-8") == before

    forced = verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        force=True,
        fixture_path=fixture_path,
    )
    assert forced.generated is True


def test_verify_external_data_boundary_rejects_unsupported_provider(monkeypatch, tmp_path):
    from podcast_ingest_core.errors import ExternalDataVerificationInputError
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    _write_boundary(monkeypatch, tmp_path)

    with pytest.raises(ExternalDataVerificationInputError, match="provider"):
        verify_external_data_boundary(
            "gooaye",
            "EP672",
            provider="live-market-api",
        )


def test_verify_external_data_boundary_output_contains_no_advice(monkeypatch, tmp_path):
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary

    paths = _write_boundary(monkeypatch, tmp_path)
    fixture_path = _write_fixture(tmp_path)

    verify_external_data_boundary(
        "gooaye",
        "EP672",
        confirm=True,
        fixture_path=fixture_path,
    )

    combined = (
        paths.json_path.read_text(encoding="utf-8")
        + "\n"
        + paths.markdown_path.read_text(encoding="utf-8")
    ).lower()
    assert "buy" not in combined
    assert "sell" not in combined
    assert "hold" not in combined
    assert "target price" not in combined
    assert "guaranteed return" not in combined
    assert "recommendation" not in combined


def test_verify_external_data_boundary_cli_parses_options_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import ExternalDataVerificationAsset
    from scripts import verify_external_data_boundary

    asset = ExternalDataVerificationAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        boundary_json_path=tmp_path / "boundary.json",
        boundary_markdown_path=tmp_path / "boundary.md",
        verification_status="final",
        candidate_count=2,
        verified_candidate_count=1,
        warning_count=0,
        dry_run=False,
        requires_confirmation=False,
        provider="fixture",
        fixture_path=tmp_path / "fixtures.yaml",
        planned_reads=[str(tmp_path / "boundary.json"), str(tmp_path / "fixtures.yaml")],
        planned_writes=[str(tmp_path / "boundary.json"), str(tmp_path / "boundary.md")],
        generated=True,
        already_exists=False,
        not_investment_advice=True,
    )
    captured = {}

    def fake_verify(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(
        verify_external_data_boundary,
        "verify_external_data_boundary",
        fake_verify,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_external_data_boundary.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--confirm",
            "--force",
            "--allow-partial",
            "--provider",
            "fixture",
            "--fixture-path",
            str(tmp_path / "fixtures.yaml"),
        ],
    )

    verify_external_data_boundary.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["verified_candidate_count"] == 1
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "confirm": True,
        "force": True,
        "allow_partial": True,
        "provider": "fixture",
        "fixture_path": tmp_path / "fixtures.yaml",
    }
