"""Synthetic end-to-end fixture for the verified-report public workflow.

Builds a complete set of episode artifacts in a temporary data root, then
assembles and publishes a verified research report from them. Every external
seam -- provider construction, external-data verification, stock lens
generation -- is monkeypatched to fail the test if it is reached, so the
fixture can never quietly depend on the network, a credential, or live
market data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _use_tmp_dirs(monkeypatch, tmp_path: Path) -> None:
    from podcast_ingest_core import storage
    import podcast_ingest_core.semantic_summary_smoke_review as semantic_review

    for name, directory in (
        ("AUDIO_DIR", "audio"),
        ("TRANSCRIPTS_DIR", "transcripts"),
        ("SUMMARIES_DIR", "summaries"),
        ("MENTIONS_DIR", "mentions"),
        ("REPORTS_DIR", "reports"),
        ("MAPPINGS_DIR", "mappings"),
        ("EXTERNAL_DIR", "external"),
        ("STOCK_LENS_DIR", "stock-lens"),
        ("CORPUS_DIR", "corpus"),
        ("RESEARCH_REPORTS_DIR", "research-reports"),
    ):
        monkeypatch.setattr(storage, name, tmp_path / directory, raising=False)
    monkeypatch.setattr(
        semantic_review,
        "REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
        raising=False,
    )

def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def _write_completed_artifacts(
    monkeypatch,
    tmp_path: Path,
    *,
    stock_query: str | None = None,
    with_lineage: bool = True,
) -> None:
    from podcast_ingest_core import storage

    _use_tmp_dirs(monkeypatch, tmp_path)
    title = "EP700 Alpha"
    transcript = storage.transcript_asset_paths("gooaye", "EP700", title)
    transcript.json_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        transcript.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "language": "zh",
            "segment_count": 1,
            "last_segment_end_seconds": 5.0,
            "completed": True,
            "segments": [
                {"id": 1, "start": 0.0, "end": 5.0, "text": "NVIDIA 與 AI 的本地 fixture"}
            ],
        },
    )
    transcript.text_path.write_text("private transcript sentinel", encoding="utf-8")
    transcript.srt_path.write_text("1\n00:00:00,000 --> 00:00:05,000\nfixture", encoding="utf-8")
    storage.semantic_summary_asset_path("gooaye", "EP700", title).parent.mkdir(parents=True, exist_ok=True)
    storage.semantic_summary_asset_path("gooaye", "EP700", title).write_text(
        "\n".join(
            [
                "# Semantic Summary",
                "Summary mode: semantic-llm",
                "Provider: openai-compatible",
                "Model: safe-model",
                "Transcript status: valid",
                "NVIDIA discussion [00:00:00 - 00:00:05]",
                "## Chunk Summaries",
                "reviewed fixture narrative",
            ]
        ),
        encoding="utf-8",
    )
    # Passing fixtures are produced by the same deterministic writer/neutral
    # evaluator as production, never by a hand-authored all-pass payload.
    from podcast_ingest_core.semantic_summary_smoke_review import (
        review_semantic_summary_smoke,
    )

    review = review_semantic_summary_smoke("gooaye", "EP700")
    mentions = storage.mention_asset_paths("gooaye", "EP700", title)
    _write_json(
        mentions.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "extraction_mode": "deterministic-rule-v1",
            "mentions": [
                {
                    "type": "company",
                    "text": "NVIDIA",
                    "normalized_text": "nvidia",
                    "count": 1,
                    "confidence": "rule",
                    "evidence": [
                        {
                            "segment_id": 1,
                            "start": 0.0,
                            "end": 5.0,
                            "timestamp": "[00:00:00 - 00:00:05]",
                            "text": "NVIDIA fixture",
                        }
                    ],
                }
            ],
        },
    )
    mentions.markdown_path.write_text("# mentions", encoding="utf-8")
    intelligence = storage.episode_intelligence_report_asset_paths("gooaye", "EP700", title)
    _write_json(
        intelligence.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "report_mode": "deterministic-episode-intelligence-v1",
            "report_status": "final",
            "timeline": [
                {
                    "timestamp": "[00:00:00 - 00:05:00]",
                    "evidence": [
                        {
                            "segment_id": 1,
                            "start": 0.0,
                            "end": 5.0,
                            "timestamp": "[00:00:00 - 00:00:05]",
                            "text": "NVIDIA fixture",
                        }
                    ],
                }
            ],
            "industry_clues": [],
            "macro_variables": [],
            "risks_and_uncertainties": [],
            "not_investment_advice": True,
        },
    )
    intelligence.markdown_path.write_text("# intelligence", encoding="utf-8")
    mapping = storage.industry_chain_mapping_asset_paths("gooaye", "EP700", title)
    _write_json(
        mapping.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "mapping_mode": "deterministic-industry-chain-v1",
            "mapping_status": "final",
            "industry_chain_nodes": [],
            "stock_candidates": [],
            "warnings": [],
        },
    )
    mapping.markdown_path.write_text("# mapping", encoding="utf-8")
    boundary = storage.external_data_boundary_asset_paths("gooaye", "EP700", title)
    _write_json(
        boundary.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "boundary_mode": "external-data-boundary-v1",
            "boundary_status": "final",
            "candidate_boundaries": [],
            "warnings": [],
        },
    )
    boundary.markdown_path.write_text("# boundary", encoding="utf-8")
    if stock_query:
        stock = storage.stock_lens_report_asset_paths("gooaye", stock_query)
        _write_json(
            stock.json_path,
            {
                "podcast_id": "gooaye",
                "stock_query": stock_query,
                "report_mode": "deterministic-stock-lens-v1",
                "report_status": "final",
                "input_set_lineage": [
                    {
                        "role": "industry_mapping",
                        "path": mapping.json_path.resolve().as_posix(),
                        "sha256": hashlib.sha256(mapping.json_path.read_bytes()).hexdigest(),
                    },
                    {
                        "role": "external_boundary",
                        "path": boundary.json_path.resolve().as_posix(),
                        "sha256": hashlib.sha256(boundary.json_path.read_bytes()).hexdigest(),
                    },
                ],
                "direct_podcast_evidence": [],
                "inferred_research_leads": [],
                "warnings": [],
                "not_investment_advice": True,
            },
        )
        stock.markdown_path.write_text("# stock", encoding="utf-8")
    if with_lineage:
        from podcast_ingest_core.verified_research_lineage import (
            record_current_verified_research_lineage,
        )

        proof_paths = {
            "transcript": transcript.json_path,
            "semantic_summary": storage.semantic_summary_asset_path("gooaye", "EP700", title),
            "semantic_review": review.review_json_path,
            "mentions": mentions.json_path,
            "intelligence": intelligence.json_path,
            "industry_mapping": mapping.json_path,
            "external_boundary": boundary.json_path,
        }
        if stock_query:
            proof_paths["stock_lens"] = storage.stock_lens_report_asset_paths(
                "gooaye", stock_query
            ).json_path
        generation_proofs = {
            role: {
                "expected_path": path.resolve().as_posix(),
                "pre_sha256": None,
                "post_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "execution": "external_selector" if role == "transcript" else "generated",
            }
            for role, path in proof_paths.items()
        }
        record_current_verified_research_lineage(
            "gooaye",
            "EP700",
            stock_query=stock_query,
            include_fixture_verification=False,
            summary_options={
                "summary_mode": "semantic-llm",
                "requested_provider": "openai-compatible",
                "requested_model": None,
                "requested_base_url_identity_sha256": None,
                "requested_chunk_seconds": 600,
                "requested_max_segments_per_chunk": 120,
            },
            generation_proofs=generation_proofs,
        )


def _independent_source_digest(assembly) -> str:
    """Reimplement the public source-digest contract without Core helpers."""
    canonical = {
        "schema_version": "latest-episode-verified-research-report-v1",
        "podcast_id": assembly.podcast_id,
        "episode_ref": assembly.episode_ref,
        "options": {
            "stock_query": assembly.stock_query,
            "include_fixture_verification": assembly.include_fixture_verification,
            "verification_scope": "local_artifact_and_fixture",
        },
        "sources": [
            {
                "role": source.role,
                "path": source.path.resolve(strict=False).as_posix(),
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
            }
            for source in assembly.source_artifacts
        ],
    }
    return hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record_lineage(*, stock_query: str) -> None:
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_lineage import record_current_verified_research_lineage

    title = "EP700 Alpha"
    paths = {
        "transcript": storage.transcript_asset_paths("gooaye", "EP700", title).json_path,
        "semantic_summary": storage.semantic_summary_asset_path("gooaye", "EP700", title),
        "mentions": storage.mention_asset_paths("gooaye", "EP700", title).json_path,
        "intelligence": storage.episode_intelligence_report_asset_paths("gooaye", "EP700", title).json_path,
        "industry_mapping": storage.industry_chain_mapping_asset_paths("gooaye", "EP700", title).json_path,
        "external_boundary": storage.external_data_boundary_asset_paths("gooaye", "EP700", title).json_path,
        "stock_lens": storage.stock_lens_report_asset_paths("gooaye", stock_query).json_path,
    }
    from podcast_ingest_core.semantic_review_artifact import inspect_semantic_review
    from podcast_ingest_core.semantic_summary_smoke_review import REPORTS_DIR
    review = inspect_semantic_review("gooaye", "EP700", semantic_summary_path=paths["semantic_summary"], review_reports_dir=REPORTS_DIR)
    assert review.review_path is not None
    paths["semantic_review"] = review.review_path
    record_current_verified_research_lineage(
        "gooaye", "EP700", stock_query=stock_query, include_fixture_verification=False,
        generation_proofs={role: {"expected_path": path.resolve().as_posix(), "pre_sha256": None, "post_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "execution": "external_selector" if role == "transcript" else "generated"} for role, path in paths.items()},
        summary_options={"summary_mode": "semantic-llm", "requested_provider": "openai-compatible", "requested_model": None, "requested_base_url_identity_sha256": None, "requested_chunk_seconds": 600, "requested_max_segments_per_chunk": 120},
    )


def run_verified_report_public_workflow(monkeypatch, tmp_path: Path) -> None:
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import assemble_verified_research_report, publish_verified_research_report_bundle

    # Guards are installed before fixture preparation: no network, provider
    # constructor, external verifier, market lookup, or ambient config reader
    # may become an invisible fixture dependency.
    def forbidden(*_args, **_kwargs):
        pytest.fail("product regression crossed an external/provider/config seam")

    monkeypatch.setattr("podcast_ingest_core.llm_provider.create_provider", forbidden)
    monkeypatch.setattr("podcast_ingest_core.llm_provider.OpenAICompatibleProvider", forbidden)
    monkeypatch.setattr("podcast_ingest_core.external_data_verification.verify_external_data_boundary", forbidden)
    monkeypatch.setattr("podcast_ingest_core.stock_lens.generate_stock_lens_report", forbidden)
    _write_completed_artifacts(monkeypatch, tmp_path, stock_query="NVDA")
    stock_path = storage.stock_lens_report_asset_paths("gooaye", "NVDA").json_path
    stock = json.loads(stock_path.read_text(encoding="utf-8"))
    stock.update({"direct_podcast_evidence": [{"episode_ref": "EP700", "title": "EP700 Alpha", "company_name": "NVIDIA", "tickers": ["NVDA"], "relation": "AI supplier", "relation_type": "supplier", "evidence_status": "podcast_explicit", "verification_status": "podcast_evidence", "evidence": [{"timestamp": "[00:00:00 - 00:00:05]", "segment_id": 1, "text": "fixture"}], "external_boundary": {"external_verification_status": "not_requested", "source_status": "not_fetched", "data_date": None, "required_external_checks": []}}], "inferred_research_leads": [{"episode_ref": "EP700", "company_name": "NVIDIA", "tickers": ["NVDA"], "relation": "AI inference", "relation_type": "research_lead", "evidence_status": "inferred_from_industry", "verification_status": "needs_verification", "external_boundary": {"external_verification_status": "not_requested", "source_status": "not_fetched", "data_date": None}}], "external_verification_needs": [{"company_name": "NVIDIA", "external_verification_status": "not_requested", "source_status": "not_fetched", "data_date": None, "required_external_checks": []}]})
    stock_path.write_text(json.dumps(stock), encoding="utf-8")
    _record_lineage(stock_query="NVDA")

    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query="NVDA")
    first = publish_verified_research_report_bundle(assembly)
    reused = publish_verified_research_report_bundle(assembly)

    assert first.reused is False and reused.reused is True
    assert assembly.report_payload["not_investment_advice"] is True
    appendix = assembly.report_payload["stock_query_appendix"]
    assert appendix["direct_podcast_evidence"][0]["classification"] == "verified_podcast_fact"
    assert appendix["direct_podcast_evidence"][0]["provenance"][0]["timestamp"] == "[00:00:00 - 00:00:05]"
    assert appendix["direct_podcast_evidence"][0]["external_verification"]["external_verification_status"] == "not_requested"
    assert appendix["direct_podcast_evidence"][0]["external_verification"]["source_status"] == "not_fetched"
    assert appendix["inferred_research_leads"][0]["classification"] == "deterministic_inference"
    assert appendix["inferred_research_leads"][0]["verification_status"] == "needs_verification"
    assert appendix["verification_details"][0]["classification"] == "external_status"
    assert appendix["verification_details"][0]["external_verification_status"] == "not_requested"
    assert appendix["verification_details"][0]["source_status"] == "not_fetched"
    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_digest"] == first.source_digest
    assert _independent_source_digest(assembly) == first.source_digest
    assert all("sha256" in item for item in manifest["source_artifacts"])
    # Each canonical source record contributes role, canonical path, SHA and
    # size.  Mutating any representative field changes the independently
    # computed digest, so an old lineage/published digest cannot match it.
    for index, source_artifact in enumerate(assembly.source_artifacts):
        class MutatedSource:
            pass
        mutated = []
        for candidate_index, candidate in enumerate(assembly.source_artifacts):
            replacement = MutatedSource()
            replacement.role = candidate.role
            replacement.path = candidate.path
            replacement.sha256 = candidate.sha256
            replacement.size_bytes = candidate.size_bytes
            if candidate_index == index:
                replacement.sha256 = hashlib.sha256((candidate.sha256 + "-mutated").encode("utf-8")).hexdigest()
            mutated.append(replacement)
        class MutatedAssembly:
            podcast_id = assembly.podcast_id
            episode_ref = assembly.episode_ref
            stock_query = assembly.stock_query
            include_fixture_verification = assembly.include_fixture_verification
            source_artifacts = mutated
        assert _independent_source_digest(MutatedAssembly()) != first.source_digest, source_artifact.role
    stock_path.write_text(stock_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(Exception):
        assemble_verified_research_report("gooaye", "EP700", stock_query="NVDA")
