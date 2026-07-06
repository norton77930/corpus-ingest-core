from __future__ import annotations

import json
from pathlib import Path


def _write_semantic_summary(
    monkeypatch,
    tmp_path: Path,
    *,
    extra: str = "",
    include_timestamp: bool = True,
    include_chunks: bool = True,
) -> Path:
    import podcast_ingest_core.storage as storage

    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    path = tmp_path / "summaries" / "gooaye" / "EP672__title.semantic.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = "`[00:00:01 - 00:00:10]`" if include_timestamp else ""
    chunk_section = "## Chunk Summaries\n\n### Chunk 1\n\n- chunk summary" if include_chunks else ""
    path.write_text(
        "\n".join(
            [
                "# Gooaye 股癌 - EP672 語意摘要",
                "## Metadata",
                "- Podcast ID: gooaye",
                "- Episode: EP672",
                "- Transcript status: valid",
                "- Summary mode: semantic-llm",
                "- Provider: openai-compatible",
                "- Model: GB10",
                "## 摘要限制",
                "本摘要不構成投資建議。",
                "## 本集主題",
                f"- semantic point {timestamp}",
                chunk_section,
                extra,
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_review_semantic_summary_smoke_generates_passed_report(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summary_smoke_review as review

    summary_path = _write_semantic_summary(monkeypatch, tmp_path)
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    markdown = result.review_markdown_path.read_text(encoding="utf-8")
    assert result.review_status == "passed"
    assert result.semantic_summary_path == summary_path
    assert payload["review_status"] == "passed"
    assert payload["semantic_summary_path"] == str(summary_path)
    assert payload["failed_check_count"] == 0
    assert "Semantic Summary Smoke Review" in markdown
    assert "timestamp_evidence" in markdown


def test_review_semantic_summary_smoke_blocks_missing_artifact(monkeypatch, tmp_path):
    import podcast_ingest_core.storage as storage
    import podcast_ingest_core.semantic_summary_smoke_review as review

    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "blocked"
    assert payload["blocked_check_count"] == 1
    assert any(check["name"] == "semantic_summary_exists" for check in payload["checks"])


def test_review_semantic_summary_smoke_fails_safety_issues(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="sk-test-secret-value\nTraceback (most recent call last):\nBuy 台積電 now.",
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(check["name"] == "secret_leak" and check["status"] == "fail" for check in payload["checks"])
    assert any(check["name"] == "traceback_leak" and check["status"] == "fail" for check in payload["checks"])
    assert any(check["name"] == "prohibited_advice" and check["status"] == "fail" for check in payload["checks"])


def test_review_semantic_summary_smoke_allows_transcript_derived_trade_descriptions(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="\n".join(
            [
                "speaker 當時買進作為避險或佈局。",
                "主持人提到持有超過 100 檔台股股票。",
                "市場提到買進/賣出的情境，但不是對使用者的建議。",
            ]
        ),
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "passed"
    assert any(
        check["name"] == "prohibited_advice" and check["status"] == "pass"
        for check in payload["checks"]
    )


def test_review_semantic_summary_smoke_rejects_direct_trade_advice(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="Buy 台積電 now.\nSell 台積電.\nHold 台積電.\n建議買進。\n不建議買進。\n可以賣出。",
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(
        check["name"] == "prohibited_advice"
        and check["status"] == "fail"
        and "matched_guard=trade_action" in check["message"]
        for check in payload["checks"]
    )


def test_review_semantic_summary_smoke_rejects_target_price_and_guaranteed_return(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="target price 1000\n目標價 1000\nguaranteed return\n保證報酬",
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(
        check["name"] == "prohibited_advice" and check["status"] == "fail"
        for check in payload["checks"]
    )


def test_review_semantic_summary_smoke_warns_for_missing_quality_signals(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        include_timestamp=False,
        include_chunks=False,
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "passed"
    assert payload["warning_count"] >= 2
    assert any(check["name"] == "timestamp_evidence" and check["status"] == "warn" for check in payload["checks"])
    assert any(check["name"] == "chunk_summaries" and check["status"] == "warn" for check in payload["checks"])


def test_review_semantic_summary_smoke_cli_parses_arguments(monkeypatch, tmp_path, capsys):
    from podcast_ingest_core.models import SemanticSummarySmokeReviewResult
    from scripts import review_semantic_summary_smoke as cli

    captured = {}

    def fake_review(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return SemanticSummarySmokeReviewResult(
            podcast_id="gooaye",
            episode_ref="EP672",
            review_status="passed",
            review_json_path=tmp_path / "review.json",
            review_markdown_path=tmp_path / "review.md",
            semantic_summary_path=tmp_path / "summary.semantic.md",
            workflow_stdout_path=tmp_path / "stdout.json",
            check_count=1,
            failed_check_count=0,
            warning_count=0,
            blocked_check_count=0,
        )

    monkeypatch.setattr(cli, "review_semantic_summary_smoke", fake_review)

    exit_code = cli.main(
        [
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--workflow-stdout-path",
            str(tmp_path / "stdout.json"),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"]["workflow_stdout_path"] == tmp_path / "stdout.json"
    assert payload["review_status"] == "passed"
