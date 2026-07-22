from __future__ import annotations

from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any

from .models import ResearchLLMSmokeReviewResult
from .report_safety import strip_safety_disclaimers
from . import storage
from .stock_lens_synthesis import (
    INPUT_BOUNDARY,
    REVIEWED_SEMANTIC_INPUT_BOUNDARY,
    _matched_prohibited_guard,
)


REVIEW_MODE = "research-llm-smoke-review-v1"
REPORTS_DIR = Path("evals") / "research-llm-smoke" / "reports"
_SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
_TRACEBACK_PATTERN = re.compile(r"Traceback\s+\(most recent call last\):")
_RAW_TRANSCRIPT_LEAK_PATTERN = re.compile(
    r"raw transcript\s*(?:text|dump|content)\s*[:：]", re.IGNORECASE
)
_EXTERNAL_STATUS_TOKEN_PATTERN = re.compile(
    r"not_requested|not_fetched|data_date\s*=\s*null", re.IGNORECASE
)
_EXTERNAL_STATUS_CONTEXT_PATTERN = re.compile(
    r"unavailable|not market facts?|missing data|not fetched|尚未查證|未查證|不是市場事實",
    re.IGNORECASE,
)
_LENS_PATTERN = re.compile(
    r"go?oaye lens|industry chain|supply|demand|cycle|valuation|capex|geopolitics|產業鏈|供需|景氣|估值|資本支出|地緣",
    re.IGNORECASE,
)


def review_research_llm_smoke(
    podcast_id: str,
    episode_ref: str,
    stock_query: str,
    *,
    workflow_stdout_path: str | Path | None = None,
    raw_output_path: str | Path | None = None,
) -> ResearchLLMSmokeReviewResult:
    """Create a deterministic review report for an existing LLM smoke synthesis."""

    synthesis_paths = storage.stock_lens_synthesis_asset_paths(podcast_id, stock_query)
    workflow_path = Path(workflow_stdout_path) if workflow_stdout_path is not None else None
    raw_path = Path(raw_output_path) if raw_output_path is not None else None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_name = (
        f"{timestamp}__{storage.title_slug(podcast_id, 'podcast')}"
        f"__{storage.title_slug(episode_ref, 'episode')}"
        f"__{storage.title_slug(stock_query, 'stock')}.review.json"
    )
    review_json_path = _next_available_path(REPORTS_DIR / report_name)
    review_markdown_path = review_json_path.with_suffix(".md")

    payload, load_checks = _load_synthesis_payload(synthesis_paths.json_path)
    markdown_text, markdown_checks = _load_markdown(synthesis_paths.markdown_path)
    checks = load_checks + markdown_checks
    if payload is not None and markdown_text is not None:
        checks.extend(_evaluate_payload(payload))
        checks.extend(_evaluate_markdown(markdown_text))
    review_status = _review_status(checks)
    failed_count = sum(1 for check in checks if check["status"] == "fail")
    warning_count = sum(1 for check in checks if check["status"] == "warn")
    blocked_count = sum(1 for check in checks if check["status"] == "blocked")

    report_payload = {
        "review_mode": REVIEW_MODE,
        "review_status": review_status,
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "stock_query": stock_query,
        "synthesis_json_path": str(synthesis_paths.json_path),
        "synthesis_markdown_path": str(synthesis_paths.markdown_path),
        "workflow_stdout_path": str(workflow_path) if workflow_path is not None else None,
        "raw_output_path": str(raw_path) if raw_path is not None else None,
        "provider": payload.get("provider") if payload else None,
        "model": payload.get("model") if payload else None,
        "llm_input_boundary": payload.get("llm_input_boundary") if payload else None,
        "not_investment_advice": payload.get("not_investment_advice") if payload else None,
        "check_count": len(checks),
        "failed_check_count": failed_count,
        "warning_count": warning_count,
        "blocked_check_count": blocked_count,
        "checks": checks,
        "not_investment_advice_notice": True,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    review_json_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    review_markdown_path.write_text(_render_markdown(report_payload), encoding="utf-8")

    return ResearchLLMSmokeReviewResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        stock_query=stock_query,
        review_status=review_status,
        review_json_path=review_json_path,
        review_markdown_path=review_markdown_path,
        synthesis_json_path=synthesis_paths.json_path,
        synthesis_markdown_path=synthesis_paths.markdown_path,
        workflow_stdout_path=workflow_path,
        raw_output_path=raw_path,
        check_count=len(checks),
        failed_check_count=failed_count,
        warning_count=warning_count,
        blocked_check_count=blocked_count,
    )


def _load_synthesis_payload(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not path.exists():
        return None, [_check("synthesis_json_exists", "blocked", f"missing: {path}")]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, [_check("synthesis_json_parse", "blocked", f"invalid JSON: {path}")]
    if not isinstance(payload, dict):
        return None, [_check("synthesis_json_parse", "blocked", "JSON root is not object")]
    return payload, [_check("synthesis_json_exists", "pass", str(path))]


def _load_markdown(path: Path) -> tuple[str | None, list[dict[str, str]]]:
    if not path.exists():
        return None, [_check("synthesis_markdown_exists", "blocked", f"missing: {path}")]
    return path.read_text(encoding="utf-8"), [
        _check("synthesis_markdown_exists", "pass", str(path))
    ]


def _evaluate_payload(payload: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    checks.append(_input_boundary_check(payload))
    checks.append(
        _check(
            "not_investment_advice_flag",
            "pass" if payload.get("not_investment_advice") is True else "fail",
            str(payload.get("not_investment_advice")),
        )
    )
    direct = payload.get("source_direct_podcast_evidence")
    inferred = payload.get("source_inferred_research_leads")
    external = payload.get("source_external_verification_needs")
    checks.append(
        _check(
            "evidence_separation_payload",
            "pass"
            if isinstance(direct, list) and isinstance(inferred, list) and isinstance(external, list)
            else "fail",
            "source evidence fields present",
        )
    )
    return checks


def _input_boundary_check(payload: dict[str, Any]) -> dict[str, str]:
    boundary = str(payload.get("llm_input_boundary"))
    semantic_context = payload.get("source_semantic_context")

    if boundary == INPUT_BOUNDARY:
        if semantic_context is None or semantic_context == []:
            return _check("input_boundary", "pass", boundary)
        return _check(
            "input_boundary",
            "fail",
            f"{boundary}: source_semantic_context must be empty",
        )

    if boundary == REVIEWED_SEMANTIC_INPUT_BOUNDARY:
        if not isinstance(semantic_context, list) or not semantic_context:
            return _check(
                "input_boundary",
                "fail",
                f"{boundary}: source_semantic_context must be non-empty",
            )
        invalid_indexes = [
            str(index)
            for index, entry in enumerate(semantic_context)
            if not _is_passed_semantic_context_entry(entry)
        ]
        if invalid_indexes:
            return _check(
                "input_boundary",
                "fail",
                f"{boundary}: invalid semantic context entries at indexes {', '.join(invalid_indexes)}",
            )
        return _check("input_boundary", "pass", boundary)

    return _check("input_boundary", "fail", boundary)


def _is_passed_semantic_context_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    review_status = str(entry.get("review_status", "")).strip()
    content = str(entry.get("content", "")).strip()
    return review_status == "passed" and bool(content)


def _evaluate_markdown(markdown_text: str) -> list[dict[str, str]]:
    checks = [
        _check(
            "secret_leak",
            "fail" if _SECRET_PATTERN.search(markdown_text) else "pass",
            "API key-like value scan",
        ),
        _check(
            "traceback_leak",
            "fail" if _TRACEBACK_PATTERN.search(markdown_text) else "pass",
            "traceback scan",
        ),
        _check(
            "raw_transcript_leak",
            "fail" if _RAW_TRANSCRIPT_LEAK_PATTERN.search(markdown_text) else "pass",
            "raw transcript dump scan",
        ),
    ]
    review_text = strip_safety_disclaimers(markdown_text)
    matched_guard = _matched_prohibited_guard(review_text)
    checks.append(
        _check(
            "prohibited_advice",
            "fail" if matched_guard else "pass",
            f"matched_guard={matched_guard}" if matched_guard else "no prohibited advice",
        )
    )
    checks.append(_external_status_check(markdown_text))
    checks.append(
        _check(
            "evidence_separation_markdown",
            "pass"
            if all(
                phrase.lower() in markdown_text.lower()
                for phrase in ("direct podcast evidence", "inferred", "external")
            )
            else "warn",
            "direct podcast evidence / inferred / external wording scan",
        )
    )
    checks.append(
        _check(
            "gooaye_lens_coverage",
            "pass" if _LENS_PATTERN.search(markdown_text) else "warn",
            "Gooaye Lens dimension wording scan",
        )
    )
    return checks


def _external_status_check(markdown_text: str) -> dict[str, str]:
    token_lines = [
        line for line in markdown_text.splitlines() if _EXTERNAL_STATUS_TOKEN_PATTERN.search(line)
    ]
    if not token_lines:
        return _check("external_status_boundary", "na", "no unavailable external status tokens")
    weak_lines = [
        line for line in token_lines if not _EXTERNAL_STATUS_CONTEXT_PATTERN.search(line)
    ]
    if weak_lines:
        return _check(
            "external_status_boundary",
            "warn",
            "external status token appears without unavailable-data context",
        )
    return _check(
        "external_status_boundary",
        "pass",
        "external status tokens are described as unavailable or not market facts",
    )


def _review_status(checks: list[dict[str, str]]) -> str:
    if any(check["status"] == "blocked" for check in checks):
        return "blocked"
    if any(check["status"] == "fail" for check in checks):
        return "failed"
    return "passed"


def _check(name: str, status: str, message: str) -> dict[str, str]:
    return {"name": name, "status": status, "message": message}


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Research LLM Smoke Review",
        "",
        "## Metadata",
        "",
        f"- Review status: {payload['review_status']}",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Episode ref: {payload['episode_ref']}",
        f"- Stock query: {payload['stock_query']}",
        f"- Provider / model: {payload.get('provider')} / {payload.get('model')}",
        f"- LLM input boundary: {payload.get('llm_input_boundary')}",
        f"- Synthesis JSON: `{payload['synthesis_json_path']}`",
        f"- Synthesis Markdown: `{payload['synthesis_markdown_path']}`",
        "",
        "## Quality Checks",
        "",
        "| Check | Status | Notes |",
        "| --- | --- | --- |",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {check['message']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This review report is deterministic.",
            "- It does not call an LLM, read `.env`, fetch external market data, or rewrite synthesis artifacts.",
            "- This heuristic quality gate does not replace manual review.",
        ]
    )
    return "\n".join(lines) + "\n"


def _next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    suffix_index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{suffix_index}{path.suffix}")
        if not candidate.exists():
            return candidate
        suffix_index += 1
