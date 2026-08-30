from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _write_semantic_summary(
    monkeypatch,
    tmp_path: Path,
    *,
    extra: str = "",
    include_timestamp: bool = True,
    include_chunks: bool = True,
) -> Path:
    import corpus_ingest_core.storage as storage

    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    transcript = storage.transcript_asset_paths("gooaye", "EP672", "title")
    transcript.json_path.parent.mkdir(parents=True, exist_ok=True)
    transcript.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP672",
                "title": "title",
                "segment_count": 1,
                "completed": True,
                "segments": [{"id": 1, "start": 0, "end": 1, "text": "fixture"}],
            }
        ),
        encoding="utf-8",
    )
    transcript.text_path.write_text("fixture", encoding="utf-8")
    transcript.srt_path.write_text("fixture", encoding="utf-8")
    path = tmp_path / "summaries" / "gooaye" / "EP672__title.semantic.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = "`[00:00:01 - 00:00:10]`" if include_timestamp else ""
    chunk_section = "## Chunk Summaries\n\n### Chunk 1\n\n- chunk summary" if include_chunks else ""
    path.write_text(
        "\n".join(
            [
                "# Gooaye 股癌 - EP672 Semantic Summary",
                "## Metadata",
                "- Podcast ID: gooaye",
                "- Episode: EP672",
                "- Transcript status: valid",
                "- Summary mode: semantic-llm",
                "- Provider: openai-compatible",
                "- Model: GB10",
                "## Summary Limitations",
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
    import corpus_ingest_core.semantic_summary_smoke_review as review

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
    assert payload["semantic_summary_sha256"] == hashlib.sha256(summary_path.read_bytes()).hexdigest()
    assert "Semantic Summary Smoke Review" in markdown
    assert "timestamp_evidence" in markdown


def test_review_semantic_summary_smoke_blocks_missing_artifact(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review
    import corpus_ingest_core.storage as storage

    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "blocked"
    assert payload["blocked_check_count"] == 8
    assert any(check["name"] == "semantic_summary_exists" for check in payload["checks"])


def test_review_semantic_summary_smoke_fails_safety_issues(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

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


def test_review_semantic_summary_smoke_allows_transcript_derived_trade_descriptions(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

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
    assert any(check["name"] == "prohibited_advice" and check["status"] == "pass" for check in payload["checks"])


def test_review_semantic_summary_smoke_rejects_direct_trade_advice(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

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


@pytest.mark.parametrize(
    "advice",
    (
        "You should buy ACME.",
        "You should sell ACME.",
        "You should hold ACME.",
        "I recommend buying ACME.",
        "I recommend selling ACME.",
        "Consider buying ACME.",
        "推薦買進 ACME。",
        "建議賣出 ACME。",
        "值得買進 ACME。",
    ),
)
def test_red_review_and_assembler_share_personalized_advice_guard(monkeypatch, tmp_path, advice):
    import corpus_ingest_core.semantic_summary_smoke_review as review
    from corpus_ingest_core.verified_research_report import (
        VerifiedResearchReportInputError,
        _assert_safe_source_bytes,
        _source_artifact,
    )

    summary_path = _write_semantic_summary(monkeypatch, tmp_path, extra=advice)
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    assert result.review_status == "failed"
    with pytest.raises(VerifiedResearchReportInputError, match="safety boundary"):
        _assert_safe_source_bytes(_source_artifact("semantic_summary", summary_path, True), "semantic summary")


def test_review_semantic_summary_smoke_allows_attributed_quoted_historical_advice(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra='The transcript quoted "You should buy ACME" as a historical example.\n主持人引述「建議買進」作為歷史案例。',
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    assert result.review_status == "passed"


def test_review_semantic_summary_smoke_rejects_target_price_and_guaranteed_return(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="target price 1000\n目標價 1000\nguaranteed return\n保證報酬",
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(check["name"] == "prohibited_advice" and check["status"] == "fail" for check in payload["checks"])


def test_review_semantic_summary_smoke_warns_for_missing_quality_signals(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

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
    from scripts import review_semantic_summary_smoke as cli

    from corpus_ingest_core.models import SemanticSummarySmokeReviewResult

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


def test_review_binds_summary_hash_and_rejects_extended_credential_forms(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

    summary_path = _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="\n".join(
            [
                "AWS_SECRET_ACCESS_KEY=not-a-real-secret",
                "-----BEGIN PRIVATE KEY-----",
                "credential: not-a-real-secret",
                "access_token = not-a-real-secret",
                "password: not-a-real-secret",
            ]
        ),
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert payload["semantic_summary_sha256"] == hashlib.sha256(summary_path.read_bytes()).hexdigest()
    assert result.review_status == "failed"
    assert any(check["name"] == "secret_leak" and check["status"] == "fail" for check in payload["checks"])


def test_review_rejects_json_and_yaml_quoted_credential_assignments(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summary_smoke_review as review

    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        extra="\"password\": \"not-a-real-secret\"\n'token': 'not-a-real-secret'",
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_semantic_summary_smoke("gooaye", "EP672")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(check["name"] == "secret_leak" and check["status"] == "fail" for check in payload["checks"])


@pytest.mark.parametrize(
    "quoted_advice",
    (
        'The transcript quoted "You should buy ACME" as a historical example.',
        "The transcript said “You should buy ACME” as a historical example.",
        "主持人引述「建議買進 ACME」作為歷史案例。",
    ),
)
def test_red_attributed_quote_exception_only_excludes_the_matched_quote_content(quoted_advice):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(quoted_advice) is None
    assert matched_investment_advice_guard(f"{quoted_advice} You should sell ACME.") == "trade_action"


@pytest.mark.parametrize(
    "mismatched_quote_advice",
    (
        'The transcript quoted "You should buy ACME” as a historical example.',
        "The transcript said “You should buy ACME」 as a historical example.",
        '主持人引述「建議買進 ACME"作為歷史案例。',
    ),
)
def test_red_mismatched_quote_never_receives_the_attributed_advice_exception(mismatched_quote_advice):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(mismatched_quote_advice) == "trade_action"


@pytest.mark.parametrize(
    "text",
    (
        "This report is not investment advice. Buy ACME now.",
        "This report is not investment advice.\n- Sell ACME now.",
        "本報告不構成投資建議。立即買進 ACME。",
        "本報告不構成投資建議。\n- 賣出 ACME。",
    ),
)
def test_red_disclaimer_never_bypasses_direct_trade_command(text):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(text) == "trade_action"


@pytest.mark.parametrize(
    "disclaimer",
    (
        "This report is not investment advice.",
        "本報告不構成投資建議。",
    ),
)
def test_disclaimer_without_trade_command_is_not_rejected(disclaimer):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(disclaimer) is None


@pytest.mark.parametrize(
    "text",
    (
        'The analyst said markets were volatile. "You should buy ACME".',
        'The transcript recorded "the analyst said nothing" then "You should buy ACME".',
        'The transcript quoted "a historical note" then "You should buy ACME".',
        'The transcript quoted ""You should buy ACME"" as an ambiguous ASCII quote.',
        'The transcript quoted "The analyst said "You should buy ACME"".',
    ),
)
def test_red_attribution_exception_fails_closed_for_unrelated_or_ambiguous_quotes(text):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(text) == "trade_action"


@pytest.mark.parametrize(
    "text",
    (
        'The transcript quoted "You should buy ACME" as a historical example.',
        "主持人引述「建議買進 ACME」作為歷史案例。",
    ),
)
def test_direct_single_quote_attribution_remains_a_historical_exception(text):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(text) is None


@pytest.mark.parametrize(
    "text",
    (
        "This report is not investment advice: Buy ACME.",
        "This report is not investment advice; Sell ACME.",
        "general text：Hold ACME.",
        "general text；Buy ACME.",
        "本報告不構成投資建議：立即買進 ACME。",
        "本報告不構成投資建議；賣出 ACME。",
        "一般文字: 持有 ACME。",
        "一般文字；立即買進 ACME。",
    ),
)
def test_red_sentence_or_clause_boundary_rejects_trade_commands_after_colons_and_semicolons(text):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(text) == "trade_action"


@pytest.mark.parametrize(
    "disclaimer",
    (
        "This report is not investment advice: no buy/sell/hold advice is provided.",
        "本報告不構成投資建議；不提供任何買賣建議。",
    ),
)
def test_red_colon_or_semicolon_disclaimer_without_command_remains_allowed(disclaimer):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(disclaimer) is None


@pytest.mark.parametrize(
    "text",
    (
        'said: "You should buy ACME"',
        "說：「建議買進 ACME」",
    ),
)
def test_red_subjectless_quote_attribution_never_receives_historical_exception(text):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(text) == "trade_action"


@pytest.mark.parametrize(
    "text",
    (
        'The analyst said: "You should buy ACME"',
        'They said: "You should buy ACME"',
        "分析師說：「建議買進 ACME」",
        "旁白說：「建議買進 ACME」",
    ),
)
def test_red_explicit_quote_attribution_subjects_remain_historical_exceptions(text):
    from corpus_ingest_core.report_safety import matched_investment_advice_guard

    assert matched_investment_advice_guard(text) is None


def test_single_review_inspector_rejects_valid_external_review_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A caller-provided file path must not authorize an arbitrary review directory."""
    import corpus_ingest_core.semantic_review_artifact as artifact
    import corpus_ingest_core.semantic_summary_smoke_review as smoke_review

    trusted_reports = tmp_path / "trusted-reports"
    external_reports = tmp_path / "external-reports"
    external_reports.mkdir()
    summary_path = tmp_path / "summaries" / "show" / "EP1.semantic.md"
    summary_bytes = b"Summary mode: semantic-llm\nProvider: local\nModel: fixture\nTranscript status: valid\n## Chunk Summaries\n[00:00:00 - 00:00:01]"
    payload, evaluation = artifact.semantic_review_payload(
        podcast_id="show",
        episode_ref="EP1",
        semantic_summary_path=summary_path,
        semantic_summary_bytes=summary_bytes,
    )
    assert evaluation.review_status == "passed"
    external_path = external_reports / "20260101-000000__show__EP1.semantic-review.json"
    external_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(smoke_review, "REPORTS_DIR", trusted_reports)

    inspection = artifact.inspect_semantic_review_file(
        "show",
        "EP1",
        semantic_summary_path=summary_path,
        review_path=external_path,
        semantic_summary_bytes=summary_bytes,
    )

    assert inspection.review_status == "needs_review"
    assert inspection.review_payload is None


# --- Spec 037: the disclaimer was never the gate -----------------------------

_LEARNING_NOTES_SUMMARY = "\n".join(
    [
        "# @Raytar (X) - 2071290493581840707 Semantic Summary",
        "",
        "## Metadata",
        "",
        "- Podcast ID: x-raytar",
        "- Episode: 2071290493581840707",
        "- Transcript status: valid",
        "- Summary mode: semantic-llm",
        "- Provider: openai-compatible",
        "- Model: GB10",
        "",
        "## Summary Limitations",
        "",
        "本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。",
        "本摘要僅整理影片內容，結論請回到 timestamp 驗證。",
        "",
        "## 本片主題與適合誰看",
        "",
        "- 這支影片講 prompt engineering `[00:00:01 - 00:00:10]`",
        "",
        "## Chunk Summaries",
        "",
        "### Chunk 1",
        "",
        "- chunk summary",
        "",
    ]
)


def _prohibited_advice_status(markdown: str) -> str:
    from corpus_ingest_core.semantic_review_artifact import (
        evaluate_semantic_review_bytes,
    )

    evaluation = evaluate_semantic_review_bytes(
        summary_bytes=markdown.encode("utf-8"),
        semantic_summary_path=Path("data/summaries/x-raytar/example.semantic.md"),
    )
    checks = {check["name"]: check["status"] for check in evaluation.checks}
    return checks["prohibited_advice"]


def test_learning_notes_summary_passes_without_an_investment_disclaimer():
    """Spec 037's load-bearing claim: ``matched_investment_advice_guard`` is a
    prohibition detector, not a disclaimer requirement. Dropping the disclaimer
    for a profile whose content has no market claim does not weaken the gate."""

    assert "投資" not in _LEARNING_NOTES_SUMMARY
    assert _prohibited_advice_status(_LEARNING_NOTES_SUMMARY) == "pass"


def test_learning_notes_summary_still_fails_when_it_carries_actual_advice():
    """And the profile is not an escape hatch: the check reads rendered Markdown
    and never sees which profile produced it."""

    with_advice = _LEARNING_NOTES_SUMMARY + "\n- 立即買進 ACME。\n"

    assert _prohibited_advice_status(with_advice) == "fail"
