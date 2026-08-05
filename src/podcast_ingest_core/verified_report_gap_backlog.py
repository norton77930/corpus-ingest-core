"""Read-only verified-report gap backlog (projection of SPEC 022 coverage)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .errors import (
    VerifiedReportGapBacklogInputError,
    VerifiedResearchReportCoverageInputError,
)
from .models import VerifiedReportGapBacklogPage, VerifiedReportGapBacklogRow
from .verified_research_report_coverage import list_verified_research_report_coverage

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100


def list_verified_report_gap_backlog(
    podcast_id: str,
    *,
    limit: int = _DEFAULT_LIMIT,
) -> VerifiedReportGapBacklogPage:
    """List inventory episodes missing a verified report bundle (zero-write)."""

    try:
        page = list_verified_research_report_coverage(
            podcast_id,
            has_bundle=False,
            limit=limit,
        )
    except VerifiedResearchReportCoverageInputError as exc:
        raise VerifiedReportGapBacklogInputError(str(exc) or "gap backlog input is invalid") from exc

    items = [
        VerifiedReportGapBacklogRow(
            podcast_id=row.podcast_id,
            episode_ref=row.episode_ref,
            inventory_present=row.inventory_present,
        )
        for row in page.items
    ]
    return VerifiedReportGapBacklogPage(
        podcast_id=page.podcast_id,
        items=items,
        limit=page.limit,
        returned_count=page.returned_count,
        gap_count=page.without_bundle_count,
        inventory_episode_count=page.inventory_episode_count,
        coverage_status=page.coverage_status,
        catalog_root_status=page.catalog_root_status,
        not_investment_advice=True,
    )


def result_to_dict(result: VerifiedReportGapBacklogPage) -> dict[str, Any]:
    """Serialize backlog page to JSON-safe scalars and lists only."""

    return asdict(result)
