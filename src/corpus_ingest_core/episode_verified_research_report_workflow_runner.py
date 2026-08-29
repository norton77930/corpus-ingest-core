"""SPEC 019: explicit-episode verified research report (assemble/publish only)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
from typing import Any, Literal

from .errors import (
    EpisodeVerifiedResearchReportWorkflowRunnerFailedError,
    VerifiedResearchReportInputError,
)
from .models import EpisodeVerifiedResearchReportWorkflowRunResult
from .verified_research_report import (
    VerifiedResearchReportAssembly,
    VerifiedResearchReportBundle,
    assemble_verified_research_report,
    publish_verified_research_report_bundle,
)

_RESERVED_SELECTORS = frozenset({"latest", "next"})
# Closed patterns owned by lineage/assembly error text (spaces form of role names).
_ROLE_LINEAGE_RE = re.compile(
    r"^verified report (?P<role>.+?) lineage is stale or invalid$"
)
_EXACT_GATE_MESSAGES: dict[str, tuple[str, Literal["missing", "stale", "gate"]]] = {
    "verified report lineage is missing or untrusted": ("lineage", "missing"),
    "verified report lineage is invalid": ("lineage", "gate"),
    "verified report lineage role selection is invalid": ("lineage", "gate"),
    "verified report canonical transcript is missing": ("transcript", "missing"),
    "verified report canonical transcript is ambiguous": ("transcript", "gate"),
    "verified report semantic review is not current and passed": (
        "semantic_review",
        "stale",
    ),
    "verified report semantic review lineage is unavailable": (
        "semantic_review",
        "missing",
    ),
    "verified report semantic review lineage mode is invalid": (
        "semantic_review",
        "gate",
    ),
    "verified report transcript artifact contract is invalid": (
        "transcript",
        "gate",
    ),
    "verified report semantic summary identity is invalid": (
        "semantic_summary",
        "stale",
    ),
}


IssueKind = Literal["missing", "stale", "gate"]


@dataclass(frozen=True)
class ReadinessIssue:
    """One structured readiness failure (no free-text role guessing)."""

    role: str
    kind: IssueKind


@dataclass(frozen=True)
class ReadinessSnapshot:
    """Authority: assemble succeeds iff ready; issues only when not ready."""

    ready: bool
    assembly: VerifiedResearchReportAssembly | None
    issues: list[ReadinessIssue] = field(default_factory=list)

    @property
    def missing_roles(self) -> list[str]:
        return [i.role for i in self.issues if i.kind == "missing"]

    @property
    def stale_roles(self) -> list[str]:
        return [i.role for i in self.issues if i.kind == "stale"]

    @property
    def failed_gates(self) -> list[str]:
        return [i.role for i in self.issues if i.kind == "gate"]


def run_episode_verified_research_report_workflow(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
) -> EpisodeVerifiedResearchReportWorkflowRunResult:
    """Preview readiness or assemble/publish an 018-equivalent report for one episode.

    Confirmed work never constructs LLM providers, never requires api_cost_ack,
    never hits RSS, and never dispatches 015–017 or research-workflow children.
    """

    podcast_id = _require_non_empty_str(podcast_id, "podcast_id")
    episode_ref = _normalize_episode_ref(episode_ref)
    if not isinstance(confirm, bool):
        raise EpisodeVerifiedResearchReportWorkflowRunnerFailedError("confirm is invalid")
    if not isinstance(include_fixture_verification, bool):
        raise EpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "include_fixture_verification is invalid"
        )
    if stock_query is not None and (
        not isinstance(stock_query, str) or not stock_query.strip()
    ):
        raise EpisodeVerifiedResearchReportWorkflowRunnerFailedError("stock_query is invalid")
    normalized_stock = stock_query.strip() if isinstance(stock_query, str) else None

    readiness = _inspect_readiness(
        podcast_id,
        episode_ref,
        stock_query=normalized_stock,
        include_fixture_verification=include_fixture_verification,
    )
    if not confirm:
        return _build_result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            outcome="ready" if readiness.ready else "blocked",
            ready=readiness.ready,
            readiness=readiness,
            stock_query=normalized_stock,
            include_fixture_verification=include_fixture_verification,
        )

    if not readiness.ready or readiness.assembly is None:
        return _build_result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=True,
            outcome="blocked",
            ready=False,
            readiness=readiness,
            stock_query=normalized_stock,
            include_fixture_verification=include_fixture_verification,
        )

    try:
        bundle = publish_verified_research_report_bundle(readiness.assembly)
    except VerifiedResearchReportInputError as exc:
        publish_readiness = ReadinessSnapshot(
            ready=False,
            assembly=None,
            issues=_issues_from_input_error(str(exc))
            or [ReadinessIssue(role="publication", kind="gate")],
        )
        return _build_result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=True,
            outcome="blocked",
            ready=False,
            readiness=publish_readiness,
            stock_query=normalized_stock,
            include_fixture_verification=include_fixture_verification,
        )

    return _build_result(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=True,
        outcome="reused" if bundle.reused else "completed",
        ready=True,
        readiness=readiness,
        bundle=bundle,
        stock_query=normalized_stock,
        include_fixture_verification=include_fixture_verification,
    )


def result_to_dict(result: EpisodeVerifiedResearchReportWorkflowRunResult) -> dict[str, Any]:
    """Serialize result to JSON-safe metadata only."""

    payload = asdict(result)
    for key in (
        "bundle_dir",
        "report_json_path",
        "report_markdown_path",
        "manifest_path",
    ):
        value = payload.get(key)
        if isinstance(value, Path):
            payload[key] = value.as_posix()
    return payload


def issues_from_verified_report_message(message: str) -> list[ReadinessIssue]:
    """Map owned assembly/lineage error text to structured issues (testable)."""

    return _issues_from_input_error(message)


def _inspect_readiness(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool,
) -> ReadinessSnapshot:
    try:
        assembly = assemble_verified_research_report(
            podcast_id,
            episode_ref,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
        )
    except VerifiedResearchReportInputError as exc:
        issues = _issues_from_input_error(str(exc)) or [
            ReadinessIssue(role="readiness", kind="gate")
        ]
        return ReadinessSnapshot(ready=False, assembly=None, issues=issues)
    except Exception as exc:  # pragma: no cover - defensive bounded gate
        return ReadinessSnapshot(
            ready=False,
            assembly=None,
            issues=[ReadinessIssue(role=type(exc).__name__, kind="gate")],
        )
    return ReadinessSnapshot(ready=True, assembly=assembly, issues=[])


def _issues_from_input_error(message: str) -> list[ReadinessIssue]:
    """Only recognize stable, code-owned error shapes; never freestyle keyword scan."""

    text = message.strip()
    exact = _EXACT_GATE_MESSAGES.get(text)
    if exact is not None:
        role, kind = exact
        return [ReadinessIssue(role=role, kind=kind)]

    match = _ROLE_LINEAGE_RE.fullmatch(text)
    if match is not None:
        role = match.group("role").strip().replace(" ", "_")
        # "stale or invalid" from lineage validator covers both missing record and mismatch.
        kind: IssueKind = "stale"
        return [ReadinessIssue(role=role, kind=kind)]

    if "lineage is missing or untrusted" in text:
        return [ReadinessIssue(role="lineage", kind="missing")]
    if "lineage" in text and "stale or invalid" in text:
        # Prefer regex above; this is a safety net for minor wording drift of the same shape.
        relaxed = re.search(
            r"verified report (?P<role>[a-z0-9_ ]+?) lineage is stale or invalid",
            text,
        )
        if relaxed is not None:
            role = relaxed.group("role").strip().replace(" ", "_")
            return [ReadinessIssue(role=role, kind="stale")]
        return [ReadinessIssue(role="lineage", kind="stale")]

    return []


def _build_result(
    *,
    podcast_id: str,
    episode_ref: str,
    confirm: bool,
    outcome: str,
    ready: bool,
    readiness: ReadinessSnapshot,
    stock_query: str | None,
    include_fixture_verification: bool,
    bundle: VerifiedResearchReportBundle | None = None,
    warnings: list[str] | None = None,
) -> EpisodeVerifiedResearchReportWorkflowRunResult:
    assembly = readiness.assembly
    return EpisodeVerifiedResearchReportWorkflowRunResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=confirm,
        outcome=outcome,
        ready=ready,
        missing_roles=list(readiness.missing_roles),
        stale_roles=list(readiness.stale_roles),
        failed_gates=list(readiness.failed_gates),
        report_version=None if bundle is None else assembly.report_version if assembly else None,
        source_digest=None if bundle is None else assembly.source_digest if assembly else None,
        bundle_dir=None if bundle is None else bundle.bundle_dir,
        report_json_path=None if bundle is None else bundle.report_json_path,
        report_markdown_path=None if bundle is None else bundle.report_markdown_path,
        manifest_path=None if bundle is None else bundle.manifest_path,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
        warnings=list(warnings or []),
        not_investment_advice=True,
    )


def _normalize_episode_ref(episode_ref: str) -> str:
    if not isinstance(episode_ref, str) or not episode_ref.strip():
        raise EpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "episode_ref is invalid"
        )
    normalized = episode_ref.strip()
    if normalized.casefold() in _RESERVED_SELECTORS:
        raise EpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "episode_ref rejects reserved latest selectors"
        )
    return normalized


def _require_non_empty_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EpisodeVerifiedResearchReportWorkflowRunnerFailedError(f"{name} is invalid")
    return value.strip()
