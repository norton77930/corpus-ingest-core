"""Read-only episode-centric coverage of verified research report bundles."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Any

from .corpus_index import discover_local_episode_refs
from .errors import (
    VerifiedResearchReportCatalogInputError,
    VerifiedResearchReportCoverageInputError,
)
from .models import (
    VerifiedResearchReportCoveragePage,
    VerifiedResearchReportCoverageRow,
)
from .verified_research_report_catalog import (
    discover_eligible_report_summaries,
    require_safe_podcast_id,
)

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100
_MAX_DIGESTS = 10
_RESERVED_EPISODE_REFS = frozenset({"latest", "next"})


def list_verified_research_report_coverage(
    podcast_id: str,
    *,
    has_bundle: bool | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> VerifiedResearchReportCoveragePage:
    """Join local inventory episode refs with 020-safe bundle summaries for one podcast."""

    normalized_podcast_id = _validate_podcast_id(podcast_id)
    normalized_has_bundle = _validate_optional_bool(has_bundle, "has_bundle")
    normalized_limit = _validate_limit(limit)

    inventory_set = {
        ref
        for ref in discover_local_episode_refs(normalized_podcast_id)
        if ref.casefold() not in _RESERVED_EPISODE_REFS
    }
    summaries, catalog_root_status, coverage_status = discover_eligible_report_summaries(
        podcast_id=normalized_podcast_id
    )

    digests_by_episode: dict[str, list[str]] = defaultdict(list)
    for summary in summaries:
        if summary.episode_ref.casefold() in _RESERVED_EPISODE_REFS:
            continue
        digests_by_episode[summary.episode_ref].append(summary.source_digest)
    for episode_ref, digests in digests_by_episode.items():
        digests_by_episode[episode_ref] = sorted(set(digests))

    all_refs = sorted(inventory_set | set(digests_by_episode.keys()))
    rows: list[VerifiedResearchReportCoverageRow] = []
    with_bundle = 0
    without_bundle = 0
    orphan_count = 0
    for episode_ref in all_refs:
        digests = digests_by_episode.get(episode_ref, [])
        bundle_count = len(digests)
        inventory_present = episode_ref in inventory_set
        has = bundle_count > 0
        if inventory_present and has:
            with_bundle += 1
        elif inventory_present and not has:
            without_bundle += 1
        elif not inventory_present and has:
            orphan_count += 1
        rows.append(
            VerifiedResearchReportCoverageRow(
                podcast_id=normalized_podcast_id,
                episode_ref=episode_ref,
                inventory_present=inventory_present,
                has_bundle=has,
                bundle_count=bundle_count,
                source_digests=digests[:_MAX_DIGESTS],
            )
        )

    filtered = (
        rows if normalized_has_bundle is None else [row for row in rows if row.has_bundle is normalized_has_bundle]
    )
    page_items = filtered[:normalized_limit]
    return VerifiedResearchReportCoveragePage(
        podcast_id=normalized_podcast_id,
        items=page_items,
        limit=normalized_limit,
        returned_count=len(page_items),
        inventory_episode_count=len(inventory_set),
        bundle_episode_count=len(digests_by_episode),
        with_bundle_count=with_bundle,
        without_bundle_count=without_bundle,
        orphan_bundle_episode_count=orphan_count,
        coverage_status=coverage_status,
        catalog_root_status=catalog_root_status,
        not_investment_advice=True,
    )


def result_to_dict(result: VerifiedResearchReportCoveragePage) -> dict[str, Any]:
    """Serialize coverage page to JSON-safe scalars and lists only."""

    return asdict(result)


def _validate_podcast_id(value: str) -> str:
    try:
        return require_safe_podcast_id(value)
    except VerifiedResearchReportCatalogInputError as exc:
        raise VerifiedResearchReportCoverageInputError("podcast_id is invalid") from exc


def _validate_optional_bool(value: bool | None, field: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise VerifiedResearchReportCoverageInputError(f"{field} must be a boolean or omitted")
    return value


def _validate_limit(limit: int) -> int:
    if type(limit) is not int or not (1 <= limit <= _MAX_LIMIT):
        raise VerifiedResearchReportCoverageInputError("limit must be an integer from 1 to 100")
    return limit
