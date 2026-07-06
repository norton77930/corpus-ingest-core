from __future__ import annotations

from datetime import datetime
import json
import re
from pathlib import Path

from .models import SemanticSummarySmokeReviewResult
from . import storage
from .stock_lens_synthesis import _strip_safety_disclaimers


REVIEW_MODE = "semantic-summary-smoke-review-v1"
REPORTS_DIR = Path("evals") / "research-llm-smoke" / "reports"
_TIMESTAMP_EVIDENCE_PATTERN = re.compile(
    r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]"
)
_SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
_TRACEBACK_PATTERN = re.compile(r"Traceback\s+\(most recent call last\):")
_RAW_TRANSCRIPT_DUMP_PATTERN = re.compile(
    r"raw transcript\s*(?:text|dump|content)\s*[:：]", re.IGNORECASE
)
_SEMANTIC_PROHIBITED_ADVICE_PATTERNS = [
    ("trade_action", re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:buy|sell|hold)\b")),
    (
        "trade_action",
        re.compile(r"(?:建議|不建議|應該|可以|可考慮|不要)\s*(?:買進|賣出|持有)"),
    ),
    (
        "target_price",
        re.compile(r"\btarget\s+price\s*(?:of|is|:)?\s*\$?\d", re.IGNORECASE),
    ),
    (
        "target_price",
        re.compile(r"目標價\s*(?:為|是|:|：)?\s*[\d一二三四五六七八九十百千萬]"),
    ),
    (
        "guaranteed_return",
        re.compile(r"\bguaranteed\s+returns?\s*(?:of|is|:)?\s*\d?", re.IGNORECASE),
    ),
    ("guaranteed_return", re.compile(r"保證報酬")),
]


def review_semantic_summary_smoke(
    podcast_id: str,
    episode_ref: str,
    *,
    workflow_stdout_path: str | Path | None = None,
) -> SemanticSummarySmokeReviewResult:
    """Create a deterministic review report for an existing semantic summary."""

    workflow_path = Path(workflow_stdout_path) if workflow_stdout_path is not None else None
    summary_path = _find_semantic_summary_path(podcast_id, episode_ref)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_json_path = _next_available_path(
        REPORTS_DIR
        / (
            f"{timestamp}__{storage.title_slug(podcast_id, 'podcast')}"
            f"__{storage.title_slug(episode_ref, 'episode')}.semantic-review.json"
        )
    )
    report_markdown_path = report_json_path.with_suffix(".md")

    markdown_text, checks = _load_markdown(summary_path)
    if markdown_text is not None:
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
        "semantic_summary_path": str(summary_path) if summary_path is not None else None,
        "workflow_stdout_path": str(workflow_path) if workflow_path is not None else None,
        "check_count": len(checks),
        "failed_check_count": failed_count,
        "warning_count": warning_count,
        "blocked_check_count": blocked_count,
        "checks": checks,
        "not_investment_advice_notice": True,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_markdown_path.write_text(_render_markdown(report_payload), encoding="utf-8")

    return SemanticSummarySmokeReviewResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        review_status=review_status,
        review_json_path=report_json_path,
        review_markdown_path=report_markdown_path,
        semantic_summary_path=summary_path,
        workflow_stdout_path=workflow_path,
        check_count=len(checks),
        failed_check_count=failed_count,
        warning_count=warning_count,
        blocked_check_count=blocked_count,
    )


def _find_semantic_summary_path(podcast_id: str, episode_ref: str) -> Path | None:
    summary_dir = storage.SUMMARIES_DIR / storage.title_slug(podcast_id, "podcast")
    matches = sorted(summary_dir.glob(f"{storage.title_slug(episode_ref, 'episode')}__*.semantic.md"))
    return matches[0] if matches else None


def _load_markdown(path: Path | None) -> tuple[str | None, list[dict[str, str]]]:
    if path is None:
        return None, [_check("semantic_summary_exists", "blocked", "missing semantic summary")]
    if not path.exists():
        return None, [_check("semantic_summary_exists", "blocked", f"missing: {path}")]
    try:
        return path.read_text(encoding="utf-8"), [
            _check("semantic_summary_exists", "pass", str(path))
        ]
    except OSError as exc:
        return None, [_check("semantic_summary_readable", "blocked", str(exc))]


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
            "raw_transcript_dump",
            "fail" if _RAW_TRANSCRIPT_DUMP_PATTERN.search(markdown_text) else "pass",
            "raw transcript dump marker scan",
        ),
        _check(
            "timestamp_evidence",
            "pass" if _TIMESTAMP_EVIDENCE_PATTERN.search(markdown_text) else "warn",
            "timestamp evidence scan",
        ),
        _check(
            "chunk_summaries",
            "pass" if "## Chunk Summaries" in markdown_text else "warn",
            "chunk summaries section scan",
        ),
        _check(
            "metadata",
            "pass"
            if all(
                phrase in markdown_text
                for phrase in ("Summary mode: semantic-llm", "Provider:", "Model:", "Transcript status:")
            )
            else "warn",
            "metadata/provider/model/status scan",
        ),
    ]
    review_text = _strip_safety_disclaimers(markdown_text)
    matched_guard = _matched_semantic_prohibited_guard(review_text)
    checks.append(
        _check(
            "prohibited_advice",
            "fail" if matched_guard else "pass",
            f"matched_guard={matched_guard}" if matched_guard else "no prohibited advice",
        )
    )
    return checks


def _review_status(checks: list[dict[str, str]]) -> str:
    if any(check["status"] == "blocked" for check in checks):
        return "blocked"
    if any(check["status"] == "fail" for check in checks):
        return "failed"
    return "passed"


def _matched_semantic_prohibited_guard(text: str) -> str | None:
    for name, pattern in _SEMANTIC_PROHIBITED_ADVICE_PATTERNS:
        if pattern.search(text):
            return name
    return None


def _check(name: str, status: str, message: str) -> dict[str, str]:
    return {"name": name, "status": status, "message": message}


def _render_markdown(payload: dict) -> str:
    lines = [
        "# Semantic Summary Smoke Review",
        "",
        "## Metadata",
        "",
        f"- Review status: {payload['review_status']}",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Episode ref: {payload['episode_ref']}",
        f"- Semantic summary: `{payload['semantic_summary_path']}`",
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
            "- It does not call an LLM, read `.env`, fetch external market data, or rewrite semantic summary artifacts.",
            "- Semantic summary may contain transcript-derived text; review reports do not add new LLM content.",
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
