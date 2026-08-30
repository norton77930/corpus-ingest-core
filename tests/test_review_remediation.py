from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest


def _configure_local_artifacts(monkeypatch, tmp_path: Path) -> Path:
    import corpus_ingest_core.corpus_index as corpus_index
    import corpus_ingest_core.semantic_summary_smoke_review as review
    from corpus_ingest_core import storage

    for name, directory in (
        ("TRANSCRIPTS_DIR", "transcripts"),
        ("SUMMARIES_DIR", "summaries"),
        ("CORPUS_DIR", "corpus"),
        ("RESEARCH_REPORTS_DIR", "research-reports"),
    ):
        monkeypatch.setattr(storage, name, tmp_path / directory, raising=False)
    reports_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(review, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(corpus_index, "SEMANTIC_REVIEW_REPORTS_DIR", reports_dir)
    return reports_dir


def _write_transcript_and_summary(
    monkeypatch,
    tmp_path: Path,
    *,
    episode_ref: str = "EP700",
    title: str = "EP700 Zulu",
    text: str | None = None,
) -> Path:
    from corpus_ingest_core import storage

    _configure_local_artifacts(monkeypatch, tmp_path)
    transcript = storage.transcript_asset_paths("gooaye", episode_ref, title)
    transcript.json_path.parent.mkdir(parents=True, exist_ok=True)
    transcript.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
                "title": title,
                "segment_count": 1,
                "completed": True,
                "segments": [{"id": 1, "start": 0, "end": 5, "text": "fixture"}],
            }
        ),
        encoding="utf-8",
    )
    transcript.text_path.write_text("fixture", encoding="utf-8")
    transcript.srt_path.write_text("fixture", encoding="utf-8")
    summary = storage.semantic_summary_asset_path("gooaye", episode_ref, title)
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        text
        or "\n".join(
            (
                "# Semantic Summary",
                "Summary mode: semantic-llm",
                "Provider: fixture",
                "Model: fixture",
                "Transcript status: valid",
                "[00:00:00 - 00:00:05] fixture",
                "## Chunk Summaries",
            )
        ),
        encoding="utf-8",
    )
    return summary


def test_red_forged_all_pass_review_with_correct_metadata_is_not_authentic(monkeypatch, tmp_path):
    """A payload that is internally self-consistent is not evidence of evaluation."""
    from corpus_ingest_core import semantic_summary_smoke_review as writer
    from corpus_ingest_core.semantic_review_artifact import inspect_semantic_review

    summary = _write_transcript_and_summary(monkeypatch, tmp_path)
    created = writer.review_semantic_summary_smoke("gooaye", "EP700")
    payload = json.loads(created.review_json_path.read_text(encoding="utf-8"))
    for check in payload["checks"]:
        check["message"] = "forged all-pass evidence"
    created.review_json_path.write_text(json.dumps(payload), encoding="utf-8")

    inspection = inspect_semantic_review(
        "gooaye",
        "EP700",
        semantic_summary_path=summary,
        review_reports_dir=writer.REPORTS_DIR,
    )

    assert inspection.review_status == "needs_review"


@pytest.mark.parametrize("authorization", ["Bearer AbCdEf0123456789._-~+/=", "bEaReR token_0123456789"])
def test_red_bearer_authorization_is_rejected_by_semantic_reviewer(monkeypatch, tmp_path, authorization):
    from corpus_ingest_core import semantic_summary_smoke_review as writer

    _write_transcript_and_summary(monkeypatch, tmp_path, text=f"Bearer scan\n{authorization}")

    result = writer.review_semantic_summary_smoke("gooaye", "EP700")

    assert result.review_status == "failed"


def test_red_canonical_summary_uses_transcript_title_not_lexicographic_candidate(monkeypatch, tmp_path):
    import corpus_ingest_core.latest_episode_verified_research_report_workflow_runner as workflow
    from corpus_ingest_core import corpus_index, storage
    from corpus_ingest_core import semantic_summary_smoke_review as writer

    zulu = _write_transcript_and_summary(monkeypatch, tmp_path, title="EP700 Zulu")
    alpha = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    alpha.write_text("Buy ACME now", encoding="utf-8")

    review = writer.review_semantic_summary_smoke("gooaye", "EP700")
    row = next(
        row
        for row in corpus_index._build_corpus_index_snapshot("gooaye").payload["episodes"]
        if row["episode_ref"] == "EP700"
    )
    state = workflow._semantic_state("gooaye", "EP700", workflow._transcript_title("gooaye", "EP700"))

    assert review.review_status == "passed"
    assert review.semantic_summary_path == zulu
    assert row["artifact_status"]["semantic_summary"]["path"] == str(zulu)
    assert state == {"summary": "available", "review": "passed"}


def test_red_neutral_semantic_review_uses_low_level_disclaimer_policy_without_llm_imports():
    """Semantic review remains deterministic and compatible with safety disclaimers."""
    import inspect

    import corpus_ingest_core.semantic_review_artifact as review

    source = inspect.getsource(review)
    assert "stock_lens_synthesis" not in source
    assert "llm_provider" not in source
    assert "semantic_summarizer" not in source

    evaluation = review.evaluate_semantic_review_bytes(
        (
            b"Summary mode: semantic-llm\nProvider: fixture\nModel: fixture\n"
            b"Transcript status: valid\n[00:00:00 - 00:00:05] fixture\n"
            b"## Chunk Summaries\n"
            b"This is not investment advice. No buy/sell/hold advice is provided."
        ),
        semantic_summary_path=Path("summary.semantic.md"),
    )

    assert evaluation.review_status == "passed"
    assert next(check for check in evaluation.checks if check["name"] == "prohibited_advice") == {
        "name": "prohibited_advice",
        "status": "pass",
        "message": "no prohibited advice",
    }


def test_red_same_second_review_writers_claim_distinct_complete_artifacts(monkeypatch, tmp_path):
    from corpus_ingest_core import semantic_summary_smoke_review as writer

    _write_transcript_and_summary(monkeypatch, tmp_path)
    monkeypatch.setattr(writer, "_next_available_path", lambda path: path)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: writer.review_semantic_summary_smoke("gooaye", "EP700"), range(8)))

    assert len({result.review_json_path for result in results}) == 8
    assert all(result.review_json_path.exists() for result in results)
    assert all(result.review_markdown_path.exists() for result in results)
    assert not list(writer.REPORTS_DIR.glob("*.part"))


def test_review_writer_holds_the_episode_claim_while_publishing(monkeypatch, tmp_path):
    from corpus_ingest_core import semantic_summary_smoke_review as writer
    from corpus_ingest_core.episode_claim import _episode_writer_claim_is_held

    _write_transcript_and_summary(monkeypatch, tmp_path)
    original_publish = writer._publish_review_artifacts
    held = []

    def publish(*args):
        held.append(_episode_writer_claim_is_held("gooaye", "EP700"))
        return original_publish(*args)

    monkeypatch.setattr(writer, "_publish_review_artifacts", publish)

    result = writer.review_semantic_summary_smoke("gooaye", "EP700")

    assert result.review_json_path.exists()
    assert held == [True]


def test_review_writer_reenters_an_existing_same_episode_claim(monkeypatch, tmp_path):
    from corpus_ingest_core import semantic_summary_smoke_review as writer
    from corpus_ingest_core.episode_claim import episode_writer_claim

    _write_transcript_and_summary(monkeypatch, tmp_path)

    with episode_writer_claim("gooaye", "EP700"):
        result = writer.review_semantic_summary_smoke("gooaye", "EP700")

    assert result.review_json_path.exists()


def test_review_writer_serializes_external_same_episode_writer(monkeypatch, tmp_path):
    from corpus_ingest_core import semantic_summary_smoke_review as writer

    _write_transcript_and_summary(monkeypatch, tmp_path)
    original_publish = writer._publish_review_artifacts
    first_started = Event()
    release_first = Event()
    second_started = Event()
    publish_count = 0

    def publish(*args):
        nonlocal publish_count
        publish_count += 1
        if publish_count == 1:
            first_started.set()
            assert release_first.wait(timeout=5)
        else:
            second_started.set()
        return original_publish(*args)

    monkeypatch.setattr(writer, "_publish_review_artifacts", publish)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(writer.review_semantic_summary_smoke, "gooaye", "EP700")
        assert first_started.wait(timeout=5)
        second = executor.submit(writer.review_semantic_summary_smoke, "gooaye", "EP700")
        assert not second_started.wait(timeout=0.2)
        release_first.set()
        first.result(timeout=5)
        second.result(timeout=5)

    assert publish_count == 2


@pytest.mark.parametrize("selector", ["latest", "LATEST", "Latest"])
def test_red_reserved_selector_is_rejected_before_completion_core_selection(monkeypatch, selector):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as workflow
    from corpus_ingest_core import CorpusEpisodeCompletionWorkflowRunnerFailedError

    monkeypatch.setattr(
        workflow,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: pytest.fail("reserved selector reached RSS"),
    )

    with pytest.raises(CorpusEpisodeCompletionWorkflowRunnerFailedError):
        workflow.run_corpus_episode_completion_workflow("gooaye", episode_ref=selector, action="intake", confirm=True)


@pytest.mark.parametrize("selector", ["latest", "LATEST", "Latest"])
def test_red_reserved_selector_is_rejected_before_018_core_rss_and_checkpoint(monkeypatch, selector):
    import corpus_ingest_core.latest_episode_verified_research_report_workflow_runner as workflow
    from corpus_ingest_core import LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError
    from corpus_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    monkeypatch.setattr(
        workflow,
        "_resolve_latest_episode",
        lambda *args, **kwargs: pytest.fail("reserved expected reference reached RSS"),
    )

    with pytest.raises(LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError):
        workflow.run_latest_episode_verified_research_report_workflow(
            "gooaye",
            confirm=True,
            expected_episode_ref=selector,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )


@pytest.mark.parametrize("selector", ["latest", "LATEST", "Latest"])
def test_red_reserved_selector_is_rejected_by_mcp_before_core(monkeypatch, selector):
    from corpus_ingest_core import mcp_server

    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        lambda *args, **kwargs: pytest.fail("reserved selector reached completion Core"),
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        "gooaye", episode_ref=selector, action="intake", confirm=True
    )

    assert response["ok"] is False


def test_red_late_failed_checkpoint_cannot_downgrade_published_bundle(tmp_path):
    import corpus_ingest_core.latest_episode_verified_research_report_workflow_runner as workflow

    checkpoint = tmp_path / "EP700.checkpoint.json"
    digest = "a" * 64
    workflow._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "publish", "status": "completed"}],
        source_digest=digest,
        report_version=f"v1-{digest}",
        terminal_outcome="completed",
        bundle_references={"manifest_path": "data/research-reports/gooaye/EP700/v1-a/manifest.json"},
    )
    workflow._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "semantic_review", "status": "failed"}],
        terminal_outcome="failed",
    )

    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["terminal_outcome"] == "completed"
    assert payload["source_digest"] == digest
    assert payload["bundle_references"]["manifest_path"].endswith("manifest.json")


def _same_second_process_review(root_text: str, result_queue) -> None:
    """Spawn target: independently claim one report path from the same fixture."""
    from datetime import datetime as real_datetime
    from pathlib import Path as local_path

    import corpus_ingest_core.semantic_summary_smoke_review as writer
    from corpus_ingest_core import storage

    root = local_path(root_text)
    storage.TRANSCRIPTS_DIR = root / "transcripts"
    storage.SUMMARIES_DIR = root / "summaries"
    writer.REPORTS_DIR = root / "evals" / "research-llm-smoke" / "reports"

    class _FrozenDatetime:
        @classmethod
        def now(cls):
            return real_datetime(2026, 7, 22, 1, 2, 3)

    writer.datetime = _FrozenDatetime
    # This forces the pre-claim implementation's allocation race.  The claimed
    # writer no longer relies on this compatibility helper.
    writer._next_available_path = lambda path: path
    result = writer.review_semantic_summary_smoke("gooaye", "EP700")
    result_queue.put((str(result.review_json_path), str(result.review_markdown_path)))


def _hold_artifact_claim_until_terminated(claim_path_text: str, result_queue) -> None:
    """Spawn target: hold an OS-backed claim until the parent terminates us."""
    import time

    from corpus_ingest_core.artifact_lock import exclusive_artifact_claim

    with exclusive_artifact_claim(Path(claim_path_text), timeout_seconds=5.0):
        result_queue.put("held")
        time.sleep(60)


def _resume_artifact_claim(claim_path_text: str, result_queue) -> None:
    """Spawn target: prove a persistent lockfile is not a held OS lock."""
    from corpus_ingest_core.artifact_lock import exclusive_artifact_claim

    try:
        with exclusive_artifact_claim(Path(claim_path_text), timeout_seconds=0.5):
            result_queue.put("acquired")
    except TimeoutError:
        result_queue.put("timed_out")


@pytest.mark.parametrize(
    "claim_name",
    (
        ".EP700.checkpoint.json.checkpoint.claim",
        ".v1-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.publish.claim",
    ),
    ids=("checkpoint", "bundle"),
)
def test_red_process_lifetime_claim_releases_after_terminated_holder_and_keeps_lockfile(tmp_path, claim_name):
    """Crash recovery covers the exact claim names used by checkpoint and bundle writers."""
    import multiprocessing

    claim_path = tmp_path / "claims" / claim_name
    context = multiprocessing.get_context("spawn")
    held_queue = context.Queue()
    holder = context.Process(
        target=_hold_artifact_claim_until_terminated,
        args=(str(claim_path), held_queue),
    )
    holder.start()
    try:
        assert held_queue.get(timeout=10) == "held"
        assert claim_path.is_file()
        holder.terminate()
        holder.join(timeout=10)
        assert holder.exitcode is not None

        resumed_queue = context.Queue()
        resumed = context.Process(
            target=_resume_artifact_claim,
            args=(str(claim_path), resumed_queue),
        )
        resumed.start()
        resumed.join(timeout=10)
        assert resumed.exitcode == 0
        assert resumed_queue.get(timeout=5) == "acquired"
        assert claim_path.is_file()
    finally:
        if holder.is_alive():
            holder.terminate()
            holder.join(timeout=10)


def _resume_checkpoint_writer(root_text: str, result_queue) -> None:
    """Spawn target: resume a real checkpoint write after a killed holder."""
    from corpus_ingest_core import latest_episode_verified_research_report_workflow_runner as runner

    checkpoint = Path(root_text) / "EP700.checkpoint.json"
    runner._write_checkpoint(
        checkpoint,
        "gooaye",
        "EP700",
        [{"stage": "inspection", "status": "completed"}],
    )
    result_queue.put(checkpoint.is_file())


def test_process_crash_recovery_resumes_real_checkpoint_writer(tmp_path):
    """A retained checkpoint claim cannot block the next process's real writer.

    Bundle publish recovery is not faked here: lineage-gated publication is covered
    by dedicated 018 assemble/publish tests without stubs. Bundle *claim-name*
    crash recovery is covered by
    ``test_red_process_lifetime_claim_releases_after_terminated_holder_and_keeps_lockfile``.
    """
    import multiprocessing

    root = tmp_path / "checkpoint"
    checkpoint = root / "EP700.checkpoint.json"
    claim_path = checkpoint.with_name(f".{checkpoint.name}.checkpoint.claim")

    context = multiprocessing.get_context("spawn")
    held_queue = context.Queue()
    holder = context.Process(
        target=_hold_artifact_claim_until_terminated,
        args=(str(claim_path), held_queue),
    )
    holder.start()
    try:
        assert held_queue.get(timeout=10) == "held"
        holder.terminate()
        holder.join(timeout=10)
        assert holder.exitcode is not None

        resumed_queue = context.Queue()
        resumed = context.Process(
            target=_resume_checkpoint_writer,
            args=(str(root), resumed_queue),
        )
        resumed.start()
        resumed.join(timeout=15)
        assert resumed.exitcode == 0
        assert resumed_queue.get(timeout=5) is True
        assert claim_path.is_file()
    finally:
        if holder.is_alive():
            holder.terminate()
            holder.join(timeout=10)


def test_same_second_process_review_writers_claim_distinct_complete_artifacts(monkeypatch, tmp_path):
    import multiprocessing

    reports_dir = _configure_local_artifacts(monkeypatch, tmp_path)
    _write_transcript_and_summary(monkeypatch, tmp_path)
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    processes = [
        context.Process(
            target=_same_second_process_review,
            args=(str(tmp_path), result_queue),
        )
        for _ in range(3)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)

    assert all(process.exitcode == 0 for process in processes)
    results = [result_queue.get(timeout=5) for _ in processes]
    assert len({json_path for json_path, _ in results}) == len(processes)
    assert all(Path(json_path).is_file() and Path(markdown_path).is_file() for json_path, markdown_path in results)
    assert not list(reports_dir.glob("*.part"))
    assert list(reports_dir.glob("*.claim"))


def test_red_inspector_skips_future_forged_and_rejected_candidates_for_latest_authentic_collision(
    monkeypatch, tmp_path
):
    """Filename order cannot let invalid future artifacts poison current provenance."""
    from datetime import datetime as real_datetime

    from corpus_ingest_core import semantic_summary_smoke_review as writer
    from corpus_ingest_core.semantic_review_artifact import inspect_semantic_review

    reports_dir = _configure_local_artifacts(monkeypatch, tmp_path)
    summary = _write_transcript_and_summary(monkeypatch, tmp_path)

    class FixedDateTime:
        @classmethod
        def now(cls):
            return real_datetime(2026, 7, 22, 1, 2, 3)

    monkeypatch.setattr(writer, "datetime", FixedDateTime)
    first = writer.review_semantic_summary_smoke("gooaye", "EP700")
    second = writer.review_semantic_summary_smoke("gooaye", "EP700")
    forged_future = reports_dir / "20991231-235959__gooaye__EP700.semantic-review.json"
    forged_payload = json.loads(second.review_json_path.read_text(encoding="utf-8"))
    forged_payload["checks"][0]["message"] = "forged deterministic evidence"
    forged_future.write_text(json.dumps(forged_payload), encoding="utf-8")
    rejected = reports_dir / "future__gooaye__EP700.semantic-review.json"
    rejected.write_text("{}", encoding="utf-8")

    inspection = inspect_semantic_review(
        "gooaye",
        "EP700",
        semantic_summary_path=summary,
        review_reports_dir=reports_dir,
    )

    assert first.review_json_path != second.review_json_path
    assert inspection.review_status == "passed"
    assert inspection.review_path == second.review_json_path
