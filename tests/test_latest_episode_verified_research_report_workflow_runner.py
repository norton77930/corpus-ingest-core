"""Focused contracts for SPEC 018 latest verified research report workflow."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def _manifest(root: Path) -> dict[str, tuple[str, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


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


def _ready_result() -> SimpleNamespace:
    return SimpleNamespace(outcome="ready_for_semantic_summary", episode_ref="EP700", rows=[])


def test_public_contract_models_and_safe_parameter_surface():
    import podcast_ingest_core as core

    signature = inspect.signature(core.run_latest_episode_verified_research_report_workflow)
    assert list(signature.parameters) == [
        "podcast_id",
        "confirm",
        "expected_episode_ref",
        "api_cost_ack",
        "stock_query",
        "include_fixture_verification",
        "transcription_model",
        "transcription_device",
        "transcription_compute_type",
        "transcription_vad_filter",
        "semantic_provider",
        "semantic_model",
        "semantic_base_url",
        "semantic_api_key_env",
        "semantic_chunk_seconds",
        "semantic_max_segments_per_chunk",
    ]
    assert signature.parameters["confirm"].default is False
    assert signature.parameters["expected_episode_ref"].default is None
    assert signature.parameters["api_cost_ack"].default == ""
    assert core.LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError
    assert [field.name for field in fields(core.LatestEpisodeVerifiedResearchReportWorkflowRunResult)] == [
        "podcast_id", "run_mode", "confirm", "selector", "episode_ref",
        "expected_episode_ref", "outcome", "required_api_cost_ack", "report_version",
        "source_digest", "bundle_dir", "report_json_path", "report_markdown_path",
        "manifest_path", "checkpoint_path", "filters", "stage_plan", "warnings",
        "not_investment_advice",
    ]
    for forbidden in ("force", "partial", "retry", "scheduler", "provider_url", "output_path"):
        assert forbidden not in signature.parameters


def test_storage_paths_are_pure_and_preview_is_strict_zero_write(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _use_tmp_dirs(monkeypatch, tmp_path)
    paths = storage.latest_episode_verified_research_report_paths("gooaye", "EP700", "a" * 64)
    assert paths.bundle_dir == tmp_path / "research-reports" / "gooaye" / "EP700" / ("v1-" + "a" * 64)
    assert paths.checkpoint_path == tmp_path / "corpus" / "gooaye" / "verified-research" / "EP700.checkpoint.json"
    assert not (tmp_path / "research-reports").exists()
    calls = []
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda podcast_id: calls.append(podcast_id) or ("EP700", None))
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: pytest.fail("preview dispatched child"))
    before = _manifest(tmp_path)

    result = runner.run_latest_episode_verified_research_report_workflow("gooaye")

    assert calls == ["gooaye"]
    assert result.outcome == "dry_run"
    assert result.episode_ref == "EP700"
    assert result.required_api_cost_ack
    assert [step.stage for step in result.stage_plan] == [
        "deterministic_processing", "semantic_summary", "semantic_review", "research", "publish"
    ]
    assert result.bundle_dir is None and result.checkpoint_path is None
    assert _manifest(tmp_path) == before
    assert not list(tmp_path.rglob("*.part"))


def test_invalid_ack_blocks_rss_env_provider_writer_and_child_stages(monkeypatch):
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner
    from podcast_ingest_core import LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError

    calls = {name: 0 for name in ("rss", "deterministic", "semantic", "research", "publish")}
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: calls.__setitem__("rss", calls["rss"] + 1))
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: calls.__setitem__("deterministic", calls["deterministic"] + 1))
    monkeypatch.setattr(runner, "run_corpus_semantic_remediation", lambda *args, **kwargs: calls.__setitem__("semantic", calls["semantic"] + 1))
    monkeypatch.setattr(runner, "run_research_workflow", lambda *args, **kwargs: calls.__setitem__("research", calls["research"] + 1))
    monkeypatch.setattr(runner, "publish_verified_research_report_bundle", lambda *args, **kwargs: calls.__setitem__("publish", calls["publish"] + 1))

    with pytest.raises(LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError):
        runner.run_latest_episode_verified_research_report_workflow(
            "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack="wrong"
        )

    assert calls == {name: 0 for name in calls}


def test_confirmed_drift_is_approval_boundary_rejection_with_strict_zero_writes(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _use_tmp_dirs(monkeypatch, tmp_path)
    calls = {"latest": 0, "deterministic": 0}
    monkeypatch.setattr(
        runner,
        "_resolve_latest_episode",
        lambda podcast_id: (calls.__setitem__("latest", calls["latest"] + 1) or "EP701", None),
    )
    monkeypatch.setattr(
        runner,
        "_run_pinned_deterministic_workflow",
        lambda *args, **kwargs: calls.__setitem__("deterministic", calls["deterministic"] + 1),
    )
    before = _manifest(tmp_path)

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result.outcome == "rejected"
    assert result.episode_ref == "EP701"
    assert calls == {"latest": 1, "deterministic": 0}
    assert result.checkpoint_path is None
    assert _manifest(tmp_path) == before
    assert not list(tmp_path.rglob("*.claim"))
    assert not list(tmp_path.rglob("*.staging"))


def test_review_passed_runs_pinned_deterministic_research_once_with_fixed_options_and_publishes(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path, stock_query="NVDA")
    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    calls: dict[str, object] = {"latest": 0, "semantic": 0}
    monkeypatch.setattr(
        runner,
        "_resolve_latest_episode",
        lambda podcast_id: (calls.__setitem__("latest", int(calls["latest"]) + 1) or "EP700", None),
    )
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result())
    monkeypatch.setattr(
        runner,
        "run_corpus_semantic_remediation",
        lambda *args, **kwargs: calls.__setitem__("semantic", int(calls["semantic"]) + 1),
    )
    captured = {}
    monkeypatch.setattr(
        runner,
        "run_research_workflow",
        lambda *args, **kwargs: captured.update(kwargs) or SimpleNamespace(workflow_status="completed"),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
        stock_query="NVDA",
    )

    assert result.outcome == "completed"
    assert calls == {"latest": 1, "semantic": 0}
    assert captured == {
        "stock_query": "NVDA", "confirm": True, "force": False, "allow_partial": False,
        "include_semantic_summary": False, "include_stock_lens_synthesis": False,
        "include_external_data_verification": False,
    }
    assert result.manifest_path is not None and result.manifest_path.exists()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_digest"] == result.source_digest
    assert manifest["bundle_files"]["report.json"]["sha256"]
    report = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert report["stock_query_appendix"]["scope"] == "podcast_wide"
    assert report["podcast_evidence_timeline"][0]["segment_id"] == 1
    assert "private transcript sentinel" not in result.report_markdown_path.read_text(encoding="utf-8")


def test_missing_summary_runs_summary_then_review_once_and_requires_exact_pass(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    from podcast_ingest_core import storage
    storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha").unlink()
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    for path in review_dir.glob("*"):
        path.unlink()
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda podcast_id: ("EP700", None))
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result())
    calls: list[str] = []

    def semantic(*args, **kwargs):
        calls.append(kwargs["action"])
        if kwargs["action"] == "semantic_summary":
            storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha").write_text(
                "Summary mode: semantic-llm\nProvider: safe\nModel: safe\nTranscript status: valid\n[00:00:00 - 00:00:05]\n## Chunk Summaries",
                encoding="utf-8",
            )
        else:
            from podcast_ingest_core.semantic_summary_smoke_review import (
                review_semantic_summary_smoke,
            )

            review_semantic_summary_smoke("gooaye", "EP700")
        return SimpleNamespace(episode_ref="EP700", rows=[SimpleNamespace(status="executed")])

    monkeypatch.setattr(runner, "run_corpus_semantic_remediation", semantic)
    monkeypatch.setattr(runner, "run_research_workflow", lambda *args, **kwargs: SimpleNamespace(workflow_status="completed"))

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result.outcome == "completed"
    assert calls == ["semantic_summary", "semantic_review"]


@pytest.mark.parametrize(
    "review_defect", ("missing_hash", "stale_hash", "forged_payload")
)
def test_stale_passed_review_is_deterministically_rereviewed_before_research(
    monkeypatch, tmp_path, review_defect
):
    """SPEC 018 re-reviews its own stale or forged authenticity deficits once."""
    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.corpus_index as corpus_index
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(corpus_index, "SEMANTIC_REVIEW_REPORTS_DIR", review_dir)
    existing_review = next(review_dir.glob("*.json"))
    existing_payload = json.loads(existing_review.read_text(encoding="utf-8"))
    if review_defect == "missing_hash":
        existing_payload.pop("semantic_summary_sha256")
    elif review_defect == "stale_hash":
        existing_payload["semantic_summary_sha256"] = "0" * 64
    else:
        existing_payload["review_boundary"] = "forged-review-boundary"
    existing_review.write_text(json.dumps(existing_payload, ensure_ascii=False), encoding="utf-8")
    existing_bytes = existing_review.read_bytes()

    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    monkeypatch.setattr(
        runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result()
    )
    research_calls = []
    monkeypatch.setattr(
        runner,
        "run_research_workflow",
        lambda *args, **kwargs: research_calls.append((args, kwargs))
        or SimpleNamespace(workflow_status="completed"),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    review_paths = sorted(review_dir.glob("*.semantic-review*.json"))
    new_review_paths = [path for path in review_paths if path != existing_review]
    assert result.outcome == "completed"
    assert existing_review.read_bytes() == existing_bytes
    assert len(new_review_paths) == 1
    new_review = json.loads(new_review_paths[0].read_text(encoding="utf-8"))
    assert new_review["review_status"] == "passed"
    assert new_review["semantic_summary_sha256"] == hashlib.sha256(summary_path.read_bytes()).hexdigest()
    assert research_calls
    assert result.manifest_path is not None and result.manifest_path.exists()


def test_stale_passed_review_with_failed_rereview_returns_bounded_blocked(
    monkeypatch, tmp_path
):
    """A real deterministic rereview failure never becomes a workflow failure."""
    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.corpus_index as corpus_index
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(corpus_index, "SEMANTIC_REVIEW_REPORTS_DIR", review_dir)
    existing_review = next(review_dir.glob("*.json"))
    existing_payload = json.loads(existing_review.read_text(encoding="utf-8"))
    existing_payload.pop("semantic_summary_sha256")
    existing_review.write_text(json.dumps(existing_payload, ensure_ascii=False), encoding="utf-8")
    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8") + "\n- Buy ACME now",
        encoding="utf-8",
    )
    _record_current_018_lineage(roles=("semantic_summary",))

    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    monkeypatch.setattr(
        runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result()
    )
    monkeypatch.setattr(
        runner,
        "run_research_workflow",
        lambda *args, **kwargs: pytest.fail("research must not run after failed rereview"),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    review_paths = sorted(review_dir.glob("*.semantic-review*.json"))
    new_review_paths = [path for path in review_paths if path != existing_review]
    assert result.outcome == "blocked"
    assert [(step.stage, step.status) for step in result.stage_plan] == [
        ("deterministic_processing", "completed"),
        ("semantic_summary", "reused"),
        ("semantic_review", "blocked"),
    ]
    assert len(new_review_paths) == 1
    assert json.loads(new_review_paths[0].read_text(encoding="utf-8"))["review_status"] == "failed"


@pytest.mark.parametrize("review_status", ["failed", "blocked"])
def test_nonpassed_review_stops_before_research_and_publish(monkeypatch, tmp_path, review_status):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summary_smoke_review import (
        review_semantic_summary_smoke,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    summary = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    if review_status == "failed":
        summary.write_text(summary.read_text(encoding="utf-8") + "\nBuy ACME now", encoding="utf-8")
        _record_current_018_lineage(roles=("semantic_summary",))
        review_semantic_summary_smoke("gooaye", "EP700")
    else:
        # An unreadable canonical summary blocks before review execution; this is
        # the authentic blocked form rather than a forged blocked payload.
        summary.write_bytes(b"\xff")
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda podcast_id: ("EP700", None))
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result())
    monkeypatch.setattr(runner, "run_corpus_semantic_remediation", lambda *args, **kwargs: pytest.fail("review must not be retried"))
    monkeypatch.setattr(runner, "run_research_workflow", lambda *args, **kwargs: pytest.fail("research must not run"))
    monkeypatch.setattr(runner, "publish_verified_research_report_bundle", lambda *args, **kwargs: pytest.fail("publish must not run"))

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result.outcome == "blocked"


def test_bundle_reuses_identical_digest_and_fails_closed_on_conflicting_final(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    sources = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    first = publish_verified_research_report_bundle(sources)
    second = publish_verified_research_report_bundle(sources)
    assert first.reused is False
    assert second.reused is True
    assert first.bundle_dir == second.bundle_dir
    (first.bundle_dir / "report.json").write_text("conflict", encoding="utf-8")
    with pytest.raises(VerifiedResearchReportInputError):
        publish_verified_research_report_bundle(sources)
    assert not list((storage.RESEARCH_REPORTS_DIR / "gooaye" / "EP700").glob("*.staging"))


def test_assembler_rejects_timestampless_verified_evidence_and_source_mutation(monkeypatch, tmp_path):
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    intelligence = next((tmp_path / "reports" / "gooaye").glob("*.json"))
    payload = json.loads(intelligence.read_text(encoding="utf-8"))
    payload["timeline"][0]["evidence"][0]["timestamp"] = ""
    intelligence.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(VerifiedResearchReportInputError):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)

    _write_completed_artifacts(monkeypatch, tmp_path)
    sources = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    sources.source_artifacts[0].path.write_text("changed after assembly", encoding="utf-8")
    with pytest.raises(VerifiedResearchReportInputError):
        publish_verified_research_report_bundle(sources)


def test_manifest_preserves_safe_windows_local_source_paths(monkeypatch, tmp_path):
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    bundle = publish_verified_research_report_bundle(assembly)

    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    source_paths = {item["role"]: item["path"] for item in manifest["source_artifacts"]}
    assert source_paths["transcript"] == assembly.source_artifacts[0].path.as_posix()


def test_complete_matching_bundle_is_adopted_without_rerunning_children(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    publish_verified_research_report_bundle(
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    )
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda podcast_id: ("EP700", None))
    monkeypatch.setattr(
        runner,
        "_run_pinned_deterministic_workflow",
        lambda *args, **kwargs: pytest.fail("complete matching bundle must be adopted"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_semantic_remediation",
        lambda *args, **kwargs: pytest.fail("complete matching bundle must not run semantic child"),
    )
    monkeypatch.setattr(
        runner,
        "run_research_workflow",
        lambda *args, **kwargs: pytest.fail("complete matching bundle must not run research"),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.outcome == "reused"
    assert result.source_digest
    assert [step.status for step in result.stage_plan] == ["reused"]


def test_checkpoint_failure_after_publish_returns_bundle_with_bounded_warning(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    from podcast_ingest_core import LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda podcast_id: ("EP700", None))
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result())
    monkeypatch.setattr(
        runner,
        "run_research_workflow",
        lambda *args, **kwargs: SimpleNamespace(workflow_status="completed"),
    )
    calls = {"count": 0}

    def fail_final_checkpoint(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 3:
            raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                "checkpoint write failed"
            )

    monkeypatch.setattr(runner, "_write_checkpoint", fail_final_checkpoint)

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.outcome == "completed"
    assert result.bundle_dir is not None and result.bundle_dir.exists()
    assert [(warning.scope, warning.message) for warning in result.warnings] == [
        ("checkpoint", "verified report bundle published but checkpoint update failed")
    ]


def test_existing_bundle_rejects_coordinated_report_manifest_tampering_and_extra_files(monkeypatch, tmp_path):
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    bundle = publish_verified_research_report_bundle(assembly)
    report = json.loads(bundle.report_json_path.read_text(encoding="utf-8"))
    report["episode_identity"]["completion_status"] = "tampered"
    bundle.report_json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    manifest["bundle_files"]["report.json"] = {
        "sha256": hashlib.sha256(bundle.report_json_path.read_bytes()).hexdigest(),
        "size_bytes": bundle.report_json_path.stat().st_size,
    }
    bundle.manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )

    with pytest.raises(VerifiedResearchReportInputError):
        publish_verified_research_report_bundle(assembly)

    bundle.report_json_path.write_text(
        json.dumps(assembly.report_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    bundle.manifest_path.write_text("{}", encoding="utf-8")
    (bundle.bundle_dir / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(VerifiedResearchReportInputError):
        publish_verified_research_report_bundle(assembly)


def test_adoption_requires_valid_transcript_complete_output_contract(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    publish_verified_research_report_bundle(
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    )
    storage.find_transcript_asset_paths("gooaye", "EP700").text_path.unlink()

    assert runner._adopt_complete_bundle("gooaye", "EP700", None) is None


def test_assembler_rejects_stale_or_spoofed_semantic_review_hash(monkeypatch, tmp_path):
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    review_path = next(review_dir.glob("*.json"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review.pop("semantic_summary_sha256")
    review_path.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(VerifiedResearchReportInputError):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)

    review["semantic_summary_sha256"] = "0" * 64
    review_path.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(VerifiedResearchReportInputError):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)

    review["semantic_summary_sha256"] = hashlib.sha256(
        (tmp_path / "summaries" / "gooaye" / "EP700__EP700_Alpha.semantic.md").read_bytes()
    ).hexdigest()
    spoof_path = review_dir / "spoof__gooaye__EP700.semantic-review.json"
    _write_json(spoof_path, review)
    with pytest.raises(VerifiedResearchReportInputError):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


def test_secret_bearing_summary_cannot_be_assembled_or_published(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    summary = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    summary.write_text(
        "Summary mode: semantic-llm\nAWS_SECRET_ACCESS_KEY=not-a-real-secret",
        encoding="utf-8",
    )

    with pytest.raises(VerifiedResearchReportInputError):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


def test_publish_rechecks_sources_after_staging_before_atomic_rename(monkeypatch, tmp_path):
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    original_verify = report._verify_staged_bundle

    def mutate_source_after_staging(staging_dir, staged_assembly):
        original_verify(staging_dir, staged_assembly)
        staged_assembly.source_artifacts[0].path.write_text("mutated", encoding="utf-8")

    monkeypatch.setattr(report, "_verify_staged_bundle", mutate_source_after_staging)
    with pytest.raises(VerifiedResearchReportInputError):
        publish_verified_research_report_bundle(assembly)


def test_summary_stage_exception_returns_bounded_terminal_result(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    from podcast_ingest_core import storage
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha").unlink()
    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result())
    monkeypatch.setattr(
        runner,
        "run_corpus_semantic_remediation",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("password=not-a-real-secret")),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result.outcome == "failed"
    assert result.stage_plan[-1].stage == "semantic_summary"
    assert result.stage_plan[-1].failure_category == "RuntimeError"
    assert "password=" not in result.stage_plan[-1].reason


def test_checkpoint_merges_valid_history_and_records_terminal_bundle_reference(tmp_path):
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "schema_version": "latest-episode-verified-research-report-v1",
                "podcast_id": "gooaye",
                "episode_ref": "EP700",
                "stage_history": [{"stage": "deterministic_processing", "status": "completed"}],
                "terminal_outcome": "in_progress",
                "not_investment_advice": True,
            }
        ),
        encoding="utf-8",
    )

    runner._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "publish", "status": "completed"}],
        source_digest="a" * 64,
        report_version="v1-" + "a" * 64,
        terminal_outcome="completed",
        bundle_references={"manifest_path": "data/research-reports/gooaye/EP700/manifest.json"},
    )

    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["stage_history"] == [
        {"stage": "deterministic_processing", "status": "completed"},
        {"stage": "publish", "status": "completed"},
    ]
    assert payload["terminal_outcome"] == "completed"
    assert payload["bundle_references"]["manifest_path"].endswith("manifest.json")
    assert not list(tmp_path.glob("*.part"))


def test_fixture_verification_changes_canonical_digest_and_manifest_options(monkeypatch, tmp_path):
    from podcast_ingest_core.verified_research_report import assemble_verified_research_report

    _write_completed_artifacts(monkeypatch, tmp_path)
    without_fixture = assemble_verified_research_report(
        "gooaye", "EP700", stock_query=None, include_fixture_verification=False
    )
    _mark_boundary_fixture_verified(monkeypatch, tmp_path)
    _record_current_018_lineage(include_fixture_verification=True)
    with_fixture = assemble_verified_research_report(
        "gooaye", "EP700", stock_query=None, include_fixture_verification=True
    )

    assert without_fixture.source_digest != with_fixture.source_digest
    assert with_fixture.report_payload["assembly_options"]["include_fixture_verification"] is True


def test_red_identical_timestamped_rereview_at_new_path_creates_a_new_auditable_bundle(
    monkeypatch, tmp_path
):
    """Path-distinct authentic review provenance cannot conflict forever with v1."""
    from podcast_ingest_core.semantic_summary_smoke_review import review_semantic_summary_smoke
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    first_assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    first_bundle = publish_verified_research_report_bundle(first_assembly)
    first_review = next(
        source for source in first_assembly.source_artifacts if source.role == "semantic_review"
    )

    rereview = review_semantic_summary_smoke("gooaye", "EP700")
    _record_current_018_lineage()
    second_assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    second_review = next(
        source for source in second_assembly.source_artifacts if source.role == "semantic_review"
    )
    second_bundle = publish_verified_research_report_bundle(second_assembly)

    assert rereview.review_json_path == second_review.path
    assert first_review.path != second_review.path
    assert first_review.raw_bytes == second_review.raw_bytes
    assert first_assembly.source_digest != second_assembly.source_digest
    assert first_bundle.bundle_dir != second_bundle.bundle_dir
    assert second_bundle.reused is False
    manifest = json.loads(second_bundle.manifest_path.read_text(encoding="utf-8"))
    assert next(
        item["path"] for item in manifest["source_artifacts"] if item["role"] == "semantic_review"
    ) == second_review.path.as_posix()


def test_public_filters_and_result_serialization_reject_or_scrub_unsafe_values(monkeypatch):
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner
    from podcast_ingest_core import LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError

    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    with pytest.raises(LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError):
        runner.run_latest_episode_verified_research_report_workflow(
            "gooaye", transcription_device="credential=not-a-real-secret"
        )

    dry_run = runner.run_latest_episode_verified_research_report_workflow("gooaye")
    tainted = replace(
        dry_run,
        stage_plan=[
            replace(
                dry_run.stage_plan[0],
                reason="token=not-a-real-secret",
                planned_reads=[object()],
            )
        ],
    )
    serialized = runner.result_to_dict(tainted)
    assert json.dumps(serialized, ensure_ascii=False)
    assert "not-a-real-secret" not in json.dumps(serialized)


def test_report_retains_sanitized_evidence_and_readable_stock_appendix(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import assemble_verified_research_report

    _write_completed_artifacts(monkeypatch, tmp_path, stock_query="NVDA")
    stock_path = storage.stock_lens_report_asset_paths("gooaye", "NVDA").json_path
    stock = json.loads(stock_path.read_text(encoding="utf-8"))
    direct_evidence = {
        "episode_ref": "EP700",
        "title": "EP700 Alpha",
        "company_name": "NVIDIA",
        "tickers": ["NVDA"],
        "relation": "AI supplier",
        "relation_type": "supplier",
        "evidence_status": "podcast_explicit",
        "verification_status": "podcast_evidence",
        "evidence": [{"timestamp": "[00:00:00 - 00:00:05]", "segment_id": 1, "text": "NVIDIA fixture"}],
        "external_boundary": {"external_verification_status": "not_requested", "source_status": "not_fetched", "data_date": None, "required_external_checks": ["revenue"]},
    }
    inferred_lead = {**direct_evidence, "company_name": "Related Company", "evidence_status": "inferred_from_industry", "verification_status": "needs_verification", "evidence": []}
    stock.update(
        {
            "direct_podcast_evidence": [direct_evidence],
            "inferred_research_leads": [inferred_lead],
            "external_verification_needs": [{"company_name": "NVIDIA", "external_verification_status": "not_requested", "source_status": "not_fetched", "data_date": None, "required_external_checks": ["revenue"]}],
        }
    )
    stock_path.write_text(json.dumps(stock), encoding="utf-8")
    _record_current_018_lineage(stock_query="NVDA")

    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query="NVDA")

    assert assembly.report_payload["podcast_evidence_timeline"][0]["evidence"] == "NVIDIA fixture"
    appendix = assembly.report_payload["stock_query_appendix"]
    assert appendix["direct_podcast_evidence"][0]["classification"] == "verified_podcast_fact"
    assert appendix["direct_podcast_evidence"][0]["provenance"][0]["segment_id"] == 1
    assert appendix["inferred_research_leads"][0]["classification"] == "deterministic_inference"
    assert appendix["verification_details"][0]["classification"] == "external_status"
    assert "NVIDIA fixture" in assembly.report_markdown


def test_destination_race_reuses_only_a_matching_bundle(monkeypatch, tmp_path):
    from pathlib import Path
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    original_replace = Path.replace

    def create_matching_race_destination(staging_dir, destination):
        if staging_dir.name.startswith(".stage-"):
            destination.mkdir(parents=True, exist_ok=False)
            report_json = destination / "report.json"
            report_markdown = destination / "report.md"
            report_json.write_bytes(report._canonical_report_json_bytes(assembly))
            report_markdown.write_bytes(assembly.report_markdown.encode("utf-8"))
            (destination / "manifest.json").write_bytes(
                json.dumps(
                    report._manifest_payload(assembly, report_json, report_markdown),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ).encode("utf-8")
            )
            raise FileExistsError("destination raced")
        return original_replace(staging_dir, destination)

    monkeypatch.setattr(Path, "replace", create_matching_race_destination)
    bundle = publish_verified_research_report_bundle(assembly)

    assert bundle.reused is True


def test_assembly_uses_one_immutable_source_snapshot_across_parse_safety_and_digest(
    monkeypatch, tmp_path
):
    """A disk mutation after the first source read cannot mix parsed and hashed bytes."""
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core import storage

    _write_completed_artifacts(monkeypatch, tmp_path)
    transcript_path = storage.transcript_asset_paths("gooaye", "EP700", "EP700 Alpha").json_path
    original_bytes = transcript_path.read_bytes()
    mutated_payload = json.loads(original_bytes)
    mutated_payload["title"] = "EP700 Mutated"
    original_read_bytes = Path.read_bytes
    transcript_reads = 0

    def snapshot_then_mutate(path):
        nonlocal transcript_reads
        raw = original_read_bytes(path)
        if path == transcript_path:
            transcript_reads += 1
        # Lineage inspection is a pre-source read.  Mutate after the assembler
        # takes its immutable transcript snapshot, rather than before it can
        # establish the trusted selector.
        if path == transcript_path and transcript_reads == 2:
            path.write_text(json.dumps(mutated_payload), encoding="utf-8")
        return raw

    monkeypatch.setattr(Path, "read_bytes", snapshot_then_mutate)

    assembly = report.assemble_verified_research_report("gooaye", "EP700", stock_query=None)

    transcript_source = next(
        source for source in assembly.source_artifacts if source.role == "transcript"
    )
    assert assembly.report_payload["episode_identity"]["title"] == "EP700 Alpha"
    assert transcript_source.sha256 == hashlib.sha256(original_bytes).hexdigest()
    assert transcript_source.size_bytes == len(original_bytes)


def test_reuse_revalidates_source_snapshot_after_bundle_comparison(monkeypatch, tmp_path):
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    publish_verified_research_report_bundle(assembly)
    source_path = storage.transcript_asset_paths("gooaye", "EP700", "EP700 Alpha").json_path
    original_compare = report._existing_bundle_matches

    def matching_then_mutate(paths, compared_assembly):
        matched = original_compare(paths, compared_assembly)
        source_path.write_text("changed during reuse comparison", encoding="utf-8")
        return matched

    monkeypatch.setattr(report, "_existing_bundle_matches", matching_then_mutate)

    with pytest.raises(VerifiedResearchReportInputError, match="changed during assembly"):
        publish_verified_research_report_bundle(assembly)


def test_destination_race_revalidates_source_snapshot_before_success(monkeypatch, tmp_path):
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    source_path = storage.transcript_asset_paths("gooaye", "EP700", "EP700 Alpha").json_path
    original_replace = Path.replace

    def create_matching_destination_then_mutate(staging_dir, destination):
        if staging_dir.name.startswith(".stage-"):
            destination.mkdir(parents=True, exist_ok=False)
            report_json = destination / "report.json"
            report_markdown = destination / "report.md"
            report_json.write_bytes(report._canonical_report_json_bytes(assembly))
            report_markdown.write_bytes(assembly.report_markdown.encode("utf-8"))
            (destination / "manifest.json").write_bytes(
                json.dumps(
                    report._manifest_payload(assembly, report_json, report_markdown),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ).encode("utf-8")
            )
            source_path.write_text("changed during destination race", encoding="utf-8")
            raise FileExistsError("destination raced")
        return original_replace(staging_dir, destination)

    monkeypatch.setattr(Path, "replace", create_matching_destination_then_mutate)

    with pytest.raises(VerifiedResearchReportInputError, match="changed during assembly"):
        publish_verified_research_report_bundle(assembly)


def test_review_inspector_rejects_timestamped_matching_hash_forgery(monkeypatch, tmp_path):
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core import storage

    _write_completed_artifacts(monkeypatch, tmp_path)
    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    review_path = next((tmp_path / "evals" / "research-llm-smoke" / "reports").glob("*.json"))
    review_path.write_text(
        json.dumps(
            {
                "review_mode": "forged-review-mode",
                "review_boundary": "forged-boundary",
                "podcast_id": "gooaye",
                "episode_ref": "EP700",
                "review_status": "passed",
                "semantic_summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                "check_count": 8,
                "failed_check_count": 0,
                "warning_count": 0,
                "blocked_check_count": 0,
                "checks": [
                    {"name": name, "status": "pass", "message": "forged"}
                    for name in (
                        "semantic_summary_exists",
                        "secret_leak",
                        "traceback_leak",
                        "raw_transcript_dump",
                        "timestamp_evidence",
                        "chunk_summaries",
                        "metadata",
                        "prohibited_advice",
                    )
                ],
                "not_investment_advice_notice": True,
            }
        ),
        encoding="utf-8",
    )

    inspection = report.inspect_semantic_review(
        "gooaye", "EP700", semantic_summary_path=summary_path
    )

    assert inspection.review_status == "needs_review"


def test_checkpoint_intermediate_merge_keeps_last_successful_bundle_metadata(tmp_path):
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "schema_version": "latest-episode-verified-research-report-v1",
                "podcast_id": "gooaye",
                "episode_ref": "EP700",
                "stage_history": [{"stage": "publish", "status": "completed"}],
                "source_digest": "a" * 64,
                "report_version": "v1-" + "a" * 64,
                "terminal_outcome": "completed",
                "bundle_references": {
                    "manifest_path": "data/research-reports/gooaye/EP700/v1-a/manifest.json"
                },
                "not_investment_advice": True,
            }
        ),
        encoding="utf-8",
    )

    runner._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "inspection", "status": "completed"}],
    )

    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["source_digest"] == "a" * 64
    assert payload["report_version"] == "v1-" + "a" * 64
    assert payload["bundle_references"]["manifest_path"].endswith("manifest.json")


def test_red_reserved_generations_prevent_deterministic_stale_success_overwrite(tmp_path):
    """Interleave A=1 and B=2: B succeeds first, then stale A must not replace B."""
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    checkpoint = tmp_path / "checkpoint.json"
    older_generation = runner._reserve_invocation_generation(checkpoint, "gooaye", "EP700")
    newer_generation = runner._reserve_invocation_generation(checkpoint, "gooaye", "EP700")
    newer_digest = "b" * 64
    runner._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "research", "status": "completed"}],
        source_digest=newer_digest,
        report_version="v1-" + newer_digest,
        terminal_outcome="completed",
        bundle_references={
            "manifest_path": "data/research-reports/gooaye/EP700/v1-b/manifest.json"
        },
        invocation_generation=newer_generation,
    )
    runner._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "publish", "status": "completed"}],
        source_digest="a" * 64,
        report_version="v1-" + "a" * 64,
        terminal_outcome="completed",
        bundle_references={
            "manifest_path": "data/research-reports/gooaye/EP700/v1-a/manifest.json"
        },
        invocation_generation=older_generation,
    )

    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert (older_generation, newer_generation) == (1, 2)
    assert payload["invocation_generation"] == newer_generation
    assert payload["successful_invocation_generation"] == newer_generation
    assert payload["terminal_outcome"] == "completed"
    assert payload["source_digest"] == newer_digest
    assert payload["report_version"] == "v1-" + newer_digest
    assert payload["bundle_references"]["manifest_path"].endswith("v1-b/manifest.json")
    assert payload["stage_history"] == [
        {"stage": "research", "status": "completed"},
        {"stage": "publish", "status": "completed"},
    ]


def test_confirmed_blocked_return_finalizes_checkpoint_terminal_outcome(monkeypatch, tmp_path):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    monkeypatch.setattr(
        runner,
        "_run_pinned_deterministic_workflow",
        lambda *args, **kwargs: SimpleNamespace(outcome="blocked", episode_ref="EP700", rows=[]),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )

    payload = json.loads(result.checkpoint_path.read_text(encoding="utf-8"))
    assert result.outcome == "blocked"
    assert payload["terminal_outcome"] == "blocked"


def test_stock_appendix_preserves_production_structured_external_checks(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.stock_lens import generate_stock_lens_report
    from podcast_ingest_core.verified_research_report import assemble_verified_research_report

    _write_completed_artifacts(monkeypatch, tmp_path)
    title = "EP700 Alpha"
    mapping = storage.industry_chain_mapping_asset_paths("gooaye", "EP700", title)
    _write_json(
        mapping.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "mapping_mode": "deterministic-industry-chain-v1",
            "mapping_status": "final",
            "stock_candidates": [
                {
                    "company_name": "NVIDIA",
                    "tickers": ["NVDA"],
                    "relation": "accelerator_design",
                    "relation_type": "inferred_from_industry",
                    "evidence_status": "inferred_from_industry",
                    "verification_status": "needs_verification",
                    "evidence": [],
                }
            ],
            "industry_chain_nodes": [],
            "warnings": [],
        },
    )
    boundary = storage.external_data_boundary_asset_paths("gooaye", "EP700", title)
    _write_json(
        boundary.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": title,
            "boundary_mode": "external-data-boundary-v1",
            "boundary_status": "final",
            "candidate_boundaries": [
                {
                    "company_name": "NVIDIA",
                    "tickers": ["NVDA"],
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
                }
            ],
            "warnings": [],
        },
    )
    generate_stock_lens_report("gooaye", "NVDA")
    _record_current_018_lineage(stock_query="NVDA")

    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query="NVDA")

    appendix = assembly.report_payload["stock_query_appendix"]
    lead = appendix["inferred_research_leads"][0]
    check = appendix["verification_details"][0]["required_external_checks"][0]
    assert lead["external_verification"]["required_external_checks"][0]["data_type"] == "market_snapshot"
    assert check == {
        "data_type": "market_snapshot",
        "label": "Price, market cap, and liquidity snapshot",
        "requires_source_status": True,
        "requires_data_date": True,
    }
    assert "{'data_type'" not in assembly.report_markdown
    assert "Price, market cap, and liquidity snapshot" in assembly.report_markdown


@pytest.mark.parametrize(
    "assignment",
    ['"password": "not-a-real-secret"', "'token': 'not-a-real-secret'"],
)
def test_assembler_rejects_quoted_credential_assignments(monkeypatch, tmp_path, assignment):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8") + "\n" + assignment,
        encoding="utf-8",
    )
    review_path = next((tmp_path / "evals" / "research-llm-smoke" / "reports").glob("*.json"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["semantic_summary_sha256"] = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    review_path.write_text(json.dumps(review), encoding="utf-8")

    with pytest.raises(VerifiedResearchReportInputError, match="lineage|safety boundary"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


@pytest.mark.parametrize("authorization", ["Bearer AaBbCcDdEeFf012345", "bEaReR token_0123456789"])
def test_assembler_rejects_standard_bearer_authorization(monkeypatch, tmp_path, authorization):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8") + "\n" + authorization,
        encoding="utf-8",
    )
    review_path = next((tmp_path / "evals" / "research-llm-smoke" / "reports").glob("*.json"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["semantic_summary_sha256"] = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    review_path.write_text(json.dumps(review), encoding="utf-8")

    with pytest.raises(VerifiedResearchReportInputError, match="lineage|safety boundary"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


def test_reuse_revalidates_bundle_after_first_matching_comparison(monkeypatch, tmp_path):
    import podcast_ingest_core.verified_research_report as report
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    bundle = publish_verified_research_report_bundle(assembly)
    original_compare = report._existing_bundle_matches
    calls = 0

    def matching_then_replace_report(paths, compared_assembly):
        nonlocal calls
        matched = original_compare(paths, compared_assembly)
        calls += 1
        if calls == 1 and matched:
            paths.report_json_path.write_text("replacement after comparison", encoding="utf-8")
        return matched

    monkeypatch.setattr(report, "_existing_bundle_matches", matching_then_replace_report)

    with pytest.raises(VerifiedResearchReportInputError, match="changed before return"):
        publish_verified_research_report_bundle(assembly)
    assert bundle.report_json_path.read_text(encoding="utf-8") == "replacement after comparison"


@pytest.mark.parametrize(
    "source_name",
    ("mentions", "intelligence", "industry_mapping", "external_boundary", "stock_lens"),
)
def test_red_assembler_rejects_personalized_advice_from_every_rendered_source(
    monkeypatch, tmp_path, source_name
):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    stock_query = "NVDA" if source_name == "stock_lens" else None
    _write_completed_artifacts(monkeypatch, tmp_path, stock_query=stock_query)
    title = "EP700 Alpha"
    advice = "You should buy ACME."
    if source_name == "mentions":
        path = storage.mention_asset_paths("gooaye", "EP700", title).json_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["mentions"][0]["text"] = advice
    elif source_name == "intelligence":
        path = storage.episode_intelligence_report_asset_paths("gooaye", "EP700", title).json_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["timeline"][0]["evidence"][0]["text"] = advice
    elif source_name == "industry_mapping":
        path = storage.industry_chain_mapping_asset_paths("gooaye", "EP700", title).json_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["stock_candidates"] = [
            {
                "company_name": advice,
                "relation_type": "supplier",
                "verification_status": "needs_verification",
            }
        ]
    elif source_name == "external_boundary":
        path = storage.external_data_boundary_asset_paths("gooaye", "EP700", title).json_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["candidate_boundaries"] = [
            {
                "company_name": advice,
                "external_verification_status": "not_requested",
                "source_status": "not_fetched",
                "data_date": None,
            }
        ]
    else:
        path = storage.stock_lens_report_asset_paths("gooaye", "NVDA").json_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["direct_podcast_evidence"] = [
            {
                "company_name": "ACME",
                "tickers": ["ACME"],
                "episode_ref": "EP700",
                "relation": "fixture",
                "relation_type": "supplier",
                "evidence_status": "podcast_explicit",
                "verification_status": "podcast_evidence",
                "evidence": [
                    {
                        "timestamp": "[00:00:00 - 00:00:05]",
                        "segment_id": 1,
                        "text": advice,
                    }
                ],
                "external_boundary": {},
            }
        ]
    path.write_text(json.dumps(payload), encoding="utf-8")
    _record_current_018_lineage(stock_query=stock_query)

    with pytest.raises(VerifiedResearchReportInputError, match="safety boundary"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=stock_query)


def test_red_assembler_allows_normal_investment_disclaimer_in_rendered_source(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import assemble_verified_research_report

    _write_completed_artifacts(monkeypatch, tmp_path)
    title = "EP700 Alpha"
    path = storage.episode_intelligence_report_asset_paths("gooaye", "EP700", title).json_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    disclaimer = (
        "This report is not investment advice. No buy/sell/hold advice is provided. "
        "No target price. No guaranteed returns."
    )
    payload["timeline"][0]["evidence"][0]["text"] = disclaimer
    path.write_text(json.dumps(payload), encoding="utf-8")
    _record_current_018_lineage()

    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)

    assert assembly.report_payload["podcast_evidence_timeline"][0]["evidence"] == disclaimer


@pytest.mark.parametrize("failure_kind", ("io", "lock"))
def test_red_workflow_claim_failure_returns_bounded_terminal_result_before_children_or_publish(
    monkeypatch, tmp_path, failure_kind
):
    from contextlib import contextmanager

    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _use_tmp_dirs(monkeypatch, tmp_path)
    checkpoint_path = storage.latest_episode_verified_research_report_paths(
        "gooaye", "EP700", "0" * 64
    ).checkpoint_path
    valid_checkpoint = {
        "schema_version": runner.REPORT_SCHEMA_VERSION,
        "podcast_id": "gooaye",
        "episode_ref": "EP700",
        "stage_history": [],
        "source_digest": None,
        "report_version": None,
        "terminal_outcome": "in_progress",
        "bundle_references": {},
        "invocation_generation": 0,
        "successful_invocation_generation": None,
        "not_investment_advice": True,
    }
    if failure_kind == "unreadable":
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_bytes(b"\xff")
    elif failure_kind == "corrupt":
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text("[]", encoding="utf-8")
    elif failure_kind == "identity":
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        valid_checkpoint["podcast_id"] = "other"
        checkpoint_path.write_text(json.dumps(valid_checkpoint), encoding="utf-8")
    elif failure_kind == "generation":
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        valid_checkpoint["invocation_generation"] = True
        checkpoint_path.write_text(json.dumps(valid_checkpoint), encoding="utf-8")
    else:
        error = OSError("password=not-a-real-secret") if failure_kind == "io" else TimeoutError()

        @contextmanager
        def failing_claim(*args, **kwargs):
            raise error
            yield

        monkeypatch.setattr(runner, "exclusive_artifact_claim", failing_claim)

    calls: list[str] = []

    def unexpected_stage(*args, **kwargs):
        calls.append("unexpected")
        pytest.fail("workflow-claim failure must stop before adoption, child stages, and publication")

    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    monkeypatch.setattr(runner, "_adopt_complete_bundle", unexpected_stage)
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", unexpected_stage)
    monkeypatch.setattr(runner, "run_corpus_semantic_remediation", unexpected_stage)
    monkeypatch.setattr(runner, "run_research_workflow", unexpected_stage)
    monkeypatch.setattr(runner, "assemble_verified_research_report", unexpected_stage)
    monkeypatch.setattr(runner, "publish_verified_research_report_bundle", unexpected_stage)

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.outcome == "failed"
    assert result.checkpoint_path == checkpoint_path
    assert [(step.stage, step.status) for step in result.stage_plan] == [
        ("workflow_claim", "failed")
    ]
    assert result.stage_plan[0].failure_category in {
        "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError",
        "OSError",
        "TimeoutError",
    }
    serialized = json.dumps(runner.result_to_dict(result))
    assert "password=not-a-real-secret" not in serialized
    assert "Traceback" not in serialized
    assert calls == []


def test_red_reservation_failure_skips_finalization_and_preserves_newer_generation(
    monkeypatch, tmp_path
):
    """An unreserved invocation cannot retry or merge into a newer checkpoint."""
    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _use_tmp_dirs(monkeypatch, tmp_path)
    checkpoint_path = storage.latest_episode_verified_research_report_paths(
        "gooaye", "EP700", "0" * 64
    ).checkpoint_path
    newer_digest = "b" * 64
    checkpoint_payload = {
        "schema_version": runner.REPORT_SCHEMA_VERSION,
        "podcast_id": "gooaye",
        "episode_ref": "EP700",
        "stage_history": [{"stage": "publish", "status": "completed"}],
        "source_digest": newer_digest,
        "report_version": "v1-" + newer_digest,
        "terminal_outcome": "completed",
        "bundle_references": {
            "manifest_path": "data/research-reports/gooaye/EP700/v1-b/manifest.json"
        },
        "invocation_generation": 2,
        "successful_invocation_generation": 2,
        "not_investment_advice": True,
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(checkpoint_payload), encoding="utf-8")
    before = checkpoint_path.read_bytes()
    original_write_locked = runner._write_checkpoint_locked
    attempts: list[dict[str, object]] = []

    def fail_reservation_once(*args, **kwargs):
        attempts.append(dict(kwargs))
        if len(attempts) == 1:
            raise OSError("transient reservation write failure")
        return original_write_locked(*args, **kwargs)

    monkeypatch.setattr(runner, "_write_checkpoint_locked", fail_reservation_once)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    # Bundle inspection is intentionally before checkpoint reservation; no
    # complete bundle exists in this regression fixture.
    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args, **kwargs: None)

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.outcome == "failed"
    assert [(step.stage, step.status) for step in result.stage_plan] == [
        ("checkpoint_reservation", "failed")
    ]
    assert len(attempts) == 1
    assert checkpoint_path.read_bytes() == before


def test_red_018_rereview_converges_past_future_forged_and_rejected_candidates(
    monkeypatch, tmp_path
):
    """A new authentic review must supersede invalid higher-sorting filenames."""
    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_review_artifact import inspect_semantic_review
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    existing = next(review_dir.glob("*.semantic-review.json"))
    future_forged = review_dir / "20991231-235959__gooaye__EP700.semantic-review.json"
    forged_payload = json.loads(existing.read_text(encoding="utf-8"))
    forged_payload["review_boundary"] = "forged-review-boundary"
    forged_payload["semantic_summary_sha256"] = "0" * 64
    future_forged.write_text(json.dumps(forged_payload), encoding="utf-8")
    existing.unlink()
    existing.with_suffix(".md").unlink()
    rejected = review_dir / "future__gooaye__EP700.semantic-review.json"
    rejected.write_text("{}", encoding="utf-8")
    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")

    before = inspect_semantic_review(
        "gooaye",
        "EP700",
        semantic_summary_path=summary_path,
        review_reports_dir=review_dir,
    )
    monkeypatch.setattr(runner, "_adopt_complete_bundle", lambda *args: None)
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *args: ("EP700", None))
    monkeypatch.setattr(
        runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result()
    )
    monkeypatch.setattr(
        runner,
        "run_research_workflow",
        lambda *args, **kwargs: SimpleNamespace(workflow_status="completed"),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    after = inspect_semantic_review(
        "gooaye",
        "EP700",
        semantic_summary_path=summary_path,
        review_reports_dir=review_dir,
    )
    assert before.review_status == "needs_review"
    assert result.outcome == "completed"
    assert after.review_status == "passed"
    assert after.review_path is not None and after.review_path != future_forged
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert next(
        item["path"] for item in manifest["source_artifacts"] if item["role"] == "semantic_review"
    ) == after.review_path.as_posix()


def _record_current_018_lineage(
    podcast_id: str = "gooaye",
    episode_ref: str = "EP700",
    *,
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
    roles: tuple[str, ...] | None = None,
) -> None:
    """Create a test-only trusted 018 lineage snapshot from known fixture writes."""

    from podcast_ingest_core.verified_research_lineage import (
        record_current_verified_research_lineage,
    )

    from podcast_ingest_core import storage
    from podcast_ingest_core.canonical_transcript import (
        resolve_canonical_transcript_asset_paths,
    )
    from podcast_ingest_core.semantic_review_artifact import inspect_semantic_review
    from podcast_ingest_core.semantic_summary_smoke_review import REPORTS_DIR

    transcript = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    assert transcript is not None
    transcript_payload = json.loads(transcript.json_path.read_text(encoding="utf-8"))
    title = transcript_payload["title"]
    role_paths = {
        "transcript": transcript.json_path,
        "semantic_summary": storage.semantic_summary_asset_path(podcast_id, episode_ref, title),
        "mentions": storage.mention_asset_paths(podcast_id, episode_ref, title).json_path,
        "intelligence": storage.episode_intelligence_report_asset_paths(
            podcast_id, episode_ref, title
        ).json_path,
        "industry_mapping": storage.industry_chain_mapping_asset_paths(
            podcast_id, episode_ref, title
        ).json_path,
        "external_boundary": storage.external_data_boundary_asset_paths(
            podcast_id, episode_ref, title
        ).json_path,
    }
    review = inspect_semantic_review(
        podcast_id,
        episode_ref,
        semantic_summary_path=role_paths["semantic_summary"],
        review_reports_dir=REPORTS_DIR,
    )
    if review.review_path is not None:
        role_paths["semantic_review"] = review.review_path
    if include_fixture_verification:
        role_paths["fixture"] = storage.external_data_boundary_asset_paths(
            podcast_id, episode_ref, title
        ).json_path
    if stock_query is not None:
        role_paths["stock_lens"] = storage.stock_lens_report_asset_paths(
            podcast_id, stock_query
        ).json_path
    requested_roles = roles or tuple(role_paths)
    generation_proofs = {
        role: {
            "expected_path": role_paths[role].resolve().as_posix(),
            "pre_sha256": None,
            "post_sha256": hashlib.sha256(role_paths[role].read_bytes()).hexdigest(),
            "execution": "external_selector" if role == "transcript" else "generated",
        }
        for role in requested_roles
        if role in role_paths and role_paths[role].exists()
    }
    record_current_verified_research_lineage(
        podcast_id,
        episode_ref,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
        roles=roles,
        generation_proofs=generation_proofs,
        summary_options={
            "summary_mode": "semantic-llm",
            "requested_provider": "openai-compatible",
            "requested_model": None,
            "requested_base_url_identity_sha256": None,
            "requested_chunk_seconds": 600,
            "requested_max_segments_per_chunk": 120,
        },
    )


def _mark_boundary_fixture_verified(monkeypatch, tmp_path: Path) -> Path:
    """Install a current fixture marker without contacting an external provider."""

    from podcast_ingest_core import storage
    import podcast_ingest_core.external_data_verification as external_verification

    fixture_path = tmp_path / "fixture.yaml"
    fixture_path.write_text("candidates: []\n", encoding="utf-8")
    monkeypatch.setattr(
        external_verification,
        "DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH",
        fixture_path,
    )
    monkeypatch.setattr(
        external_verification, "PREVERIFICATION_BOUNDARIES_DIR", storage.CORPUS_DIR
    )
    boundary_path = storage.external_data_boundary_asset_paths(
        "gooaye", "EP700", "EP700 Alpha"
    ).json_path
    original_raw = boundary_path.read_bytes()
    snapshot_path = external_verification._write_preverification_boundary_snapshot(
        "gooaye", "EP700", original_raw
    )
    boundary = json.loads(original_raw)
    boundary["external_data_verification"] = {
        "verification_mode": "fixture-external-data-v1",
        "provider": "fixture",
        "fixture_path": fixture_path.resolve().as_posix(),
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "boundary_input_path": boundary_path.resolve().as_posix(),
        "boundary_input_sha256": hashlib.sha256(original_raw).hexdigest(),
        "preverification_snapshot_path": snapshot_path.resolve().as_posix(),
        "preverification_snapshot_sha256": hashlib.sha256(original_raw).hexdigest(),
        "candidate_count": 0,
        "verified_candidate_count": 0,
        "not_investment_advice": True,
    }
    boundary_path.write_text(json.dumps(boundary, ensure_ascii=False), encoding="utf-8")
    return fixture_path


def test_red_018_rejects_preexisting_artifacts_without_trusted_lineage(monkeypatch, tmp_path):
    """A legacy same-path artifact set cannot become trusted merely by existing."""

    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path, with_lineage=False)

    with pytest.raises(VerifiedResearchReportInputError, match="lineage"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


def test_red_018_transcript_bytes_mutation_invalidates_all_derived_lineage(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    _record_current_018_lineage()
    transcript = storage.transcript_asset_paths("gooaye", "EP700", "EP700 Alpha")
    transcript.json_path.write_bytes(transcript.json_path.read_bytes() + b"\n")

    with pytest.raises(VerifiedResearchReportInputError, match="lineage"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


def test_red_018_fixture_bytes_mutation_blocks_fixture_bound_assembly_and_adoption(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    fixture_path = _mark_boundary_fixture_verified(monkeypatch, tmp_path)
    _record_current_018_lineage(include_fixture_verification=True)
    assembly = assemble_verified_research_report(
        "gooaye", "EP700", stock_query=None, include_fixture_verification=True
    )
    publish_verified_research_report_bundle(assembly)
    fixture_path.write_text("candidates: []\n# changed\n", encoding="utf-8")

    with pytest.raises(VerifiedResearchReportInputError, match="fixture|lineage"):
        assemble_verified_research_report(
            "gooaye", "EP700", stock_query=None, include_fixture_verification=True
        )
    assert runner._adopt_complete_bundle(
        "gooaye", "EP700", None, include_fixture_verification=True
    ) is None


def test_red_018_upstream_mentions_mutation_invalidates_research_chain(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    _record_current_018_lineage()
    mentions = storage.mention_asset_paths("gooaye", "EP700", "EP700 Alpha").json_path
    mentions.write_bytes(mentions.read_bytes() + b"\n")

    with pytest.raises(VerifiedResearchReportInputError, match="lineage"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)


def test_red_018_stock_input_set_mutation_invalidates_stock_lens_lineage(monkeypatch, tmp_path):
    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )

    _write_completed_artifacts(monkeypatch, tmp_path, stock_query="NVDA")
    sibling_mapping = storage.industry_chain_mapping_asset_paths(
        "gooaye", "EP699", "EP699 Sibling"
    ).json_path
    sibling_boundary = storage.external_data_boundary_asset_paths(
        "gooaye", "EP699", "EP699 Sibling"
    ).json_path
    _write_json(
        sibling_mapping,
        {
            "podcast_id": "gooaye", "episode_ref": "EP699", "title": "EP699 Sibling",
            "mapping_mode": "deterministic-industry-chain-v1", "mapping_status": "final",
            "stock_candidates": [],
        },
    )
    _write_json(
        sibling_boundary,
        {
            "podcast_id": "gooaye", "episode_ref": "EP699", "title": "EP699 Sibling",
            "boundary_mode": "external-data-boundary-v1", "boundary_status": "final",
            "candidate_boundaries": [],
        },
    )
    _record_current_018_lineage(stock_query="NVDA")
    sibling_mapping.write_bytes(sibling_mapping.read_bytes() + b"\n")
    # Unused siblings are not silently part of this report's input closure.
    assemble_verified_research_report("gooaye", "EP700", stock_query="NVDA")
    storage.industry_chain_mapping_asset_paths(
        "gooaye", "EP700", "EP700 Alpha"
    ).json_path.write_bytes(
        storage.industry_chain_mapping_asset_paths(
            "gooaye", "EP700", "EP700 Alpha"
        ).json_path.read_bytes() + b"\n"
    )

    with pytest.raises(
        VerifiedResearchReportInputError,
        match="stock lens input set is stale",
    ):
        assemble_verified_research_report("gooaye", "EP700", stock_query="NVDA")


def test_red_018_adopts_valid_bundle_despite_corrupt_checkpoint(monkeypatch, tmp_path):
    """Checkpoint bytes are untrusted metadata, not a veto over a valid bundle."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    _record_current_018_lineage()
    publish_verified_research_report_bundle(
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    )
    checkpoint_path = storage.latest_episode_verified_research_report_paths(
        "gooaye", "EP700", "0" * 64
    ).checkpoint_path
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_bytes(b"not JSON")
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *_: ("EP700", None))
    monkeypatch.setattr(
        runner,
        "_run_pinned_deterministic_workflow",
        lambda *args, **kwargs: pytest.fail("valid bundle adoption must precede checkpoint recovery"),
    )

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result.outcome == "reused"
    assert result.bundle_dir is not None and result.bundle_dir.exists()


def test_red_018_same_episode_threads_hold_one_cost_boundary(monkeypatch, tmp_path):
    """Two confirmed calls for one episode may not create two semantic providers."""

    from threading import Barrier, Lock, Thread
    import time

    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _use_tmp_dirs(monkeypatch, tmp_path)
    state = {"summary": False, "review": False, "published": False}
    count_lock = Lock()
    summary_calls = 0
    barrier = Barrier(2)
    fake_bundle = SimpleNamespace(
        reused=True,
        report_version="v1-" + "a" * 64,
        source_digest="a" * 64,
        bundle_dir=tmp_path / "bundle",
        report_json_path=tmp_path / "bundle" / "report.json",
        report_markdown_path=tmp_path / "bundle" / "report.md",
        manifest_path=tmp_path / "bundle" / "manifest.json",
    )

    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *_: ("EP700", None))
    monkeypatch.setattr(runner, "_reserve_invocation_generation", lambda *args: 1)
    monkeypatch.setattr(
        runner, "_adopt_complete_bundle", lambda *args, **kwargs: fake_bundle if state["published"] else None
    )
    monkeypatch.setattr(runner, "_run_pinned_deterministic_workflow", lambda *args, **kwargs: _ready_result())
    from contextlib import contextmanager

    monkeypatch.setattr(runner, "_transcript_title", lambda *args: "EP700 Alpha")
    monkeypatch.setattr(runner, "_acquire_canonical_transcript_scope", lambda *args: None)

    @contextmanager
    def simulated_proof_scope(*args):
        committed = args[-1]
        yield lambda commit: committed.add(commit.role)

    monkeypatch.setattr(runner, "_progressive_lineage_scope", simulated_proof_scope)
    monkeypatch.setattr(runner, "_lineage_is_current", lambda *args: True)
    monkeypatch.setattr(runner, "_lineage_roles_are_current", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        runner,
        "_semantic_state",
        lambda *args: {
            "summary": "available" if state["summary"] else "missing",
            "review": "passed" if state["review"] else "missing",
        },
    )

    def semantic_child(*args, **kwargs):
        nonlocal summary_calls
        if kwargs["action"] == "semantic_summary":
            with count_lock:
                summary_calls += 1
            time.sleep(0.15)
            state["summary"] = True
        else:
            state["review"] = True
            return SimpleNamespace(
                episode_ref="EP700",
                rows=[SimpleNamespace(status="executed")],
                review_json_path=tmp_path / "review.json",
            )
        return SimpleNamespace(episode_ref="EP700", rows=[SimpleNamespace(status="executed")])

    monkeypatch.setattr(runner, "run_corpus_semantic_remediation", semantic_child)
    monkeypatch.setattr(
        runner, "run_research_workflow", lambda *args, **kwargs: SimpleNamespace(workflow_status="completed")
    )
    monkeypatch.setattr(runner, "_research_generated_current_lineage", lambda *args, **kwargs: True)
    monkeypatch.setattr(runner, "_record_lineage_roles", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner, "_record_full_lineage", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner, "assemble_verified_research_report", lambda *args, **kwargs: object())

    def publish(_assembly):
        state["published"] = True
        fake_bundle.bundle_dir.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(**{**fake_bundle.__dict__, "reused": False})

    monkeypatch.setattr(runner, "publish_verified_research_report_bundle", publish)
    results = []

    def invoke() -> None:
        barrier.wait()
        results.append(
            runner.run_latest_episode_verified_research_report_workflow(
                "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack=SEMANTIC_API_COST_ACK
            )
        )

    threads = [Thread(target=invoke), Thread(target=invoke)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not any(thread.is_alive() for thread in threads)
    assert summary_calls == 1
    assert sorted(result.outcome for result in results) == ["completed", "reused"]


def test_red_strict_transcript_resolver_rejects_ambiguous_title_variants_and_uses_seed(
    monkeypatch, tmp_path
):
    """017/018 must never derive a canonical transcript from filename sorting."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.canonical_transcript import (
        CanonicalTranscriptResolutionError,
        resolve_canonical_transcript_asset_paths,
    )

    _use_tmp_dirs(monkeypatch, tmp_path)
    for title in ("EP700 Alpha", "EP700 Corrected"):
        paths = storage.transcript_asset_paths("gooaye", "EP700", title)
        _write_json(
            paths.json_path,
            {
                "podcast_id": "gooaye", "episode_ref": "EP700", "title": title,
                "segment_count": 1, "completed": True,
                "segments": [{"id": 1, "start": 0, "end": 1, "text": "fixture"}],
            },
        )
        paths.text_path.write_text("fixture", encoding="utf-8")
        paths.srt_path.write_text("fixture", encoding="utf-8")

    with pytest.raises(CanonicalTranscriptResolutionError, match="ambiguous"):
        resolve_canonical_transcript_asset_paths("gooaye", "EP700")

    seed = storage.corpus_episode_seed_asset_path("gooaye", "EP700")
    _write_json(
        seed,
        {"podcast_id": "gooaye", "episode_ref": "EP700", "title": "EP700 Corrected"},
    )
    assert resolve_canonical_transcript_asset_paths("gooaye", "EP700").json_path == (
        storage.transcript_asset_paths("gooaye", "EP700", "EP700 Corrected").json_path
    )


def test_red_v2_lineage_without_generation_proofs_cannot_assemble_or_adopt(
    monkeypatch, tmp_path
):
    """Correct v2 hashes/options alone may not bless pre-existing report bytes."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        assemble_verified_research_report,
    )
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    sidecar = storage.CORPUS_DIR / "gooaye" / "verified-research" / "EP700.lineage.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    for artifact in payload["artifacts"].values():
        artifact.pop("generation_proof", None)
    sidecar.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(VerifiedResearchReportInputError, match="lineage"):
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    assert runner._adopt_complete_bundle("gooaye", "EP700", None) is None


def test_red_adoption_rejects_bundle_when_requested_semantic_identity_changes(
    monkeypatch, tmp_path
):
    """A bundle for request A cannot satisfy provider/model/base/chunk request B."""

    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK
    from podcast_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    publish_verified_research_report_bundle(
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    )
    monkeypatch.setattr(runner, "_resolve_latest_episode", lambda *_: ("EP700", None))

    result = runner.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack=SEMANTIC_API_COST_ACK,
        semantic_provider="request-b-provider",
        semantic_model="request-b-model",
        semantic_base_url="https://request-b.example.test/v1",
        semantic_chunk_seconds=601,
        semantic_max_segments_per_chunk=121,
    )

    assert result.outcome != "reused"


def test_red_fixture_enablement_records_in_place_boundary_and_fixture_proofs(
    monkeypatch, tmp_path
):
    """A trusted unverified boundary may become fixture-verified in place once."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary
    from podcast_ingest_core.generation_proof import notify_child_artifact_committed
    from podcast_ingest_core.verified_research_lineage import (
        validate_current_verified_research_lineage,
    )
    import podcast_ingest_core.external_data_verification as verification
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    fixture_path = tmp_path / "fixture.yaml"
    fixture_path.write_text("candidates: []\n", encoding="utf-8")
    monkeypatch.setattr(verification, "DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH", fixture_path)
    monkeypatch.setattr(verification, "PREVERIFICATION_BOUNDARIES_DIR", storage.CORPUS_DIR)
    boundary_path = storage.external_data_boundary_asset_paths(
        "gooaye", "EP700", "EP700 Alpha"
    ).json_path
    filters = runner._filters(
        expected_episode_ref="EP700",
        stock_query=None,
        include_fixture_verification=True,
        transcription_model=None,
        transcription_device="cpu",
        transcription_compute_type="int8",
        transcription_vad_filter=False,
        semantic_provider="openai-compatible",
        semantic_model=None,
        semantic_base_url_identity_sha256=None,
        semantic_chunk_seconds=600,
        semantic_max_segments_per_chunk=120,
    )
    committed: set[str] = set()

    with runner._progressive_lineage_scope(
        "gooaye",
        "EP700",
        filters,
        {"external_boundary": boundary_path, "fixture": boundary_path},
        committed,
    ):
        asset = verify_external_data_boundary(
            "gooaye", "EP700", confirm=True, fixture_path=fixture_path
        )
        assert asset.generated
        notify_child_artifact_committed("fixture", boundary_path, generated=True)

    assert committed == {"external_boundary", "fixture"}
    validation = validate_current_verified_research_lineage(
        "gooaye",
        "EP700",
        stock_query=None,
        include_fixture_verification=True,
        summary_options=runner._summary_lineage_options(filters),
        require_generation_proofs=True,
    )
    assert set(validation["artifacts"]) == {
        "transcript", "semantic_summary", "semantic_review", "mentions",
        "intelligence", "industry_mapping", "external_boundary", "fixture",
    }


def test_red_fresh_fixture_run_records_non_preexisting_fixture_proof(monkeypatch, tmp_path):
    """A fresh boundary plus fixture run records two ordinary post-commit proofs."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.external_data_boundary import generate_external_data_boundary
    from podcast_ingest_core.external_data_verification import verify_external_data_boundary
    from podcast_ingest_core.generation_proof import notify_child_artifact_committed
    from podcast_ingest_core.verified_research_lineage import (
        validate_current_verified_research_lineage,
    )
    import podcast_ingest_core.external_data_verification as verification
    import podcast_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _write_completed_artifacts(monkeypatch, tmp_path)
    fixture_path = tmp_path / "fresh-fixture.yaml"
    fixture_path.write_text("candidates: []\n", encoding="utf-8")
    monkeypatch.setattr(verification, "DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH", fixture_path)
    monkeypatch.setattr(verification, "PREVERIFICATION_BOUNDARIES_DIR", storage.CORPUS_DIR)
    boundary = storage.external_data_boundary_asset_paths("gooaye", "EP700", "EP700 Alpha")
    boundary.json_path.unlink()
    boundary.markdown_path.unlink()
    filters = runner._filters(
        expected_episode_ref="EP700", stock_query=None, include_fixture_verification=True,
        transcription_model=None, transcription_device="cpu", transcription_compute_type="int8",
        transcription_vad_filter=False, semantic_provider="openai-compatible", semantic_model=None,
        semantic_base_url_identity_sha256=None, semantic_chunk_seconds=600,
        semantic_max_segments_per_chunk=120,
    )
    committed: set[str] = set()
    with runner._progressive_lineage_scope(
        "gooaye", "EP700", filters,
        {"external_boundary": boundary.json_path, "fixture": boundary.json_path}, committed,
    ):
        generated_boundary = generate_external_data_boundary("gooaye", "EP700")
        notify_child_artifact_committed(
            "external_boundary", generated_boundary.boundary_json_path, generated=True
        )
        fixture = verify_external_data_boundary(
            "gooaye", "EP700", confirm=True, fixture_path=fixture_path
        )
        notify_child_artifact_committed("fixture", fixture.boundary_json_path, generated=True)

    assert committed == {"external_boundary", "fixture"}
    validate_current_verified_research_lineage(
        "gooaye", "EP700", stock_query=None, include_fixture_verification=True,
        summary_options=runner._summary_lineage_options(filters), require_generation_proofs=True,
    )
