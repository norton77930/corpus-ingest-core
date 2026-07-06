from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest


def _write_synthesis_artifacts(
    monkeypatch,
    tmp_path: Path,
    *,
    markdown_extra: str = "",
    payload_extra: dict | None = None,
    corrupt_json: bool = False,
) -> tuple[Path, Path]:
    import podcast_ingest_core.storage as storage

    monkeypatch.setattr(storage, "STOCK_LENS_DIR", tmp_path / "stock-lens")
    json_path, markdown_path = _synthesis_paths(tmp_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "podcast_id": "gooaye",
        "stock_query": "台積電",
        "synthesis_mode": "llm-stock-lens-synthesis-v1",
        "synthesis_status": "final",
        "llm_input_boundary": "phase-6f-stock-lens-json-only",
        "provider": "openai-compatible",
        "model": "GB10",
        "not_investment_advice": True,
        "source_direct_podcast_evidence": [{"timestamp": "[00:01:23 - 00:01:30]"}],
        "source_inferred_research_leads": [],
        "source_external_verification_needs": [
            {"source_status": "not_fetched", "external_verification_status": "not_requested"}
        ],
        "warnings": ["no raw transcript was used"],
    }
    if payload_extra:
        payload.update(payload_extra)
    if corrupt_json:
        json_path.write_text("{not-json", encoding="utf-8")
    else:
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(
        "\n".join(
            [
                "# 台積電 Stock Lens LLM Synthesis",
                "LLM input boundary: phase-6f-stock-lens-json-only",
                "Direct podcast evidence is separated from inferred research leads.",
                "External status values such as not_requested, not_fetched, and data_date=null are unavailable-data markers.",
                "Gooaye Lens dimensions: industry chain, supply demand, cycle, valuation, capex, geopolitics.",
                "No buy/sell/hold advice. No target price. No guaranteed returns.",
                markdown_extra,
            ]
        ),
        encoding="utf-8",
    )
    return json_path, markdown_path


def _synthesis_paths(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "stock-lens" / "gooaye" / "台積電"
    return (
        base.with_suffix(".stock-lens-synthesis.json"),
        base.with_suffix(".stock-lens-synthesis.md"),
    )


def test_review_research_llm_smoke_generates_passed_report(monkeypatch, tmp_path):
    import podcast_ingest_core.research_llm_smoke_review as review

    json_path, markdown_path = _write_synthesis_artifacts(monkeypatch, tmp_path)
    reports_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(review, "REPORTS_DIR", reports_dir)

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    markdown = result.review_markdown_path.read_text(encoding="utf-8")
    assert result.review_status == "passed"
    assert result.review_json_path.name.endswith(".review.json")
    assert result.review_markdown_path.name.endswith(".review.md")
    assert payload["review_status"] == "passed"
    assert payload["synthesis_json_path"] == str(json_path)
    assert payload["synthesis_markdown_path"] == str(markdown_path)
    assert payload["provider"] == "openai-compatible"
    assert payload["model"] == "GB10"
    assert any(check["name"] == "input_boundary" for check in payload["checks"])
    assert "phase-6f-stock-lens-json-only" in markdown
    assert "Quality Checks" in markdown


def test_review_research_llm_smoke_accepts_reviewed_semantic_boundary(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.research_llm_smoke_review as review

    _write_synthesis_artifacts(
        monkeypatch,
        tmp_path,
        payload_extra={
            "llm_input_boundary": "phase-6f-stock-lens-json-plus-reviewed-semantic-summary",
            "source_semantic_context": [
                {
                    "podcast_id": "gooaye",
                    "episode_ref": "EP672",
                    "review_status": "passed",
                    "content": "Reviewed semantic summary says 台積電產能限制延長 AI cycle.",
                }
            ],
        },
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "passed"
    assert any(
        check["name"] == "input_boundary" and check["status"] == "pass"
        for check in payload["checks"]
    )
    assert payload["llm_input_boundary"] == (
        "phase-6f-stock-lens-json-plus-reviewed-semantic-summary"
    )


@pytest.mark.parametrize(
    "payload_extra",
    [
        {
            "llm_input_boundary": "phase-6f-stock-lens-json-plus-reviewed-semantic-summary",
            "source_semantic_context": [],
        },
        {
            "llm_input_boundary": "phase-6f-stock-lens-json-plus-reviewed-semantic-summary",
            "source_semantic_context": [
                {
                    "podcast_id": "gooaye",
                    "episode_ref": "EP672",
                    "review_status": "failed",
                    "content": "Semantic context exists but did not pass review.",
                }
            ],
        },
        {
            "source_semantic_context": [
                {
                    "podcast_id": "gooaye",
                    "episode_ref": "EP672",
                    "review_status": "passed",
                    "content": "Semantic context should not appear with JSON-only boundary.",
                }
            ],
        },
    ],
)
def test_review_research_llm_smoke_fails_inconsistent_semantic_boundary(
    monkeypatch, tmp_path, payload_extra
):
    import podcast_ingest_core.research_llm_smoke_review as review

    _write_synthesis_artifacts(monkeypatch, tmp_path, payload_extra=payload_extra)
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(
        check["name"] == "input_boundary" and check["status"] == "fail"
        for check in payload["checks"]
    )


def test_review_research_llm_smoke_blocks_missing_artifacts(monkeypatch, tmp_path):
    import podcast_ingest_core.storage as storage
    import podcast_ingest_core.research_llm_smoke_review as review

    monkeypatch.setattr(storage, "STOCK_LENS_DIR", tmp_path / "stock-lens")
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "blocked"
    assert payload["review_status"] == "blocked"
    assert any(check["status"] == "blocked" for check in payload["checks"])


def test_review_research_llm_smoke_blocks_corrupt_json(monkeypatch, tmp_path):
    import podcast_ingest_core.research_llm_smoke_review as review

    _write_synthesis_artifacts(monkeypatch, tmp_path, corrupt_json=True)
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "blocked"
    assert any(check["name"] == "synthesis_json_parse" for check in payload["checks"])


@pytest.mark.parametrize(
    ("markdown_extra", "expected_check"),
    [
        ("sk-test-secret-value", "secret_leak"),
        ("Traceback (most recent call last):", "traceback_leak"),
        ("Buy 台積電 now.", "prohibited_advice"),
        ("This has a target price of 1000.", "prohibited_advice"),
        ("This has a guaranteed return of 20%.", "prohibited_advice"),
    ],
)
def test_review_research_llm_smoke_fails_safety_issues(
    monkeypatch, tmp_path, markdown_extra, expected_check
):
    import podcast_ingest_core.research_llm_smoke_review as review

    _write_synthesis_artifacts(monkeypatch, tmp_path, markdown_extra=markdown_extra)
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "failed"
    assert any(
        check["name"] == expected_check and check["status"] == "fail"
        for check in payload["checks"]
    )


def test_review_research_llm_smoke_warns_when_external_status_context_is_missing(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.research_llm_smoke_review as review

    _write_synthesis_artifacts(
        monkeypatch,
        tmp_path,
        markdown_extra="External status: not_fetched not_requested data_date=null.",
    )
    monkeypatch.setattr(review, "REPORTS_DIR", tmp_path / "reports")

    result = review.review_research_llm_smoke("gooaye", "EP672", "台積電")

    payload = json.loads(result.review_json_path.read_text(encoding="utf-8"))
    assert result.review_status == "passed"
    assert any(
        check["name"] == "external_status_boundary" and check["status"] == "warn"
        for check in payload["checks"]
    )


def test_review_research_llm_smoke_cli_parses_arguments(monkeypatch, tmp_path, capsys):
    from podcast_ingest_core.models import ResearchLLMSmokeReviewResult
    from scripts import review_research_llm_smoke as cli

    captured = {}

    def fake_review(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return ResearchLLMSmokeReviewResult(
            podcast_id="gooaye",
            episode_ref="EP672",
            stock_query="台積電",
            review_status="passed",
            review_json_path=tmp_path / "review.json",
            review_markdown_path=tmp_path / "review.md",
            synthesis_json_path=tmp_path / "synthesis.json",
            synthesis_markdown_path=tmp_path / "synthesis.md",
            workflow_stdout_path=tmp_path / "stdout.json",
            raw_output_path=tmp_path / "raw.md",
            check_count=1,
            failed_check_count=0,
            warning_count=0,
            blocked_check_count=0,
        )

    monkeypatch.setattr(cli, "review_research_llm_smoke", fake_review)

    exit_code = cli.main(
        [
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--workflow-stdout-path",
            str(tmp_path / "stdout.json"),
            "--raw-output-path",
            str(tmp_path / "raw.md"),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["args"] == ("gooaye", "EP672", "台積電")
    assert captured["kwargs"]["workflow_stdout_path"] == tmp_path / "stdout.json"
    assert captured["kwargs"]["raw_output_path"] == tmp_path / "raw.md"
    assert payload["review_status"] == "passed"
