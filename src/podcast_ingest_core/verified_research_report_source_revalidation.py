"""Read-only exact-bundle source revalidation for SPEC 021."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from . import storage
from .errors import (
    VerifiedResearchReportInputError,
    VerifiedResearchReportSourceRevalidationInputError,
)
from .models import (
    VerifiedResearchReportCatalogItem,
    VerifiedResearchReportSourceRevalidation,
)
from .verified_research_report import (
    REPORT_SCHEMA_VERSION,
    _canonical_source_path,
    _current_verified_research_source_snapshot,
    _safe_path,
    _normalize_stock_query,
    _source_digest,
)
from .verified_research_report_catalog import _exact_bundle_evidence


_CHECK_NAMES = (
    "bundle_self_consistency",
    "assembly_options",
    "current_lineage",
    "published_lineage_match",
    "source_artifact_metadata_match",
    "source_digest_match",
)
_ARTIFACT_ROLES = frozenset({
    "transcript", "semantic_summary", "semantic_review", "mentions",
    "intelligence", "industry_mapping", "external_boundary", "fixture", "stock_lens",
})
_CLOSED_ROLES = _ARTIFACT_ROLES | frozenset({"lineage", "source_digest"})
_FAILED_ROLE_ORDER = (
    "transcript", "semantic_summary", "semantic_review", "mentions",
    "intelligence", "industry_mapping", "external_boundary", "fixture", "stock_lens",
    "lineage", "source_digest",
)


def revalidate_verified_research_report_sources(
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> VerifiedResearchReportSourceRevalidation:
    """Revalidate exactly one published bundle's canonical local sources.

    Published manifest values are comparison-only.  In particular, no manifest
    source, lineage, fixture, snapshot, or path field is used to select a file.
    """

    locator = _validate_locator(podcast_id, episode_ref, source_digest)
    evidence = _exact_bundle_evidence(locator)
    checks = _checks_for_bundle(evidence.status)
    if evidence.status != "valid":
        return _result(locator, evidence.status, "not_evaluated", "not_evaluated", checks)

    options = _supported_assembly_options(evidence.manifest)
    if options is None:
        checks["assembly_options"] = "invalid"
        return _result(locator, "valid", "not_evaluated", "stale_or_invalid", checks, evidence)
    checks["assembly_options"] = "valid"
    stock_query, include_fixture_verification = options

    try:
        snapshot = _current_verified_research_source_snapshot(
            locator["podcast_id"], locator["episode_ref"], stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
        )
    except VerifiedResearchReportInputError as exc:
        lineage_status = "missing" if "lineage is missing" in str(exc) else "stale_or_invalid"
        checks["current_lineage"] = lineage_status
        return _result(
            locator, "valid", lineage_status, "stale_or_invalid", checks, evidence, ["lineage"]
        )
    except Exception:
        checks["current_lineage"] = "stale_or_invalid"
        return _result(
            locator, "valid", "stale_or_invalid", "stale_or_invalid", checks, evidence, ["lineage"]
        )

    checks["current_lineage"] = "current"
    published_lineage_match = evidence.manifest.get("lineage") == snapshot.lineage_manifest
    checks["published_lineage_match"] = "match" if published_lineage_match else "mismatch"
    metadata_failed_roles = _metadata_failed_roles(
        evidence.manifest.get("source_artifacts"), snapshot.source_artifacts
    )
    checks["source_artifact_metadata_match"] = (
        "match" if not metadata_failed_roles else "mismatch"
    )
    recomputed_digest = _source_digest(
        podcast_id=locator["podcast_id"], episode_ref=locator["episode_ref"],
        stock_query=stock_query, include_fixture_verification=include_fixture_verification,
        sources=snapshot.source_artifacts,
    )
    digest_match = recomputed_digest == locator["source_digest"]
    checks["source_digest_match"] = "match" if digest_match else "mismatch"

    stable_roles, lineage_stable = _stable_snapshot_roles(
        locator, stock_query, include_fixture_verification, snapshot
    )
    failed_roles = set(metadata_failed_roles) | stable_roles
    if not published_lineage_match or not lineage_stable:
        failed_roles.add("lineage")
    if not digest_match:
        failed_roles.add("source_digest")
    failed_roles = _ordered_failed_roles(failed_roles)
    if stable_roles:
        checks["source_artifact_metadata_match"] = "mismatch"
    if not lineage_stable:
        checks["current_lineage"] = "stale_or_invalid"
    lineage_status = (
        "current" if published_lineage_match and lineage_stable
        else "mismatch" if not published_lineage_match
        else "stale_or_invalid"
    )
    current = (
        lineage_status == "current"
        and not failed_roles
        and checks["source_digest_match"] == "match"
    )
    return _result(
        locator, "valid", lineage_status,
        "current" if current else "stale_or_invalid", checks, evidence, failed_roles,
    )


def _supported_assembly_options(manifest: object) -> tuple[str | None, bool] | None:
    options = manifest.get("assembly_options") if isinstance(manifest, dict) else None
    if not isinstance(options, dict) or set(options) != {
        "stock_query", "include_fixture_verification", "verification_scope",
    }:
        return None
    if (
        not isinstance(options.get("include_fixture_verification"), bool)
        or options.get("verification_scope") != "local_artifact_and_fixture"
    ):
        return None
    try:
        stock_query = _normalize_stock_query(options.get("stock_query"))
    except VerifiedResearchReportInputError:
        return None
    return stock_query, options["include_fixture_verification"]


def _metadata_failed_roles(published: object, sources: list[Any]) -> list[str]:
    """Compare manifest metadata only; published path strings are never opened."""

    expected_roles = [source.role for source in sources]
    if not expected_roles or any(role not in _ARTIFACT_ROLES for role in expected_roles):
        # A malformed internal snapshot still must not make a valid bundle current.
        # Use an approved generic artifact role rather than exposing an unknown role.
        return ["transcript"]
    if (
        not isinstance(published, list)
        or len(published) != len(expected_roles)
        or len(set(expected_roles)) != len(expected_roles)
    ):
        return _ordered_failed_roles(set(expected_roles))
    failed: set[str] = set()
    for expected_role, item, source in zip(expected_roles, published, sources, strict=True):
        expected = {
            "role": expected_role,
            "sha256": source.sha256,
            "size_bytes": source.size_bytes,
            "identity_valid": source.identity_valid,
        }
        accepted_paths = {_safe_path(source.path), _canonical_source_path(source.path)}
        if (
            not isinstance(item, dict)
            or set(item) != {*expected, "path"}
            or item.get("path") not in accepted_paths
            or any(item.get(key) != value for key, value in expected.items())
        ):
            failed.add(expected_role)
    return _ordered_failed_roles(failed)


def _ordered_failed_roles(roles: set[str]) -> list[str]:
    return [role for role in _FAILED_ROLE_ORDER if role in roles]


def _stable_snapshot_roles(
    locator: dict[str, str], stock_query: str | None, include_fixture_verification: bool,
    first_snapshot: Any,
) -> tuple[set[str], bool]:
    """Return source race roles and whether the independently read lineage is stable."""

    first_roles = {
        source.role for source in first_snapshot.source_artifacts if source.role in _ARTIFACT_ROLES
    }
    try:
        second = _current_verified_research_source_snapshot(
            locator["podcast_id"], locator["episode_ref"], stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
        )
    except Exception:
        return first_roles, False
    if second.lineage_manifest != first_snapshot.lineage_manifest:
        return set(), False
    first = {
        source.role: (_canonical_source_path(source.path), source.sha256, source.size_bytes)
        for source in first_snapshot.source_artifacts
    }
    second_values = {
        source.role: (_canonical_source_path(source.path), source.sha256, source.size_bytes)
        for source in second.source_artifacts
    }
    return {role for role in first if first.get(role) != second_values.get(role)}, True


def _result(
    locator: dict[str, str], bundle_status: str, lineage_status: str,
    currentness_status: str, checks: dict[str, str], evidence: Any | None = None,
    failed_roles: list[str] | None = None,
) -> VerifiedResearchReportSourceRevalidation:
    safe_metadata = evidence.safe_metadata if evidence is not None else None
    return VerifiedResearchReportSourceRevalidation(
        locator=locator,
        bundle_self_consistency_status=bundle_status,
        lineage_revalidation_status=lineage_status,
        source_currentness_status=currentness_status,
        checks=checks,
        failed_roles=failed_roles or [],
        safe_metadata=safe_metadata,
        not_investment_advice=(
            safe_metadata.not_investment_advice if safe_metadata is not None else None
        ),
    )


def result_to_dict(result: VerifiedResearchReportSourceRevalidation) -> dict[str, Any]:
    """Serialize only the closed public revalidation contract."""

    locator = _safe_serialized_locator(result.locator)
    metadata = _safe_serialized_metadata(result.safe_metadata)
    return {
        "locator": locator,
        "bundle_self_consistency_status": _bounded(
            result.bundle_self_consistency_status, {"valid", "invalid", "not_found"}, "invalid"
        ),
        "lineage_revalidation_status": _bounded(
            result.lineage_revalidation_status,
            {"current", "missing", "stale_or_invalid", "mismatch", "not_evaluated"},
            "stale_or_invalid",
        ),
        "source_currentness_status": _bounded(
            result.source_currentness_status,
            {"current", "stale_or_invalid", "not_evaluated"},
            "stale_or_invalid",
        ),
        "checks": _safe_serialized_checks(result.checks),
        "failed_roles": [
            role for role in (result.failed_roles if isinstance(result.failed_roles, list) else [])
            if isinstance(role, str) and role in _CLOSED_ROLES
        ],
        "safe_metadata": asdict(metadata) if metadata is not None else None,
        "not_investment_advice": metadata.not_investment_advice if metadata is not None else None,
    }


def _safe_serialized_locator(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        try:
            return _validate_locator(
                value.get("podcast_id"), value.get("episode_ref"), value.get("source_digest")
            )
        except VerifiedResearchReportSourceRevalidationInputError:
            pass
    return {"podcast_id": "invalid", "episode_ref": "invalid", "source_digest": "0" * 64}


def _safe_serialized_checks(value: object) -> dict[str, str]:
    raw = value if isinstance(value, dict) else {}
    allowed = {
        "bundle_self_consistency": {"valid", "invalid", "not_found"},
        "assembly_options": {"valid", "invalid", "not_evaluated"},
        "current_lineage": {"current", "missing", "stale_or_invalid", "not_evaluated"},
        "published_lineage_match": {"match", "mismatch", "not_evaluated"},
        "source_artifact_metadata_match": {"match", "mismatch", "not_evaluated"},
        "source_digest_match": {"match", "mismatch", "not_evaluated"},
    }
    return {
        name: _bounded(raw.get(name), values, "not_evaluated")
        for name, values in allowed.items()
    }


def _safe_serialized_metadata(value: object) -> VerifiedResearchReportCatalogItem | None:
    if not isinstance(value, VerifiedResearchReportCatalogItem):
        return None
    try:
        locator = _validate_locator(value.podcast_id, value.episode_ref, value.source_digest)
    except VerifiedResearchReportSourceRevalidationInputError:
        return None
    if (
        value.report_version != f"v1-{locator['source_digest']}"
        or value.schema_version != REPORT_SCHEMA_VERSION
        or not isinstance(value.include_fixture_verification, bool)
        or not isinstance(value.stock_query_present, bool)
        or value.semantic_review_status != "passed"
        or value.not_investment_advice is not True
    ):
        return None
    return value


def _bounded(value: object, allowed: set[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def _validate_locator(podcast_id: str, episode_ref: str, source_digest: str) -> dict[str, str]:
    if (
        not isinstance(podcast_id, str)
        or not 1 <= len(podcast_id) <= 128
        or storage._SAFE_SLUG_PATTERN.fullmatch(podcast_id) is None
        or not isinstance(episode_ref, str)
        or not 1 <= len(episode_ref) <= 128
        or not storage.is_safe_episode_ref(episode_ref, max_length=128)
        or episode_ref.casefold() in {"latest", "next"}
        or not isinstance(source_digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", source_digest) is None
    ):
        raise VerifiedResearchReportSourceRevalidationInputError(
            "verified research report source revalidation locator is invalid"
        )
    return {"podcast_id": podcast_id, "episode_ref": episode_ref, "source_digest": source_digest}


def _checks_for_bundle(bundle_status: str) -> dict[str, str]:
    return {
        "bundle_self_consistency": bundle_status,
        **{name: "not_evaluated" for name in _CHECK_NAMES[1:]},
    }
