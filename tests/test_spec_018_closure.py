"""Closure regressions for SPEC 018's independent trust and pinned-child contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _use_tmp_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from corpus_ingest_core import storage

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


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_transcript_variants(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, object]:
    from corpus_ingest_core import storage

    _use_tmp_dirs(monkeypatch, tmp_path)
    variants: dict[str, object] = {}
    for title in ("EP700 Alpha", "EP700 Corrected"):
        paths = storage.transcript_asset_paths("gooaye", "EP700", title)
        _write_json(
            paths.json_path,
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP700",
                "title": title,
                "segment_count": 1,
                "completed": True,
                "segments": [
                    {
                        "id": 1,
                        "start": 0.0,
                        "end": 1.0,
                        "text": f"NVIDIA content from {title}",
                    }
                ],
            },
        )
        paths.text_path.write_text(f"text from {title}", encoding="utf-8")
        paths.srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nfixture", encoding="utf-8")
        variants[title] = paths
    return variants


def test_red_stale_sidecar_and_manifest_cannot_select_ambiguous_transcript(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """018 self-authored metadata is not an external transcript trust root."""

    from corpus_ingest_core import storage
    from corpus_ingest_core.canonical_transcript import (
        CanonicalTranscriptResolutionError,
        resolve_canonical_transcript_asset_paths,
    )

    variants = _write_transcript_variants(monkeypatch, tmp_path)
    alpha = variants["EP700 Alpha"]
    assert hasattr(alpha, "json_path")
    alpha_json = alpha.json_path
    stale_lineage = (
        storage.CORPUS_DIR / "gooaye" / "verified-research" / "EP700.lineage.json"
    )
    _write_json(
        stale_lineage,
        {
            "schema_version": "latest-episode-verified-research-lineage-v2",
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "artifacts": {
                "transcript": {
                    "path": alpha_json.resolve().as_posix(),
                    "sha256": __import__("hashlib").sha256(alpha_json.read_bytes()).hexdigest(),
                }
            },
        },
    )
    manifest = (
        storage.RESEARCH_REPORTS_DIR
        / "gooaye"
        / "EP700"
        / ("v1-" + "a" * 64)
        / "manifest.json"
    )
    _write_json(
        manifest,
        {
            "episode_identity": {"podcast_id": "gooaye", "episode_ref": "EP700"},
            "quality_gates": {"lineage_quality_gate": "passed"},
            "source_artifacts": [
                {
                    "role": "transcript",
                    "path": alpha_json.resolve().as_posix(),
                    "sha256": __import__("hashlib").sha256(alpha_json.read_bytes()).hexdigest(),
                }
            ],
        },
    )

    with pytest.raises(CanonicalTranscriptResolutionError, match="ambiguous"):
        resolve_canonical_transcript_asset_paths("gooaye", "EP700")


def test_red_seeded_corrected_transcript_is_actual_semantic_and_research_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A seed-selected canonical path must defeat every legacy filename glob."""

    from corpus_ingest_core import storage
    from corpus_ingest_core.entity_extractor import extract_mentions
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
    import corpus_ingest_core.semantic_summarizer as semantic

    variants = _write_transcript_variants(monkeypatch, tmp_path)
    corrected = variants["EP700 Corrected"]
    assert hasattr(corrected, "json_path")
    _write_json(
        storage.corpus_episode_seed_asset_path("gooaye", "EP700"),
        {"podcast_id": "gooaye", "episode_ref": "EP700", "title": "EP700 Corrected"},
    )
    chunks: list[str] = []

    class _Provider:
        provider_name = "fixture-provider"
        model = "fixture-model"

        def summarize_chunk(self, chunk: dict[str, object]) -> str:
            chunks.append(str(chunk["text"]))
            return "[00:00:00 - 00:00:01] fixture"

        def summarize_final(self, **_kwargs: object) -> str:
            return "[00:00:00 - 00:00:01] final fixture"

    monkeypatch.setattr(semantic, "_build_provider", lambda **_kwargs: _Provider())

    summary = semantic.semantic_summarize_episode(
        "gooaye", "EP700", api_cost_ack=SEMANTIC_API_COST_ACK
    )
    mentions = extract_mentions("gooaye", "EP700")

    assert summary.transcript_json_path == corrected.json_path
    assert summary.summary_path == storage.semantic_summary_asset_path(
        "gooaye", "EP700", "EP700 Corrected"
    )
    assert chunks == ["[00:00:00 - 00:00:01] NVIDIA content from EP700 Corrected"]
    assert mentions.source_transcript_json_path == corrected.json_path
    assert mentions.mentions_json_path == storage.mention_asset_paths(
        "gooaye", "EP700", "EP700 Corrected"
    ).json_path


def test_red_audit_report_pair_rejects_second_replace_half_commit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """015--017 fixed report paths need a JSON-last verifiable commit marker."""

    from corpus_ingest_core.audit_report_pair import (
        is_complete_audit_report_pair,
        write_atomic_audit_report_pair,
    )

    json_path = tmp_path / "corpus-run.json"
    markdown_path = tmp_path / "corpus-run.md"
    original_replace = Path.replace
    replace_count = 0

    def fail_json_commit(source: Path, destination: Path) -> Path:
        nonlocal replace_count
        if source.name.startswith(".audit-stage-"):
            replace_count += 1
            if replace_count == 2:
                raise OSError("injected second replace failure")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", fail_json_commit)
    # Public contract wraps the injected replace failure so callers only see the
    # bounded pair-commit error. First-write recovery removes both members when
    # no prior complete generation exists (Markdown alone is never reusable).
    with pytest.raises(OSError, match="audit report pair commit failed") as raised:
        write_atomic_audit_report_pair(
            json_path,
            markdown_path,
            {"podcast_id": "gooaye", "outcome": "completed"},
            "# Completed\n",
        )

    assert raised.value.__cause__ is not None
    assert "injected second replace failure" in str(raised.value.__cause__)
    assert not json_path.exists()
    assert not markdown_path.exists()
    assert not is_complete_audit_report_pair(json_path, markdown_path)


def test_red_audit_pair_replace_failure_restores_last_complete_generation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A replacement failure must not permanently leave old JSON with new Markdown."""

    from corpus_ingest_core.audit_report_pair import (
        read_complete_audit_report_pair,
        write_atomic_audit_report_pair,
    )

    json_path = tmp_path / "podcast-run.json"
    markdown_path = tmp_path / "podcast-run.md"
    write_atomic_audit_report_pair(json_path, markdown_path, {"generation": "old"}, "# Old")
    old = read_complete_audit_report_pair(json_path, markdown_path)
    assert old is not None
    original_replace = Path.replace
    stage_replaces = 0

    def fail_second_staged_replace(source: Path, destination: Path) -> Path:
        nonlocal stage_replaces
        if source.name.startswith(".audit-stage-"):
            stage_replaces += 1
            if stage_replaces == 2:
                raise OSError("injected JSON commit failure")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", fail_second_staged_replace)
    with pytest.raises(OSError, match="audit report pair commit failed"):
        write_atomic_audit_report_pair(json_path, markdown_path, {"generation": "new"}, "# New")

    assert read_complete_audit_report_pair(json_path, markdown_path) == old


def test_red_summary_lineage_records_only_a_safe_base_url_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The output-affecting endpoint is lineage-bound without persisting its URL."""

    import hashlib
    import corpus_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    base_url = "https://semantic.example.test/v1"
    filters = runner._filters(
        expected_episode_ref="EP700",
        stock_query=None,
        include_fixture_verification=False,
        transcription_model=None,
        transcription_device="cpu",
        transcription_compute_type="int8",
        transcription_vad_filter=False,
        semantic_provider="openai-compatible",
        semantic_model="fixture-model",
        semantic_base_url_identity_sha256=hashlib.sha256(base_url.encode("utf-8")).hexdigest(),
        semantic_chunk_seconds=600,
        semantic_max_segments_per_chunk=120,
    )

    options = runner._summary_lineage_options(filters)

    assert options["requested_base_url_identity_sha256"] == hashlib.sha256(base_url.encode("utf-8")).hexdigest()
    assert base_url not in repr(options)


def test_red_progressive_lineage_survives_later_audit_or_research_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A committed child is reusable after a later report/stage writer fails."""

    from corpus_ingest_core import storage
    from corpus_ingest_core.generation_proof import notify_child_artifact_committed
    import corpus_ingest_core.latest_episode_verified_research_report_workflow_runner as runner

    _use_tmp_dirs(monkeypatch, tmp_path)
    transcript = storage.transcript_asset_paths("gooaye", "EP700", "EP700 Alpha")
    _write_json(
        transcript.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": "EP700 Alpha",
            "segments": [],
        },
    )
    transcript.text_path.write_text("fixture", encoding="utf-8")
    transcript.srt_path.write_text("fixture", encoding="utf-8")
    filters = runner._filters(
        expected_episode_ref="EP700",
        stock_query=None,
        include_fixture_verification=False,
        transcription_model=None,
        transcription_device="cpu",
        transcription_compute_type="int8",
        transcription_vad_filter=False,
        semantic_provider="fixture-provider",
        semantic_model="fixture-model",
        semantic_base_url_identity_sha256=None,
        semantic_chunk_seconds=600,
        semantic_max_segments_per_chunk=120,
    )
    summary_path = storage.semantic_summary_asset_path("gooaye", "EP700", "EP700 Alpha")
    summary_commits: set[str] = set()

    with pytest.raises(OSError, match="015 audit report"):
        with runner._progressive_lineage_scope(
            "gooaye", "EP700", filters, {"semantic_summary": summary_path}, summary_commits
        ):
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                "Summary mode: semantic-llm\nProvider: fixture-provider\n"
                "Model: fixture-model\n[00:00:00 - 00:00:01] fixture\n",
                encoding="utf-8",
            )
            notify_child_artifact_committed(
                "semantic_summary",
                summary_path,
                generated=True,
                metadata={"provider": "fixture-provider", "model": "fixture-model"},
            )
            raise OSError("015 audit report write failed")

    assert summary_commits == {"semantic_summary"}
    with runner._progressive_lineage_scope(
        "gooaye", "EP700", filters, {"semantic_summary": summary_path}, set()
    ):
        notify_child_artifact_committed(
            "semantic_summary",
            summary_path,
            generated=False,
            metadata={"provider": "fixture-provider", "model": "fixture-model"},
        )

    mention_path = storage.mention_asset_paths("gooaye", "EP700", "EP700 Alpha").json_path
    mention_commits: set[str] = set()
    with pytest.raises(OSError, match="later research stage"):
        with runner._progressive_lineage_scope(
            "gooaye", "EP700", filters, {"mentions": mention_path}, mention_commits
        ):
            _write_json(
                mention_path,
                {
                    "podcast_id": "gooaye",
                    "episode_ref": "EP700",
                    "title": "EP700 Alpha",
                    "extraction_mode": "deterministic-entity-extraction-v1",
                    "mentions": [],
                },
            )
            notify_child_artifact_committed("mentions", mention_path, generated=True)
            raise OSError("later research stage failed")

    assert mention_commits == {"mentions"}
    with runner._progressive_lineage_scope(
        "gooaye", "EP700", filters, {"mentions": mention_path}, set()
    ):
        notify_child_artifact_committed("mentions", mention_path, generated=False)


def test_red_same_episode_direct_semantic_calls_share_one_cost_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The direct writer must share 018's same-episode cost boundary."""

    from threading import Barrier, Lock, Thread
    import time

    from corpus_ingest_core import storage
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
    import corpus_ingest_core.semantic_summarizer as semantic

    _use_tmp_dirs(monkeypatch, tmp_path)
    paths = storage.transcript_asset_paths("gooaye", "EP700", "EP700 Alpha")
    _write_json(
        paths.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP700",
            "title": "EP700 Alpha",
            "segment_count": 1,
            "completed": True,
            "segments": [{"id": 1, "start": 0.0, "end": 1.0, "text": "NVIDIA"}],
        },
    )
    paths.text_path.write_text("NVIDIA", encoding="utf-8")
    paths.srt_path.write_text("fixture", encoding="utf-8")
    barrier = Barrier(2)
    count_lock = Lock()
    provider_count = 0

    class _Provider:
        provider_name = "fixture-provider"
        model = "fixture-model"

        def summarize_chunk(self, _chunk: dict[str, object]) -> str:
            time.sleep(0.1)
            return "[00:00:00 - 00:00:01] fixture"

        def summarize_final(self, **_kwargs: object) -> str:
            return "[00:00:00 - 00:00:01] fixture"

    def build_provider(**_kwargs: object) -> _Provider:
        nonlocal provider_count
        with count_lock:
            provider_count += 1
        return _Provider()

    monkeypatch.setattr(semantic, "_build_provider", build_provider)
    failures: list[BaseException] = []

    def invoke() -> None:
        try:
            barrier.wait()
            semantic.semantic_summarize_episode(
                "gooaye", "EP700", api_cost_ack=SEMANTIC_API_COST_ACK
            )
        except BaseException as exc:  # pragma: no cover - asserted below.
            failures.append(exc)

    threads = [Thread(target=invoke), Thread(target=invoke)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not failures
    assert not any(thread.is_alive() for thread in threads)
    assert provider_count == 1
