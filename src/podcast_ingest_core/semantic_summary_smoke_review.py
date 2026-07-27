from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import json
from pathlib import Path
import uuid

from .artifact_lock import exclusive_artifact_claim
from .generation_proof import notify_child_artifact_committed
from .models import SemanticSummarySmokeReviewResult
from .semantic_review_artifact import (
    inspect_semantic_review_file,
    semantic_review_payload,
)
from .semantic_summary_identity import canonical_semantic_summary_path
from . import storage


REPORTS_DIR = Path("evals") / "research-llm-smoke" / "reports"


def review_semantic_summary_smoke(
    podcast_id: str,
    episode_ref: str,
    *,
    workflow_stdout_path: str | Path | None = None,
) -> SemanticSummarySmokeReviewResult:
    """Create one atomic deterministic review of the canonical semantic summary."""

    workflow_path = Path(workflow_stdout_path) if workflow_stdout_path is not None else None
    summary_path = _find_semantic_summary_path(podcast_id, episode_ref)
    summary_bytes, unavailable_message = _read_summary_bytes(summary_path)
    payload, evaluation = semantic_review_payload(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        semantic_summary_path=summary_path,
        semantic_summary_bytes=summary_bytes,
        workflow_stdout_path=workflow_path,
        unavailable_message=unavailable_message,
    )
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_path = REPORTS_DIR / (
        f"{timestamp}__{storage.title_slug(podcast_id, 'podcast')}"
        f"__{storage.title_slug(episode_ref, 'episode')}.semantic-review.json"
    )
    markdown = _render_markdown(payload)
    with _claimed_report_paths(base_path) as (report_json_path, report_markdown_path):
        _publish_review_artifacts(report_json_path, report_markdown_path, payload, markdown)
        # JSON is the commit marker.  For a readable summary, ensure the neutral
        # inspector agrees with the exact claimed artifact before returning it.
        if (
            summary_path is not None
            and summary_bytes is not None
            and evaluation.semantic_summary_sha256 is not None
        ):
            inspection = inspect_semantic_review_file(
                podcast_id,
                episode_ref,
                semantic_summary_path=summary_path,
                review_path=report_json_path,
                review_reports_dir=REPORTS_DIR,
            )
            if (
                inspection.review_path != report_json_path
                or inspection.summary_sha256 != evaluation.semantic_summary_sha256
                or inspection.review_status != evaluation.review_status
            ):
                raise RuntimeError("semantic review artifact did not pass neutral inspection")
    if evaluation.review_status == "passed":
        notify_child_artifact_committed(
            "semantic_review",
            report_json_path,
            generated=True,
            metadata={"review_status": evaluation.review_status},
        )

    return SemanticSummarySmokeReviewResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        review_status=evaluation.review_status,
        review_json_path=report_json_path,
        review_markdown_path=report_markdown_path,
        semantic_summary_path=summary_path,
        workflow_stdout_path=workflow_path,
        check_count=len(evaluation.checks),
        failed_check_count=evaluation.failed_check_count,
        warning_count=evaluation.warning_count,
        blocked_check_count=evaluation.blocked_check_count,
    )


def _find_semantic_summary_path(podcast_id: str, episode_ref: str) -> Path | None:
    """Return only the transcript-title-bound semantic summary, never a glob winner."""

    return canonical_semantic_summary_path(podcast_id, episode_ref)


def _read_summary_bytes(path: Path | None) -> tuple[bytes | None, str | None]:
    if path is None:
        return None, "missing canonical semantic summary"
    try:
        return path.read_bytes(), None
    except OSError:
        return None, f"missing: {path}"


@contextmanager
def _claimed_report_paths(base_path: Path):
    """Reserve one collision-safe report pair for the whole writer critical section."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        candidate = (
            base_path
            if index == 1
            else base_path.with_name(f"{base_path.stem}-{index}{base_path.suffix}")
        )
        claim_path = candidate.with_name(f".{candidate.name}.claim")
        try:
            claim = exclusive_artifact_claim(claim_path, timeout_seconds=0.0)
            claim.__enter__()
        except TimeoutError:
            index += 1
            continue
        try:
            if candidate.exists() or candidate.with_suffix(".md").exists():
                index += 1
                continue
            yield candidate, candidate.with_suffix(".md")
            return
        finally:
            claim.__exit__(None, None, None)


def _publish_review_artifacts(
    report_json_path: Path,
    report_markdown_path: Path,
    payload: dict,
    markdown: str,
) -> None:
    """Write invocation-unique staging files; JSON is committed last."""

    stage_token = uuid.uuid4().hex
    markdown_stage = report_markdown_path.with_name(
        f".{report_markdown_path.name}.{stage_token}.part"
    )
    json_stage = report_json_path.with_name(f".{report_json_path.name}.{stage_token}.part")
    markdown_committed = False
    try:
        markdown_stage.write_text(markdown, encoding="utf-8")
        json_stage.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        markdown_stage.replace(report_markdown_path)
        markdown_committed = True
        # A reader treats JSON as the commit marker, so it is committed only after
        # its Markdown companion is completely in place.
        json_stage.replace(report_json_path)
    except Exception:
        if markdown_committed:
            try:
                report_markdown_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    finally:
        for stage_path in (markdown_stage, json_stage):
            try:
                stage_path.unlink(missing_ok=True)
            except OSError:
                pass


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


# Compatibility seam retained for callers that used the old collision helper.
def _next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    suffix_index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{suffix_index}{path.suffix}")
        if not candidate.exists():
            return candidate
        suffix_index += 1
