from __future__ import annotations

from dataclasses import asdict
import importlib
import json
from pathlib import Path
import socket
import sys


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> Path:
    from podcast_ingest_core import storage
    import podcast_ingest_core.corpus_index as corpus_index

    monkeypatch.setattr(storage, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus", raising=False)
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(
        corpus_index, "SEMANTIC_REVIEW_REPORTS_DIR", review_dir, raising=False
    )
    return review_dir


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_episode_seed(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP677",
    title: str = "EP677 Alpha",
    has_audio_url: bool = True,
) -> Path:
    from podcast_ingest_core.storage import corpus_episode_seed_asset_path

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    return _write_json(
        corpus_episode_seed_asset_path(podcast_id, episode_ref),
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "published_at": "Thu, 09 Jul 2026 00:00:00 GMT",
            "duration": "00:42:00",
            "guid_status": "present",
            "has_audio_url": has_audio_url,
            "seed_source": "rss",
            "selector": "latest",
            "warning_count": 0,
            "warnings": [],
            "not_investment_advice": True,
        },
    )


def _write_audio(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    path = storage.AUDIO_DIR / podcast_id / f"{episode_ref}__{title}.mp3"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"mp3")
    return path


def _write_transcript(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
    segments: list[dict] | None = None,
    json_text: str | None = None,
) -> Path:
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {"id": 1, "start": 0.0, "end": 5.5, "text": "transcript body must not leak"},
            {"id": 2, "start": 7.0, "end": 9.0, "text": "second body line"},
        ]
    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("\n".join(item["text"] for item in segments), encoding="utf-8")
    paths.srt_path.write_text("1\n00:00:00,000 --> 00:00:05,500\ntext\n", encoding="utf-8")
    if json_text is not None:
        paths.json_path.write_text(json_text, encoding="utf-8")
    else:
        _write_json(
            paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "language": "zh",
                "segment_count": len(segments),
                "last_segment_end_seconds": segments[-1]["end"] if segments else None,
                "generated_at": "2026-01-01T00:00:00Z",
                "segments": segments,
            },
        )
    return paths.json_path


def _write_summary(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
    semantic: bool = False,
    body: str = "summary body must not leak",
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    suffix = ".semantic.md" if semantic else ".md"
    path = storage.SUMMARIES_DIR / podcast_id / f"{episode_ref}__{title}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_mentions(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
    json_text: str | None = None,
) -> Path:
    from podcast_ingest_core.storage import mention_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = mention_asset_paths(podcast_id, episode_ref, title)
    if json_text is None:
        _write_json(
            paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "mention_count": 2,
                "mentions": [{"text": "mention evidence must not leak"}],
            },
        )
    else:
        paths.json_path.parent.mkdir(parents=True, exist_ok=True)
        paths.json_path.write_text(json_text, encoding="utf-8")
    paths.markdown_path.write_text("# mentions body must not leak", encoding="utf-8")
    return paths.json_path


def _write_episode_intelligence(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core.storage import episode_intelligence_report_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = episode_intelligence_report_asset_paths(podcast_id, episode_ref, title)
    _write_json(
        paths.json_path,
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "report_status": "final",
            "sections": [{"evidence": [{"text": "report evidence must not leak"}]}],
        },
    )
    paths.markdown_path.write_text("# report body must not leak", encoding="utf-8")
    return paths.json_path


def _write_industry_mapping(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core.storage import industry_chain_mapping_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = industry_chain_mapping_asset_paths(podcast_id, episode_ref, title)
    _write_json(
        paths.json_path,
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "mapping_status": "final",
            "industry_chain_nodes": [
                {"node_id": "semiconductor", "evidence": [{"text": "node evidence must not leak"}]}
            ],
            "warnings": ["mapping warning body must not leak"],
        },
    )
    paths.markdown_path.write_text("# mapping body must not leak", encoding="utf-8")
    return paths.json_path


def _write_external_boundary(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core.storage import external_data_boundary_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = external_data_boundary_asset_paths(podcast_id, episode_ref, title)
    _write_json(
        paths.json_path,
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "boundary_status": "final",
            "candidate_boundaries": [
                {"company_name": "TSMC", "notes": "boundary body must not leak"}
            ],
        },
    )
    paths.markdown_path.write_text("# boundary body must not leak", encoding="utf-8")
    return paths.json_path


def _write_semantic_review(
    review_dir: Path,
    *,
    timestamp: str = "20260701-000000",
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    review_status: str = "passed",
    check_count: int = 3,
    failed_check_count: int = 0,
    warning_count: int = 0,
) -> Path:
    json_path = review_dir / f"{timestamp}__{podcast_id}__{episode_ref}.semantic-review.json"
    _write_json(
        json_path,
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "review_status": review_status,
            "check_count": check_count,
            "failed_check_count": failed_check_count,
            "warning_count": warning_count,
            "checks": [{"message": "semantic review body must not leak"}],
        },
    )
    json_path.with_suffix(".md").write_text("# review body must not leak", encoding="utf-8")
    return json_path


def _payload(result) -> dict:
    return json.loads(result.plan_json_path.read_text(encoding="utf-8"))


def _episode(payload: dict, episode_ref: str) -> dict:
    return {row["episode_ref"]: row for row in payload["episodes"]}[episode_ref]


def _action(row: dict, artifact_family: str) -> dict:
    return {action["artifact_family"]: action for action in row["actions"]}[artifact_family]


def test_corpus_remediation_plan_asset_paths_contract():
    from podcast_ingest_core.storage import corpus_remediation_plan_asset_paths

    paths = corpus_remediation_plan_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-remediation-plan.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-remediation-plan.md")


def test_corpus_remediation_public_result_contract_exports(tmp_path):
    from podcast_ingest_core import (
        CorpusRemediationAction,
        CorpusRemediationActionCounts,
        CorpusRemediationBlocker,
        CorpusRemediationEpisodeRow,
        CorpusRemediationPlanFailedError,
        CorpusRemediationPlanResult,
        CorpusRemediationWarning,
        generate_corpus_remediation_plan,
    )

    counts = CorpusRemediationActionCounts(
        action_count=1,
        blocked_action_count=0,
        optional_action_count=1,
        gated_action_count=1,
    )
    blocker = CorpusRemediationBlocker(
        blocked_artifact="mentions",
        blocking_artifact="transcript",
        blocking_status="missing",
        message="transcript is missing",
    )
    warning = CorpusRemediationWarning(
        scope="episode",
        episode_ref="EP672",
        artifact_family="mentions",
        message="unreadable JSON metadata",
    )
    action = CorpusRemediationAction(
        action_id="EP672:semantic_summary",
        artifact_family="semantic_summary",
        action_type="generate",
        status="gated",
        order=5,
        reason="semantic summary is missing",
        blocking_artifacts=[],
        suggested_command="python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode semantic",
        manual_only=True,
        optional=True,
        gated=True,
        requires_api_cost_ack=True,
    )
    row = CorpusRemediationEpisodeRow(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="Alpha",
        artifact_status={},
        missing_artifacts=["semantic_summary"],
        blockers=[blocker],
        warnings=[warning],
        actions=[action],
    )
    result = CorpusRemediationPlanResult(
        podcast_id="gooaye",
        plan_json_path=tmp_path / "corpus-remediation-plan.json",
        plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        source_corpus_index_json_path=tmp_path / "corpus-index.json",
        source_corpus_index_markdown_path=tmp_path / "corpus-index.md",
        episode_count=1,
        warning_count=1,
        action_counts=counts,
    )

    assert asdict(row)["actions"][0]["requires_api_cost_ack"] is True
    assert result.action_counts.gated_action_count == 1
    assert CorpusRemediationPlanFailedError.__name__ == "CorpusRemediationPlanFailedError"
    assert callable(generate_corpus_remediation_plan)


def test_generate_corpus_remediation_plan_writes_empty_plan(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    payload = _payload(result)
    markdown = result.plan_markdown_path.read_text(encoding="utf-8")
    assert payload["episode_count"] == 0
    assert payload["action_count"] == 0
    assert payload["episodes"] == []
    assert payload["source_corpus_index_json_path"].endswith("corpus-index.json")
    assert "generated_at" not in result.plan_json_path.read_text(encoding="utf-8")
    assert "Episode count: 0" in markdown


def test_generate_corpus_remediation_plan_markdown_includes_contract_summary(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    markdown = result.plan_markdown_path.read_text(encoding="utf-8")
    assert f"Source index: {result.source_corpus_index_json_path}" in markdown
    assert (
        f"Source index Markdown: {result.source_corpus_index_markdown_path}"
        in markdown
    )
    assert "| Metric | Count |" in markdown
    assert "| episode_count | 0 |" in markdown
    assert "| action_count | 0 |" in markdown


def test_generate_corpus_remediation_plan_refreshes_index_first(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.models import CorpusArtifactFamilyCounts, CorpusIndexResult
    from podcast_ingest_core import storage
    import podcast_ingest_core.corpus_remediation_plan as remediation

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_generate_corpus_index(podcast_id: str) -> CorpusIndexResult:
        calls.append(f"refresh:{podcast_id}")
        paths = storage.corpus_index_asset_paths(podcast_id)
        _write_json(
            paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_count": 1,
                "warning_count": 0,
                "artifact_family_counts": {},
                "episodes": [
                    {
                        "podcast_id": podcast_id,
                        "episode_ref": "EP900",
                        "title": "Fresh",
                        "artifact_status": {
                            "audio": {"status": "missing"},
                            "transcript": {"status": "missing"},
                            "extractive_summary": {"status": "missing"},
                            "semantic_summary": {"status": "missing"},
                            "semantic_review": {"status": "missing"},
                            "mentions": {"status": "missing"},
                            "episode_intelligence": {"status": "missing"},
                            "industry_mapping": {"status": "missing"},
                            "external_boundary": {"status": "missing"},
                        },
                        "missing_artifacts": [
                            "audio",
                            "transcript",
                            "extractive_summary",
                            "semantic_summary",
                            "semantic_review",
                            "mentions",
                            "episode_intelligence",
                            "industry_mapping",
                            "external_boundary",
                        ],
                        "warnings": [],
                    }
                ],
            },
        )
        paths.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        paths.markdown_path.write_text("# fresh", encoding="utf-8")
        return CorpusIndexResult(
            podcast_id=podcast_id,
            index_json_path=paths.json_path,
            index_markdown_path=paths.markdown_path,
            episode_count=1,
            warning_count=0,
            artifact_family_counts={
                "audio": CorpusArtifactFamilyCounts(available=0, missing=1, unreadable=0)
            },
        )

    monkeypatch.setattr(remediation, "generate_corpus_index", fake_generate_corpus_index)

    result = remediation.generate_corpus_remediation_plan("gooaye")

    assert calls == ["refresh:gooaye"]
    assert _payload(result)["episodes"][0]["episode_ref"] == "EP900"


def test_generate_corpus_remediation_plan_orders_actions_and_counts(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path, episode_ref="EP001", title="Alpha")
    _write_audio(monkeypatch, tmp_path, episode_ref="EP002", title="Beta")
    _write_mentions(monkeypatch, tmp_path, episode_ref="EP003", title="Gamma")
    _write_summary(monkeypatch, tmp_path, episode_ref="EP004", title="Delta", semantic=True)
    _write_industry_mapping(monkeypatch, tmp_path, episode_ref="EP005", title="Epsilon")

    result = generate_corpus_remediation_plan("gooaye")

    payload = _payload(result)
    markdown = result.plan_markdown_path.read_text(encoding="utf-8")
    assert payload["episode_count"] == 5
    assert payload["action_count"] > 0
    assert payload["blocked_action_count"] > 0
    assert [row["episode_ref"] for row in payload["episodes"]] == [
        "EP001",
        "EP002",
        "EP003",
        "EP004",
        "EP005",
    ]
    ep001_families = [action["artifact_family"] for action in _episode(payload, "EP001")["actions"]]
    assert ep001_families[:4] == [
        "audio",
        "extractive_summary",
        "mentions",
        "semantic_summary",
    ]
    assert "| EP001 | Alpha |" in markdown
    assert "corpus-remediation-plan" in markdown


def test_generate_corpus_remediation_plan_uses_seed_audio_availability(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _write_episode_seed(
        monkeypatch,
        tmp_path,
        episode_ref="EP677",
        title="EP677 Alpha",
        has_audio_url=True,
    )
    _write_episode_seed(
        monkeypatch,
        tmp_path,
        episode_ref="EP678",
        title="EP678 No Audio",
        has_audio_url=False,
    )

    result = generate_corpus_remediation_plan("gooaye")
    payload = _payload(result)

    ready_audio = _action(_episode(payload, "EP677"), "audio")
    no_audio = _action(_episode(payload, "EP678"), "audio")
    assert ready_audio["status"] == "ready"
    assert ready_audio["reason"] == "audio artifact is missing"
    assert no_audio["status"] == "blocked"
    assert no_audio["blocking_artifacts"] == ["feed_audio_url"]
    assert "feed audio is unavailable" in no_audio["reason"]


def test_generate_corpus_remediation_plan_uses_contract_action_types(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    allowed_action_types = {"download", "transcribe", "generate", "review", "inspect"}
    action_types = {
        action["action_type"]
        for row in _payload(result)["episodes"]
        for action in row["actions"]
    }
    assert action_types <= allowed_action_types


def test_generate_corpus_remediation_plan_is_deterministic_and_has_no_timestamp(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    first = generate_corpus_remediation_plan("gooaye")
    first_json = first.plan_json_path.read_text(encoding="utf-8")
    first_md = first.plan_markdown_path.read_text(encoding="utf-8")
    first.plan_json_path.write_text("stale", encoding="utf-8")
    second = generate_corpus_remediation_plan("gooaye")

    assert second.plan_json_path.read_text(encoding="utf-8") == first_json
    assert second.plan_markdown_path.read_text(encoding="utf-8") == first_md
    assert "generated_at" not in first_json
    assert "2026-01-01T00:00:00Z" not in first_json


def test_generate_corpus_remediation_plan_cli_prints_output_paths_and_counts(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import (
        CorpusRemediationActionCounts,
        CorpusRemediationPlanResult,
    )
    from scripts import generate_corpus_remediation_plan as cli

    result = CorpusRemediationPlanResult(
        podcast_id="gooaye",
        plan_json_path=tmp_path / "corpus-remediation-plan.json",
        plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        source_corpus_index_json_path=tmp_path / "corpus-index.json",
        source_corpus_index_markdown_path=tmp_path / "corpus-index.md",
        episode_count=2,
        warning_count=1,
        action_counts=CorpusRemediationActionCounts(
            action_count=3,
            blocked_action_count=1,
            optional_action_count=1,
            gated_action_count=1,
        ),
    )
    captured = {}

    def fake_generate(podcast_id: str):
        captured["podcast_id"] = podcast_id
        return result

    monkeypatch.setattr(cli, "generate_corpus_remediation_plan", fake_generate)
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_corpus_remediation_plan.py", "--podcast", "gooaye"],
    )

    exit_code = cli.main()

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["podcast_id"] == "gooaye"
    assert payload["plan_json_path"] == str(tmp_path / "corpus-remediation-plan.json")
    assert payload["action_count"] == 3
    assert payload["blocked_action_count"] == 1
    assert payload["optional_action_count"] == 1
    assert payload["gated_action_count"] == 1


def test_generate_corpus_remediation_plan_marks_transcript_blockers(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_audio(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    transcript = _action(row, "transcript")
    blocked = [action for action in row["actions"] if action["status"] == "blocked"]
    assert transcript["status"] == "ready"
    assert transcript["action_type"] == "transcribe"
    assert transcript["manual_only"] is True
    assert transcript["suggested_command"].startswith("python scripts/transcribe_episode.py")
    assert len(blocked) >= 3
    assert all("transcript" in action["blocking_artifacts"] for action in blocked[:3])


def test_generate_corpus_remediation_plan_contains_unreadable_warning(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_mentions(monkeypatch, tmp_path, json_text="{not-json")

    result = generate_corpus_remediation_plan("gooaye")

    payload = _payload(result)
    row = _episode(payload, "EP672")
    mentions = _action(row, "mentions")
    assert payload["warning_count"] == 1
    assert row["artifact_status"]["mentions"]["status"] == "unreadable"
    assert row["warnings"][0]["artifact_family"] == "mentions"
    assert "unreadable JSON metadata" in row["warnings"][0]["message"]
    assert mentions["reason"] == "mentions artifact is unreadable"


def test_generate_corpus_remediation_plan_blocks_downstream_missing_upstream(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    mapping = _action(row, "industry_mapping")
    boundary = row["artifact_status"]["external_boundary"]
    assert boundary["status"] == "final"
    assert boundary["boundary_status"] == "final"
    assert mapping["status"] == "blocked"
    assert "episode_intelligence" in mapping["blocking_artifacts"]
    assert _action(row, "extractive_summary")["blocking_artifacts"] == ["transcript"]


def test_generate_corpus_remediation_plan_blocks_external_boundary_when_transcript_missing(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_industry_mapping(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    boundary = _action(row, "external_boundary")
    assert row["artifact_status"]["transcript"]["status"] == "missing"
    assert row["artifact_status"]["industry_mapping"]["status"] == "final"
    assert boundary["status"] == "blocked"
    assert boundary["blocking_artifacts"] == ["transcript"]


def test_generate_corpus_remediation_plan_blocks_industry_mapping_when_transcript_missing(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_episode_intelligence(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    mapping = _action(row, "industry_mapping")
    assert row["artifact_status"]["transcript"]["status"] == "missing"
    assert row["artifact_status"]["episode_intelligence"]["status"] == "final"
    assert mapping["status"] == "blocked"
    assert mapping["blocking_artifacts"] == ["transcript"]


def test_generate_corpus_remediation_plan_blocks_semantic_review_when_transcript_missing(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_summary(monkeypatch, tmp_path, semantic=True)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    semantic_review = _action(row, "semantic_review")
    assert row["artifact_status"]["transcript"]["status"] == "missing"
    assert row["artifact_status"]["semantic_summary"]["status"] == "available"
    assert semantic_review["status"] == "blocked"
    assert semantic_review["blocking_artifacts"] == ["transcript"]


def test_generate_corpus_remediation_plan_marks_semantic_summary_gated(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    result = generate_corpus_remediation_plan("gooaye")

    semantic = _action(_episode(_payload(result), "EP672"), "semantic_summary")
    assert semantic["status"] == "gated"
    assert semantic["optional"] is True
    assert semantic["gated"] is True
    assert semantic["requires_api_cost_ack"] is True
    assert "--mode semantic" in semantic["suggested_command"]
    assert "API_KEY" not in semantic["suggested_command"]


def test_generate_corpus_remediation_plan_reports_semantic_review_metadata(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    review_dir = _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_summary(monkeypatch, tmp_path, semantic=True)
    review_path = _write_semantic_review(
        review_dir,
        review_status="failed",
        check_count=4,
        failed_check_count=1,
        warning_count=2,
    )

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    assert "semantic_review" not in {action["artifact_family"] for action in row["actions"]}
    semantic_review = row["artifact_status"]["semantic_review"]
    assert semantic_review["review_status"] == "failed"
    assert semantic_review["review_json_path"] == str(review_path)
    assert semantic_review["check_count"] == 4
    assert semantic_review["failed_check_count"] == 1
    assert semantic_review["warning_count"] == 2


def test_generate_corpus_remediation_plan_has_semantic_review_action_after_summary(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    semantic_path = _write_summary(monkeypatch, tmp_path, semantic=True)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    semantic_review = _action(row, "semantic_review")
    assert row["artifact_status"]["semantic_summary"]["path"] == str(semantic_path)
    assert semantic_review["status"] == "optional"
    assert semantic_review["action_type"] == "review"
    assert semantic_review["optional"] is True
    assert semantic_review["blocking_artifacts"] == []


def test_corpus_remediation_plan_import_surface_stays_plan_only():
    source = Path("src/podcast_ingest_core/corpus_remediation_plan.py").read_text(
        encoding="utf-8"
    )
    forbidden_fragments = [
        "from .cache import",
        "from .downloader import",
        "from .entity_extractor import",
        "from .external_data_verification import",
        "from .feed_reader import",
        "from .llm_profiles import",
        "from .local_env import",
        "from .mcp_server import",
        "from .research_workflow import",
        "from .search import",
        "from .semantic_summarizer import",
        "from .stock_lens import",
        "from .stock_lens_synthesis import",
        "from .summarizer import",
        "from .transcriber import",
        "http.client",
        "httpx",
        "requests",
        "socket",
        "urllib",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_generate_corpus_remediation_plan_excludes_raw_body_and_secret_text(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    review_dir = _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(
        monkeypatch,
        tmp_path,
        segments=[
            {
                "id": 1,
                "start": 0.0,
                "end": 1.0,
                "text": "raw transcript sentinel must not leak",
            }
        ],
    )
    _write_summary(
        monkeypatch,
        tmp_path,
        semantic=True,
        body="semantic body sentinel must not leak\nraw LLM output sentinel",
    )
    _write_mentions(monkeypatch, tmp_path)
    _write_episode_intelligence(monkeypatch, tmp_path)
    _write_industry_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)
    _write_semantic_review(review_dir)

    result = generate_corpus_remediation_plan("gooaye")

    json_text = result.plan_json_path.read_text(encoding="utf-8")
    markdown = result.plan_markdown_path.read_text(encoding="utf-8")
    forbidden = [
        "raw transcript sentinel must not leak",
        "mention evidence must not leak",
        "report evidence must not leak",
        "node evidence must not leak",
        "mapping warning body must not leak",
        "boundary body must not leak",
        "semantic body sentinel must not leak",
        "raw LLM output sentinel",
        "semantic review body must not leak",
        "API_KEY=",
        "target price",
        "buy recommendation",
    ]
    for text in forbidden:
        assert text not in json_text
        assert text not in markdown


def test_generate_corpus_remediation_plan_does_not_execute_remediation_boundaries(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_remediation_plan import generate_corpus_remediation_plan

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_audio(monkeypatch, tmp_path)

    def forbidden_call(*args, **kwargs):
        raise AssertionError("remediation plan must not execute side effects")

    forbidden_functions = (
        ("podcast_ingest_core.cache", "initialize_cache"),
        ("podcast_ingest_core.cache", "rebuild_cache"),
        ("podcast_ingest_core.downloader", "download_audio"),
        ("podcast_ingest_core.entity_extractor", "extract_mentions"),
        ("podcast_ingest_core.external_data_verification", "verify_external_data_boundary"),
        ("podcast_ingest_core.feed_reader", "get_episode"),
        ("podcast_ingest_core.feed_reader", "list_episodes"),
        ("podcast_ingest_core.llm_profiles", "load_llm_profile"),
        ("podcast_ingest_core.local_env", "load_local_env"),
        ("podcast_ingest_core.mcp_server", "download_audio"),
        ("podcast_ingest_core.mcp_server", "rebuild_cache"),
        ("podcast_ingest_core.mcp_server", "run_research_workflow"),
        ("podcast_ingest_core.research_workflow", "run_research_workflow"),
        ("podcast_ingest_core.search", "search_mentions"),
        ("podcast_ingest_core.search", "search_transcripts"),
        ("podcast_ingest_core.semantic_summarizer", "semantic_summarize_episode"),
        ("podcast_ingest_core.stock_lens", "generate_stock_lens_report"),
        (
            "podcast_ingest_core.stock_lens_synthesis",
            "generate_stock_lens_synthesis_report",
        ),
        ("podcast_ingest_core.summarizer", "summarize_episode"),
        ("podcast_ingest_core.transcriber", "transcribe_episode"),
    )
    for module_name, function_name in forbidden_functions:
        module = importlib.import_module(module_name)
        monkeypatch.setattr(module, function_name, forbidden_call)
    monkeypatch.setattr(socket, "create_connection", forbidden_call)

    result = generate_corpus_remediation_plan("gooaye")

    row = _episode(_payload(result), "EP672")
    assert _action(row, "transcript")["manual_only"] is True
    assert result.action_counts.action_count == _payload(result)["action_count"]
