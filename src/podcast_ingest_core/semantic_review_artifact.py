"""Neutral deterministic semantic-review evaluation and artifact inspection.

The evaluator is intentionally shared by the 015 writer and every reader.  An
artifact is authentic only when its recorded checks are the deterministic result
of evaluating the immutable current summary bytes; a self-consistent payload is
not sufficient evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from . import storage
from .report_safety import contains_sensitive_text, matched_investment_advice_guard
from .secure_local_snapshot import secure_directory_names, secure_read_bytes


_MAX_REVIEW_BYTES = 64 * 1024 * 1024


REVIEW_MODE = "semantic-summary-smoke-review-v1"
REVIEW_BOUNDARY = "deterministic-local-review-no-llm-env-network-or-summary-rewrite-v1"
REVIEW_CHECK_NAMES = (
    "semantic_summary_exists",
    "secret_leak",
    "traceback_leak",
    "raw_transcript_dump",
    "timestamp_evidence",
    "chunk_summaries",
    "metadata",
    "prohibited_advice",
)
REVIEW_STATUS_BY_CHECK = {
    "semantic_summary_exists": {"pass", "blocked"},
    "secret_leak": {"pass", "fail", "blocked"},
    "traceback_leak": {"pass", "fail", "blocked"},
    "raw_transcript_dump": {"pass", "fail", "blocked"},
    "timestamp_evidence": {"pass", "warn", "blocked"},
    "chunk_summaries": {"pass", "warn", "blocked"},
    "metadata": {"pass", "warn", "blocked"},
    "prohibited_advice": {"pass", "fail", "blocked"},
}
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_TIMESTAMP_PATTERN = r"\d{8}-\d{6}"
_TIMESTAMP_EVIDENCE_PATTERN = re.compile(r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]")
_TRACEBACK_PATTERN = re.compile(r"Traceback\s+\(most recent call last\):")
_RAW_TRANSCRIPT_DUMP_PATTERN = re.compile(
    r"raw transcript\s*(?:text|dump|content)\s*[:：]", re.IGNORECASE
)
@dataclass(frozen=True)
class SemanticReviewFilename:
    """Parsed canonical or collision semantic-review filename."""

    path: Path
    timestamp: str
    collision_index: int
    episode_ref: str


@dataclass(frozen=True)
class SemanticReviewEvaluation:
    """Pure evaluation result derived only from one immutable summary byte string."""

    semantic_summary_sha256: str | None
    checks: list[dict[str, str]]
    review_status: str
    failed_check_count: int
    warning_count: int
    blocked_check_count: int


@dataclass(frozen=True)
class SemanticReviewInspection:
    """Current-summary-bound inspection result for a semantic review artifact."""

    summary_status: str
    summary_path: Path | None
    summary_sha256: str | None
    review_status: str
    review_path: Path | None
    review_payload: dict[str, Any] | None
    summary_bytes: bytes | None = None
    review_bytes: bytes | None = None


def evaluate_semantic_review_bytes(
    summary_bytes: bytes | None,
    *,
    semantic_summary_path: Path | None,
    unavailable_message: str | None = None,
) -> SemanticReviewEvaluation:
    """Deterministically evaluate summary bytes without reading files or globals."""

    if summary_bytes is None:
        message = unavailable_message or "missing semantic summary"
        checks = [_check("semantic_summary_exists", "blocked", message)]
        checks.extend(
            _check(name, "blocked", "semantic summary is unavailable")
            for name in REVIEW_CHECK_NAMES[1:]
        )
        return _evaluation(None, checks)
    try:
        markdown = summary_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        checks = [_check("semantic_summary_exists", "blocked", type(exc).__name__)]
        checks.extend(
            _check(name, "blocked", "semantic summary is unavailable")
            for name in REVIEW_CHECK_NAMES[1:]
        )
        return _evaluation(None, checks)

    checks = [_check("semantic_summary_exists", "pass", str(semantic_summary_path))]
    checks.extend(
        (
            _check(
                "secret_leak",
                "fail" if contains_sensitive_text(markdown, reject_any_uri=True) else "pass",
                "credential, private-key, and unsafe URI scan",
            ),
            _check(
                "traceback_leak",
                "fail" if _TRACEBACK_PATTERN.search(markdown) else "pass",
                "stack-trace scan",
            ),
            _check(
                "raw_transcript_dump",
                "fail" if _RAW_TRANSCRIPT_DUMP_PATTERN.search(markdown) else "pass",
                "transcript-dump marker scan",
            ),
            _check(
                "timestamp_evidence",
                "pass" if _TIMESTAMP_EVIDENCE_PATTERN.search(markdown) else "warn",
                "timestamp evidence scan",
            ),
            _check(
                "chunk_summaries",
                "pass" if "## Chunk Summaries" in markdown else "warn",
                "chunk summaries section scan",
            ),
            _check(
                "metadata",
                "pass"
                if all(
                    phrase in markdown
                    for phrase in ("Summary mode: semantic-llm", "Provider:", "Model:", "Transcript status:")
                )
                else "warn",
                "metadata/provider/model/status scan",
            ),
        )
    )
    matched_guard = matched_investment_advice_guard(markdown)
    checks.append(
        _check(
            "prohibited_advice",
            "fail" if matched_guard else "pass",
            f"matched_guard={matched_guard}" if matched_guard else "no prohibited advice",
        )
    )
    return _evaluation(hashlib.sha256(summary_bytes).hexdigest(), checks)


def semantic_review_payload(
    *,
    podcast_id: str,
    episode_ref: str,
    semantic_summary_path: Path | None,
    semantic_summary_bytes: bytes | None,
    workflow_stdout_path: Path | None = None,
    unavailable_message: str | None = None,
) -> tuple[dict[str, Any], SemanticReviewEvaluation]:
    """Build the canonical writer payload from immutable evaluated bytes."""

    evaluation = evaluate_semantic_review_bytes(
        semantic_summary_bytes,
        semantic_summary_path=semantic_summary_path,
        unavailable_message=unavailable_message,
    )
    payload = {
        "review_mode": REVIEW_MODE,
        "review_boundary": REVIEW_BOUNDARY,
        "review_status": evaluation.review_status,
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "semantic_summary_path": str(semantic_summary_path) if semantic_summary_path is not None else None,
        "semantic_summary_sha256": evaluation.semantic_summary_sha256,
        "workflow_stdout_path": str(workflow_stdout_path) if workflow_stdout_path is not None else None,
        "check_count": len(evaluation.checks),
        "failed_check_count": evaluation.failed_check_count,
        "warning_count": evaluation.warning_count,
        "blocked_check_count": evaluation.blocked_check_count,
        "checks": evaluation.checks,
        "not_investment_advice_notice": True,
    }
    return payload, evaluation


def parse_semantic_review_filename(
    path: Path,
    podcast_id: str,
    episode_ref: str | None = None,
) -> SemanticReviewFilename | None:
    """Accept canonical and ``-N`` collision filenames with numeric ordering."""

    safe_podcast = storage.title_slug(podcast_id, "podcast")
    if episode_ref is None:
        episode_pattern = r"(?P<episode>[A-Za-z0-9][A-Za-z0-9-]{0,127})"
    else:
        episode_pattern = re.escape(storage.title_slug(episode_ref, "episode"))
    match = re.fullmatch(
        rf"(?P<timestamp>{_TIMESTAMP_PATTERN})__{re.escape(safe_podcast)}__"
        rf"{episode_pattern}\.semantic-review(?:-(?P<collision>[1-9]\d*))?\.json",
        path.name,
    )
    if match is None:
        return None
    parsed_episode = episode_ref if episode_ref is not None else match.group("episode")
    assert parsed_episode is not None
    collision_text = match.group("collision")
    return SemanticReviewFilename(
        path=path,
        timestamp=match.group("timestamp"),
        collision_index=int(collision_text) if collision_text is not None else 0,
        episode_ref=parsed_episode,
    )


def semantic_review_candidates(
    reports_dir: Path,
    podcast_id: str,
    episode_ref: str,
) -> tuple[list[Path], list[Path]]:
    """Return deterministically ordered valid candidates and rejected lookalikes."""

    safe_podcast = storage.title_slug(podcast_id, "podcast")
    safe_episode = storage.title_slug(episode_ref, "episode")
    parsed: list[SemanticReviewFilename] = []
    rejected: list[Path] = []
    names = secure_directory_names(reports_dir, reports_dir, max_entries=4_096)
    if names is None:
        return [], []
    paths = [
        reports_dir / name
        for name in names
        if fnmatch.fnmatchcase(name, f"*__{safe_podcast}__{safe_episode}.semantic-review*.json")
    ]
    for path in paths:
        candidate = parse_semantic_review_filename(path, podcast_id, episode_ref)
        if candidate is None:
            rejected.append(path)
        else:
            parsed.append(candidate)
    parsed.sort(key=lambda item: (item.timestamp, item.collision_index, item.path.name))
    return [item.path for item in parsed], rejected


def inspect_semantic_review(
    podcast_id: str,
    episode_ref: str,
    *,
    semantic_summary_path: Path,
    review_reports_dir: Path,
    semantic_summary_bytes: bytes | None = None,
) -> SemanticReviewInspection:
    """Inspect the latest authentic review against immutable current summary bytes."""

    summary_raw = semantic_summary_bytes
    if summary_raw is None:
        summary_raw = secure_read_bytes(
            storage.SUMMARIES_DIR, semantic_summary_path, max_bytes=_MAX_REVIEW_BYTES
        )
    if summary_raw is None:
        return SemanticReviewInspection("missing", None, None, "missing", None, None)
    try:
        summary_raw.decode("utf-8")
    except UnicodeDecodeError:
        return SemanticReviewInspection("unavailable", semantic_summary_path, None, "missing", None, None, summary_raw)
    if not summary_raw.strip():
        return SemanticReviewInspection("unavailable", semantic_summary_path, None, "missing", None, None, summary_raw)

    summary_sha256 = hashlib.sha256(summary_raw).hexdigest()
    candidates, rejected = semantic_review_candidates(review_reports_dir, podcast_id, episode_ref)
    latest_authentic: SemanticReviewInspection | None = None
    latest_invalid: SemanticReviewInspection | None = None
    # Filename timestamps are ordering metadata, not authenticity evidence.  An
    # invalid future-name candidate must not mask an older authentic review or a
    # fresh collision rereview; recompute every legal candidate, retaining the
    # latest authentic current-summary-bound payload by canonical filename order.
    for review_path in candidates:
        inspection = inspect_semantic_review_file(
            podcast_id,
            episode_ref,
            semantic_summary_path=semantic_summary_path,
            review_path=review_path,
            review_reports_dir=review_reports_dir,
            semantic_summary_bytes=summary_raw,
        )
        if inspection.review_status == "needs_review":
            latest_invalid = inspection
        else:
            latest_authentic = inspection
    if latest_authentic is not None:
        return latest_authentic
    if latest_invalid is not None:
        return latest_invalid
    if rejected:
        return SemanticReviewInspection(
            "available", semantic_summary_path, summary_sha256, "needs_review",
            rejected[-1], None, summary_raw,
        )
    return SemanticReviewInspection(
        "available", semantic_summary_path, summary_sha256, "missing", None, None, summary_raw
    )


def inspect_semantic_review_file(
    podcast_id: str,
    episode_ref: str,
    *,
    semantic_summary_path: Path,
    review_path: Path,
    review_reports_dir: Path | None = None,
    semantic_summary_bytes: bytes | None = None,
) -> SemanticReviewInspection:
    """Inspect one claimed report path beneath a Core-derived trusted report root."""

    if review_reports_dir is None:
        # Avoid a module cycle while retaining the writer's fixed Core-owned root
        # for direct inspector callers.
        from .semantic_summary_smoke_review import REPORTS_DIR

        review_reports_dir = REPORTS_DIR
    summary_raw = semantic_summary_bytes
    if summary_raw is None:
        summary_raw = secure_read_bytes(
            storage.SUMMARIES_DIR, semantic_summary_path, max_bytes=_MAX_REVIEW_BYTES
        )
    if summary_raw is None:
        return SemanticReviewInspection("missing", None, None, "missing", None, None)
    try:
        summary_raw.decode("utf-8")
    except UnicodeDecodeError:
        return SemanticReviewInspection("unavailable", semantic_summary_path, None, "missing", None, None, summary_raw)
    if not summary_raw.strip():
        return SemanticReviewInspection("unavailable", semantic_summary_path, None, "missing", None, None, summary_raw)
    summary_sha256 = hashlib.sha256(summary_raw).hexdigest()
    review_raw = secure_read_bytes(
        review_reports_dir, review_path, max_bytes=_MAX_REVIEW_BYTES
    )
    try:
        payload = json.loads(review_raw.decode("utf-8")) if review_raw is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return SemanticReviewInspection("available", semantic_summary_path, summary_sha256, "needs_review", review_path, None, summary_raw)
    if review_raw is None:
        return SemanticReviewInspection("available", semantic_summary_path, summary_sha256, "needs_review", review_path, None, summary_raw)
    if not _is_authentic_review_payload(
        payload,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        semantic_summary_path=semantic_summary_path,
        semantic_summary_bytes=summary_raw,
    ):
        return SemanticReviewInspection(
            "available", semantic_summary_path, summary_sha256, "needs_review", review_path,
            payload if isinstance(payload, dict) else None, summary_raw, review_raw,
        )
    assert isinstance(payload, dict)
    return SemanticReviewInspection(
        "available", semantic_summary_path, summary_sha256, payload["review_status"], review_path,
        payload, summary_raw, review_raw,
    )


def _is_authentic_review_payload(
    payload: object,
    *,
    podcast_id: str,
    episode_ref: str,
    semantic_summary_path: Path,
    semantic_summary_bytes: bytes,
) -> bool:
    """Require exact deterministic evaluation, not only internally consistent counts."""

    if not isinstance(payload, dict):
        return False
    expected, evaluation = semantic_review_payload(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        semantic_summary_path=semantic_summary_path,
        semantic_summary_bytes=semantic_summary_bytes,
    )
    required_fields = (
        "review_mode", "review_boundary", "review_status", "podcast_id", "episode_ref",
        "semantic_summary_path", "semantic_summary_sha256", "check_count", "failed_check_count",
        "warning_count", "blocked_check_count", "checks", "not_investment_advice_notice",
    )
    if any(payload.get(field) != expected[field] for field in required_fields):
        return False
    # Protect against a superficially valid value in a field that appears only in
    # old reports.  The SHA format also guards accidental non-canonical hashes.
    review_hash = payload.get("semantic_summary_sha256")
    return isinstance(review_hash, str) and bool(_SHA256_PATTERN.fullmatch(review_hash)) and (
        evaluation.review_status == payload["review_status"]
    )


def _evaluation(
    semantic_summary_sha256: str | None,
    checks: list[dict[str, str]],
) -> SemanticReviewEvaluation:
    failed_count = sum(check["status"] == "fail" for check in checks)
    warning_count = sum(check["status"] == "warn" for check in checks)
    blocked_count = sum(check["status"] == "blocked" for check in checks)
    status = "blocked" if blocked_count else "failed" if failed_count else "passed"
    return SemanticReviewEvaluation(
        semantic_summary_sha256=semantic_summary_sha256,
        checks=checks,
        review_status=status,
        failed_check_count=failed_count,
        warning_count=warning_count,
        blocked_check_count=blocked_count,
    )


def _check(name: str, status: str, message: str) -> dict[str, str]:
    return {"name": name, "status": status, "message": message}
