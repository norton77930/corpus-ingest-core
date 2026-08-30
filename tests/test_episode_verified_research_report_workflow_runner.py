"""SPEC 019 explicit-episode verified research report workflow."""

from __future__ import annotations

import inspect

import pytest


def test_public_signature_requires_episode_ref_and_defaults_confirm_false():
    from corpus_ingest_core import run_episode_verified_research_report_workflow

    sig = inspect.signature(run_episode_verified_research_report_workflow)
    assert list(sig.parameters)[:2] == ["podcast_id", "episode_ref"]
    assert sig.parameters["confirm"].default is False
    assert "api_cost_ack" not in sig.parameters


def test_preview_is_strict_zero_write(monkeypatch, tmp_path):
    from corpus_ingest_core import run_episode_verified_research_report_workflow
    from tests import test_latest_episode_verified_research_report_workflow_runner as t018

    t018._write_completed_artifacts(monkeypatch, tmp_path)
    t018._record_current_018_lineage()
    before = t018._manifest(tmp_path)

    result = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=False)

    assert result.confirm is False
    assert result.ready is True
    assert result.outcome == "ready"
    assert t018._manifest(tmp_path) == before


@pytest.mark.parametrize("selector", ("latest", "LATEST", "next", "Next"))
def test_reserved_selectors_rejected(selector):
    from corpus_ingest_core import run_episode_verified_research_report_workflow
    from corpus_ingest_core.errors import (
        EpisodeVerifiedResearchReportWorkflowRunnerFailedError,
    )

    with pytest.raises(
        EpisodeVerifiedResearchReportWorkflowRunnerFailedError,
        match="reserved",
    ):
        run_episode_verified_research_report_workflow("gooaye", selector, confirm=False)


def test_blocked_when_lineage_missing(monkeypatch, tmp_path):
    from corpus_ingest_core import run_episode_verified_research_report_workflow
    from tests import test_latest_episode_verified_research_report_workflow_runner as t018

    t018._write_completed_artifacts(monkeypatch, tmp_path, with_lineage=False)
    before = t018._manifest(tmp_path)

    preview = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=False)
    confirmed = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=True)

    assert preview.ready is False
    assert preview.outcome == "blocked"
    assert preview.missing_roles or preview.stale_roles or preview.failed_gates
    assert confirmed.outcome == "blocked"
    assert confirmed.bundle_dir is None
    assert t018._manifest(tmp_path) == before


def test_confirm_publishes_and_reuses_without_provider(monkeypatch, tmp_path):
    import corpus_ingest_core.llm_provider as llm_provider
    from corpus_ingest_core import run_episode_verified_research_report_workflow
    from tests import test_latest_episode_verified_research_report_workflow_runner as t018

    t018._write_completed_artifacts(monkeypatch, tmp_path)
    t018._record_current_018_lineage()
    monkeypatch.setattr(
        llm_provider,
        "create_provider",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no provider")),
    )

    first = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=True)
    second = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=True)

    assert first.outcome == "completed"
    assert first.bundle_dir is not None and first.bundle_dir.is_dir()
    assert first.manifest_path is not None and first.manifest_path.is_file()
    assert second.outcome == "reused"
    assert second.bundle_dir == first.bundle_dir


def test_mcp_tool_rejects_latest_before_core(monkeypatch):
    import corpus_ingest_core.mcp_episode_verified_research_report as adapter
    from corpus_ingest_core import mcp_server

    called = []

    def boom(*args, **kwargs):
        called.append(True)
        raise AssertionError("core must not run")

    monkeypatch.setattr(
        adapter.core,
        "run_episode_verified_research_report_workflow",
        boom,
    )
    result = mcp_server.run_episode_verified_research_report_workflow(
        podcast_id="gooaye",
        episode_ref="latest",
        confirm=True,
    )
    assert result["ok"] is False
    assert result["error_type"] == "EpisodeVerifiedResearchReportWorkflowRunnerFailedError"
    assert called == []


def test_owned_lineage_error_maps_to_structured_roles():
    from corpus_ingest_core.episode_verified_research_report_workflow_runner import (
        issues_from_verified_report_message,
    )

    issues = issues_from_verified_report_message("verified report semantic summary lineage is stale or invalid")
    assert [(i.role, i.kind) for i in issues] == [("semantic_summary", "stale")]

    missing = issues_from_verified_report_message("verified report lineage is missing or untrusted")
    assert [(i.role, i.kind) for i in missing] == [("lineage", "missing")]

    # Must not freestyle-match unrelated words like bare "review" without owned shape.
    assert issues_from_verified_report_message("something about review only") == []


def test_post_publish_source_mutation_blocks_stale_reuse(monkeypatch, tmp_path):
    """US3: mutating a lineage-bound source must not silently reuse the old bundle."""

    from corpus_ingest_core import run_episode_verified_research_report_workflow, storage
    from tests import test_latest_episode_verified_research_report_workflow_runner as t018

    t018._write_completed_artifacts(monkeypatch, tmp_path)
    t018._record_current_018_lineage()

    first = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=True)
    assert first.outcome == "completed"
    assert first.bundle_dir is not None
    first_digest = first.source_digest
    first_manifest_bytes = first.manifest_path.read_bytes()

    summary = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    summary.write_bytes(summary.read_bytes() + b"\n# mutated after publish\n")

    second = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=True)

    assert second.outcome == "blocked"
    assert second.bundle_dir is None
    assert second.outcome != "reused"
    assert first.manifest_path.read_bytes() == first_manifest_bytes
    assert first.source_digest == first_digest
    assert second.missing_roles or second.stale_roles or second.failed_gates


def test_blank_episode_ref_rejected():
    from corpus_ingest_core import run_episode_verified_research_report_workflow
    from corpus_ingest_core.errors import (
        EpisodeVerifiedResearchReportWorkflowRunnerFailedError,
    )

    with pytest.raises(
        EpisodeVerifiedResearchReportWorkflowRunnerFailedError,
        match="episode_ref",
    ):
        run_episode_verified_research_report_workflow("gooaye", "  ", confirm=False)


def test_result_to_dict_is_metadata_only(monkeypatch, tmp_path):
    import json

    from corpus_ingest_core.episode_verified_research_report_workflow_runner import (
        result_to_dict,
        run_episode_verified_research_report_workflow,
    )
    from tests import test_latest_episode_verified_research_report_workflow_runner as t018

    t018._write_completed_artifacts(monkeypatch, tmp_path)
    t018._record_current_018_lineage()
    result = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=True)
    payload = result_to_dict(result)
    serialized = json.dumps(payload, ensure_ascii=False)

    assert payload["not_investment_advice"] is True
    assert payload["outcome"] == "completed"
    assert "private transcript sentinel" not in serialized
    assert "api_key" not in serialized.casefold()
    assert isinstance(payload.get("bundle_dir"), str)


@pytest.mark.parametrize(
    ("confirm", "with_lineage", "expected_outcome"),
    (
        (False, True, "ready"),
        (True, False, "blocked"),
        (True, True, "completed"),
    ),
)
def test_all_terminal_paths_do_not_dispatch_upstream_workflows(
    monkeypatch, tmp_path, confirm, with_lineage, expected_outcome
):
    """019 only reads verified inputs, then optionally publishes its own bundle."""

    import corpus_ingest_core.cache as cache
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as completion
    import corpus_ingest_core.corpus_episode_workflow_runner as episode_workflow
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as latest_deterministic
    import corpus_ingest_core.corpus_remediation_runner as remediation
    import corpus_ingest_core.corpus_semantic_remediation_runner as semantic_remediation
    import corpus_ingest_core.downloader as downloader
    import corpus_ingest_core.feed_reader as feed_reader
    import corpus_ingest_core.latest_episode_verified_research_report_workflow_runner as latest_verified
    import corpus_ingest_core.llm_provider as llm_provider
    import corpus_ingest_core.research_workflow as research_workflow
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer
    import corpus_ingest_core.stock_lens_synthesis as stock_lens_synthesis
    import corpus_ingest_core.transcriber as transcriber
    from corpus_ingest_core import run_episode_verified_research_report_workflow
    from tests import test_latest_episode_verified_research_report_workflow_runner as t018

    t018._write_completed_artifacts(monkeypatch, tmp_path, with_lineage=with_lineage)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("SPEC 019 must not dispatch an upstream workflow")

    # These are observable outbound safety boundaries, rather than private
    # readiness helpers. They must remain untouched in every terminal mode.
    monkeypatch.setattr(feed_reader.feedparser, "parse", fail_if_called)
    monkeypatch.setattr(llm_provider, "create_provider", fail_if_called)
    monkeypatch.setattr(semantic_summarizer, "create_provider", fail_if_called)
    monkeypatch.setattr(stock_lens_synthesis, "create_provider", fail_if_called)
    monkeypatch.setattr(downloader, "download_audio", fail_if_called)
    monkeypatch.setattr(transcriber, "transcribe_episode", fail_if_called)
    monkeypatch.setattr(semantic_summarizer, "semantic_summarize_episode", fail_if_called)
    monkeypatch.setattr(semantic_remediation, "run_corpus_semantic_remediation", fail_if_called)
    monkeypatch.setattr(remediation, "run_corpus_remediation", fail_if_called)
    monkeypatch.setattr(episode_workflow, "run_corpus_episode_workflow", fail_if_called)
    monkeypatch.setattr(completion, "run_corpus_episode_completion_workflow", fail_if_called)
    monkeypatch.setattr(latest_deterministic, "run_corpus_latest_episode_deterministic_workflow", fail_if_called)
    monkeypatch.setattr(latest_verified, "run_latest_episode_verified_research_report_workflow", fail_if_called)
    monkeypatch.setattr(research_workflow, "run_research_workflow", fail_if_called)
    monkeypatch.setattr(cache, "rebuild_cache", fail_if_called)

    result = run_episode_verified_research_report_workflow("gooaye", "EP700", confirm=confirm)

    assert result.outcome == expected_outcome
    assert result.confirm is confirm
