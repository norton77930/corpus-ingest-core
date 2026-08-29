"""Fail-closed, 018-owned provenance for derived verified-report artifacts.

Legacy artifact schemas intentionally remain consumable by their existing public
workflows.  SPEC 018 therefore records an additive sidecar only after its caller
has established generation/reuse truth.  A sidecar is not inferred from mtimes
or from the mere presence of an artifact: every reuse validates canonical paths,
immutable SHA-256 values, direct upstreams, and the modes/options that affect
meaningful output.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
import uuid

from . import storage
from .canonical_transcript import (
    CanonicalTranscriptResolutionError,
    resolve_canonical_transcript_asset_paths,
)
from .errors import VerifiedResearchReportInputError
from .external_data_verification import VERIFICATION_MODE
from .semantic_review_artifact import REVIEW_BOUNDARY, REVIEW_MODE, inspect_semantic_review
from .secure_local_snapshot import secure_read_bytes


_MAX_LINEAGE_INPUT_BYTES = 64 * 1024 * 1024


LINEAGE_SCHEMA_VERSION = "latest-episode-verified-research-lineage-v2"
LINEAGE_QUALITY_GATE = "passed"
_BASE_ROLES = (
    "transcript",
    "semantic_summary",
    "semantic_review",
    "mentions",
    "intelligence",
    "industry_mapping",
    "external_boundary",
)


@dataclass(frozen=True)
class _CurrentVerifiedResearchLineageEvidence:
    """Split persisted publisher lineage from fresh Core-derived I/O records."""

    publisher_manifest: dict[str, Any]
    current_artifacts: dict[str, dict[str, Any]]


def lineage_path(podcast_id: str, episode_ref: str) -> Path:
    """Return the pure 018-owned lineage-sidecar path."""

    return (
        storage.CORPUS_DIR
        / podcast_id
        / "verified-research"
        / f"{episode_ref}.lineage.json"
    )


def record_current_verified_research_lineage(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool,
    summary_options: dict[str, Any],
    roles: Iterable[str] | None = None,
    generation_proofs: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Record current artifact lineage after a caller-established safe generation.

    This is deliberately not an adoption mechanism.  The workflow only calls it
    for root transcript provenance or artifacts generated during the current
    invocation; tests may use it to construct explicit new-schema fixtures.
    """

    default_roles = [*_BASE_ROLES]
    if include_fixture_verification:
        default_roles.append("fixture")
    if stock_query is not None:
        default_roles.append("stock_lens")
    requested = set(roles if roles is not None else default_roles)
    allowed = set(_BASE_ROLES) | {"fixture", "stock_lens"}
    if not requested or not requested <= allowed:
        raise VerifiedResearchReportInputError("verified report lineage roles are invalid")
    if "fixture" in requested and not include_fixture_verification:
        raise VerifiedResearchReportInputError("verified report fixture lineage options are invalid")
    if "stock_lens" in requested and stock_query is None:
        raise VerifiedResearchReportInputError("verified report stock lineage options are invalid")

    path = lineage_path(podcast_id, episode_ref)
    existing = _load_existing_sidecar(path, podcast_id, episode_ref)
    artifacts = dict(existing.get("artifacts", {})) if existing is not None else {}
    current = _current_artifacts(
        podcast_id,
        episode_ref,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
        summary_options=summary_options,
        roles=requested,
    )
    if not isinstance(generation_proofs, dict) or set(generation_proofs) != requested:
        raise VerifiedResearchReportInputError("verified report generation proofs are required")
    proofs = generation_proofs
    in_place_fixture_commit = _is_in_place_fixture_commit(
        requested, current, artifacts, proofs
    )
    for role in requested:
        entry = current[role]
        proof = _validated_generation_proof(role, entry, proofs[role])
        if (
            proof["execution"] == "generated"
            and proof["pre_sha256"] is not None
            and not in_place_fixture_commit
        ):
            raise VerifiedResearchReportInputError("verified report generated proof is invalid")
        if role == "transcript":
            if proof["execution"] != "external_selector":
                raise VerifiedResearchReportInputError("verified report transcript generation proof is invalid")
        elif proof["execution"] == "external_selector":
            raise VerifiedResearchReportInputError("verified report derived generation proof is invalid")
        if proof["execution"] == "reused_current_lineage":
            existing_entry = artifacts.get(role)
            if not isinstance(existing_entry, dict):
                raise VerifiedResearchReportInputError("verified report reused lineage proof is invalid")
            existing_proof = existing_entry.get("generation_proof")
            existing_current = _normalized_current_entry(role, existing_entry)
            existing_current.pop("generation_proof", None)
            if (
                existing_current != entry
                or not _generation_proof_matches_current(role, entry, existing_proof)
            ):
                raise VerifiedResearchReportInputError("verified report reused lineage proof is invalid")
        artifacts[role] = {**entry, "generation_proof": proof}
    payload = {
        "schema_version": LINEAGE_SCHEMA_VERSION,
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "artifacts": artifacts,
        "not_investment_advice": True,
    }
    _write_atomic_json(path, payload)
    return path


def validate_current_verified_research_lineage(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool,
    summary_options: dict[str, Any] | None = None,
    roles: Iterable[str] | None = None,
    require_generation_proofs: bool = True,
) -> dict[str, Any]:
    """Validate a complete trusted lineage chain or raise a bounded input error."""

    default_roles = [*_BASE_ROLES]
    if include_fixture_verification:
        default_roles.append("fixture")
    if stock_query is not None:
        default_roles.append("stock_lens")
    requested = set(roles if roles is not None else default_roles)
    required = set(_BASE_ROLES)
    if include_fixture_verification:
        required.add("fixture")
    if stock_query is not None:
        required.add("stock_lens")
    if not requested or not requested <= required:
        raise VerifiedResearchReportInputError("verified report lineage role selection is invalid")
    path = lineage_path(podcast_id, episode_ref)
    payload = _load_existing_sidecar(path, podcast_id, episode_ref)
    if payload is None:
        raise VerifiedResearchReportInputError("verified report lineage is missing or untrusted")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        raise VerifiedResearchReportInputError("verified report lineage is invalid")
    effective_summary_options = summary_options
    if effective_summary_options is None:
        recorded_summary = artifacts.get("semantic_summary")
        effective_summary_options = (
            recorded_summary.get("options") if isinstance(recorded_summary, dict) else None
        )

    try:
        current = _current_artifacts(
            podcast_id,
            episode_ref,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
            summary_options=effective_summary_options,
            roles=requested,
        )
    except CanonicalTranscriptResolutionError as exc:
        raise VerifiedResearchReportInputError("verified report canonical transcript is ambiguous") from exc
    except VerifiedResearchReportInputError:
        raise
    except Exception as exc:  # pragma: no cover - bounded final defensive gate.
        raise VerifiedResearchReportInputError("verified report lineage inspection failed") from exc

    for role in requested:
        recorded = artifacts.get(role)
        if not isinstance(recorded, dict):
            raise VerifiedResearchReportInputError(
                f"verified report {role.replace('_', ' ')} lineage is stale or invalid"
            )
        proof = recorded.get("generation_proof")
        recorded_current = _normalized_current_entry(role, recorded)
        recorded_current.pop("generation_proof", None)
        if recorded_current != current[role] or (
            require_generation_proofs
            and (
                not _generation_proof_matches_current(role, current[role], proof)
                or (
                    isinstance(proof, dict)
                    and proof.get("execution") == "generated"
                    and proof.get("pre_sha256") is not None
                    and not _is_recorded_in_place_fixture_proof(role, artifacts)
                )
            )
        ):
            raise VerifiedResearchReportInputError(
                f"verified report {role.replace('_', ' ')} lineage is stale or invalid"
            )
    # Publisher compatibility intentionally exposes the persisted v2 shape.
    # It remains comparison-only; fresh artifact records are available only via
    # the private evidence seam below and are the sole later I/O authority.
    return {
        "schema_version": LINEAGE_SCHEMA_VERSION,
        "quality_gate": LINEAGE_QUALITY_GATE,
        "sidecar_path": _canonical_path(path),
        "artifacts": {role: artifacts[role] for role in sorted(requested)},
    }


def _current_verified_research_lineage_evidence(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool,
    summary_options: dict[str, Any] | None = None,
    roles: Iterable[str] | None = None,
    require_generation_proofs: bool = True,
) -> _CurrentVerifiedResearchLineageEvidence:
    """Return old publisher manifest plus fresh Core-derived current records.

    Persisted entries validate compatibility and equality only.  Their paths are
    never returned as a read selector: the second calculation re-derives every
    expected source path from the locator and fixed Core storage roots.
    """

    publisher_manifest = validate_current_verified_research_lineage(
        podcast_id,
        episode_ref,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
        summary_options=summary_options,
        roles=roles,
        require_generation_proofs=require_generation_proofs,
    )
    artifacts = publisher_manifest["artifacts"]
    requested = set(artifacts)
    effective_summary_options = summary_options
    if effective_summary_options is None:
        recorded_summary = artifacts.get("semantic_summary")
        effective_summary_options = (
            recorded_summary.get("options") if isinstance(recorded_summary, dict) else None
        )
    try:
        current = _current_artifacts(
            podcast_id,
            episode_ref,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
            summary_options=effective_summary_options,
            roles=requested,
        )
    except CanonicalTranscriptResolutionError as exc:
        raise VerifiedResearchReportInputError("verified report canonical transcript is ambiguous") from exc
    except VerifiedResearchReportInputError:
        raise
    except Exception as exc:  # pragma: no cover - bounded final defensive gate.
        raise VerifiedResearchReportInputError("verified report lineage inspection failed") from exc
    return _CurrentVerifiedResearchLineageEvidence(publisher_manifest, current)


def _current_artifacts(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool,
    summary_options: dict[str, Any] | None,
    roles: Iterable[str],
) -> dict[str, dict[str, Any]]:
    """Build only requested entries and their direct-upstream closure.

    Progressive records let a newly generated summary/review survive a later
    deterministic-stage failure without blessing any pre-existing downstream
    artifact.  Each entry still embeds the immediate upstream path and digest.
    """

    required = set(roles)
    if "fixture" in required:
        required.add("external_boundary")
    if "stock_lens" in required:
        required.add("external_boundary")
    if "external_boundary" in required:
        required.add("industry_mapping")
    if "industry_mapping" in required:
        required.add("intelligence")
    if "intelligence" in required:
        required.add("mentions")
    if "semantic_review" in required:
        required.add("semantic_summary")
    if required & {"semantic_summary", "mentions"}:
        required.add("transcript")

    current: dict[str, dict[str, Any]] = {}
    title: str | None = None
    transcript_entry: dict[str, Any] | None = None
    if "transcript" in required:
        transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
        if transcript_paths is None:
            raise VerifiedResearchReportInputError("verified report canonical transcript is missing")
        transcript_raw = _read_bytes(transcript_paths.json_path, "transcript")
        transcript = _read_json(transcript_raw, "transcript")
        title = _identity_title(transcript, podcast_id, episode_ref, "transcript")
        transcript_entry = _entry(
            transcript_paths.json_path,
            transcript_raw,
            options={"root": "canonical_transcript"},
        )
        current["transcript"] = transcript_entry

    if "semantic_summary" in required:
        assert title is not None and transcript_entry is not None
        summary_path = storage.semantic_summary_asset_path(podcast_id, episode_ref, title)
        summary_raw = _read_bytes(summary_path, "semantic summary")
        summary_entry = _entry(
            summary_path,
            summary_raw,
            upstream={"transcript": _reference(transcript_entry)},
            options={
                **_summary_options(summary_options),
                **_semantic_summary_actual_dependency_identity(summary_raw),
            },
        )
        current["semantic_summary"] = summary_entry

    if "semantic_review" in required:
        summary_entry = current["semantic_summary"]
        assert title is not None
        # Re-derive the expected source location; never re-open a metadata path.
        summary_path = storage.semantic_summary_asset_path(podcast_id, episode_ref, title)
        summary_raw = _read_bytes(summary_path, "semantic summary")
        review = inspect_semantic_review(
            podcast_id,
            episode_ref,
            semantic_summary_path=summary_path,
            review_reports_dir=_semantic_review_reports_dir(),
            semantic_summary_bytes=summary_raw,
        )
        if review.review_status != "passed" or review.review_path is None or review.review_bytes is None:
            raise VerifiedResearchReportInputError("verified report semantic review lineage is unavailable")
        review_payload = _read_json(review.review_bytes, "semantic review")
        if review_payload.get("review_mode") != REVIEW_MODE or review_payload.get("review_boundary") != REVIEW_BOUNDARY:
            raise VerifiedResearchReportInputError("verified report semantic review lineage mode is invalid")
        current["semantic_review"] = _entry(
            review.review_path,
            review.review_bytes,
            upstream={"semantic_summary": _reference(summary_entry)},
            options={"review_mode": REVIEW_MODE, "review_boundary": REVIEW_BOUNDARY},
        )

    if "mentions" in required:
        assert title is not None and transcript_entry is not None
        mentions_path = storage.mention_asset_paths(podcast_id, episode_ref, title).json_path
        mentions_raw = _read_bytes(mentions_path, "mentions")
        mentions = _read_json(mentions_raw, "mentions")
        _identity_title(mentions, podcast_id, episode_ref, "mentions")
        current["mentions"] = _entry(
            mentions_path,
            mentions_raw,
            upstream={"transcript": _reference(transcript_entry)},
            options={
                "extraction_mode": _required_mode(mentions, "extraction_mode", "mentions"),
                "max_evidence_per_mention": _artifact_positive_option(
                    mentions, "max_evidence_per_mention", 5
                ),
            },
        )

    if "intelligence" in required:
        assert title is not None and transcript_entry is not None
        mentions_entry = current["mentions"]
        intelligence_path = storage.episode_intelligence_report_asset_paths(
            podcast_id, episode_ref, title
        ).json_path
        intelligence_raw = _read_bytes(intelligence_path, "intelligence")
        intelligence = _read_json(intelligence_raw, "intelligence")
        _identity_title(intelligence, podcast_id, episode_ref, "intelligence")
        current["intelligence"] = _entry(
            intelligence_path,
            intelligence_raw,
            upstream={
                "transcript": _reference(transcript_entry),
                "mentions": _reference(mentions_entry),
            },
            options={
                "report_mode": _required_mode(intelligence, "report_mode", "intelligence"),
                "window_seconds": _artifact_positive_option(intelligence, "window_seconds", 300),
                "max_evidence_per_section": _artifact_positive_option(
                    intelligence, "max_evidence_per_section", 5
                ),
            },
        )

    if "industry_mapping" in required:
        assert title is not None
        intelligence_entry = current["intelligence"]
        mapping_path = storage.industry_chain_mapping_asset_paths(
            podcast_id, episode_ref, title
        ).json_path
        mapping_raw = _read_bytes(mapping_path, "industry mapping")
        mapping = _read_json(mapping_raw, "industry mapping")
        _identity_title(mapping, podcast_id, episode_ref, "industry mapping")
        current["industry_mapping"] = _entry(
            mapping_path,
            mapping_raw,
            upstream={"intelligence": _reference(intelligence_entry)},
            options={
                "mapping_mode": _required_mode(mapping, "mapping_mode", "industry mapping"),
                "max_candidates_per_node": _artifact_positive_option(
                    mapping, "max_candidates_per_node", 5
                ),
                "max_evidence_per_candidate": _artifact_positive_option(
                    mapping, "max_evidence_per_candidate", 5
                ),
                "mapping_config": _config_identity(_mapping_config_path()),
            },
        )

    if "external_boundary" in required:
        assert title is not None
        mapping_entry = current["industry_mapping"]
        boundary_path = storage.external_data_boundary_asset_paths(
            podcast_id, episode_ref, title
        ).json_path
        boundary_raw = _read_bytes(boundary_path, "external boundary")
        boundary = _read_json(boundary_raw, "external boundary")
        _identity_title(boundary, podcast_id, episode_ref, "external boundary")
        current["external_boundary"] = _entry(
            boundary_path,
            boundary_raw,
            upstream={"industry_mapping": _reference(mapping_entry)},
            options={
                "boundary_mode": _required_mode(boundary, "boundary_mode", "external boundary"),
                "boundary_config": _config_identity(_boundary_config_path()),
            },
        )

    if "fixture" in required:
        current["fixture"] = _fixture_entry(
            current["external_boundary"], boundary, boundary_raw=boundary_raw
        )

    if "stock_lens" in required:
        if stock_query is None:
            raise VerifiedResearchReportInputError("verified report stock lineage options are invalid")
        stock_path = storage.stock_lens_report_asset_paths(podcast_id, stock_query).json_path
        stock_raw = _read_bytes(stock_path, "stock lens")
        stock = _read_json(stock_raw, "stock lens")
        if stock.get("podcast_id") != podcast_id or stock.get("stock_query") != stock_query:
            raise VerifiedResearchReportInputError("verified report stock lens lineage identity is invalid")
        current["stock_lens"] = _entry(
            stock_path,
            stock_raw,
            upstream={
                "corpus_input_set": _stock_lens_input_set(
                    stock,
                    expected_inputs={
                        "industry_mapping": current["industry_mapping"]["path"],
                        "external_boundary": current["external_boundary"]["path"],
                    },
                )
            },
            options={
                "report_mode": _required_mode(stock, "report_mode", "stock lens"),
                "max_evidence_items": _artifact_positive_option(
                    stock, "max_evidence_items", 10
                ),
                "lens_config": _config_identity(_lens_config_path()),
            },
        )
    return current


def _fixture_entry(
    boundary_entry: dict[str, Any], boundary: dict[str, Any], *, boundary_raw: bytes | None = None
) -> dict[str, Any]:
    marker = boundary.get("external_data_verification")
    if not isinstance(marker, dict) or marker.get("verification_mode") != VERIFICATION_MODE:
        raise VerifiedResearchReportInputError("verified report fixture verification marker is missing")
    fixture_path = marker.get("fixture_path")
    fixture_sha = marker.get("fixture_sha256")
    boundary_input_path = marker.get("boundary_input_path")
    boundary_input_sha = marker.get("boundary_input_sha256")
    snapshot_path = marker.get("preverification_snapshot_path")
    snapshot_sha = marker.get("preverification_snapshot_sha256")
    if not all(
        isinstance(value, str) and value
        for value in (
            fixture_path,
            fixture_sha,
            boundary_input_path,
            boundary_input_sha,
            snapshot_path,
            snapshot_sha,
        )
    ) or not _is_sha256(boundary_input_sha):
        raise VerifiedResearchReportInputError("verified report fixture verification marker is invalid")
    # Marker paths are hostile metadata.  Establish Core-derived canonical paths
    # before any fixture/snapshot read, then compare the marker strings only.
    expected_fixture = _default_fixture_path()
    if fixture_path != _canonical_path(expected_fixture):
        raise VerifiedResearchReportInputError("verified report fixture lineage is stale")
    expected_boundary_path = boundary_entry.get("path")
    if not isinstance(expected_boundary_path, str) or boundary_input_path != expected_boundary_path:
        raise VerifiedResearchReportInputError("verified report fixture lineage is stale")
    snapshot_episode_slug = storage.title_slug(str(boundary["episode_ref"]), "episode")
    expected_snapshot = (
        storage.CORPUS_DIR
        / str(boundary["podcast_id"])
        / "verified-research"
        / "preverification-boundaries"
        / f"{snapshot_episode_slug}-{boundary_input_sha}.json"
    )
    if snapshot_path != _canonical_path(expected_snapshot):
        raise VerifiedResearchReportInputError("verified report preverification boundary snapshot is stale")
    fixture_raw = _read_bytes(expected_fixture, "fixture")
    if _sha256(fixture_raw) != fixture_sha:
        raise VerifiedResearchReportInputError("verified report fixture lineage is stale")
    snapshot_raw = _read_bytes(expected_snapshot, "preverification external boundary")
    if snapshot_sha != boundary_input_sha or _sha256(snapshot_raw) != boundary_input_sha:
        raise VerifiedResearchReportInputError("verified report preverification boundary snapshot is stale")
    snapshot_boundary = _read_json(snapshot_raw, "preverification external boundary")
    if (
        snapshot_boundary.get("podcast_id") != boundary.get("podcast_id")
        or snapshot_boundary.get("episode_ref") != boundary.get("episode_ref")
        or snapshot_boundary.get("title") != boundary.get("title")
    ):
        raise VerifiedResearchReportInputError("verified report preverification boundary snapshot is invalid")
    # ``boundary_entry`` was built from the current, securely captured boundary
    # bytes in this invocation.  Do not convert its metadata path back into an
    # I/O authority merely to construct the fixture's provenance record.
    if boundary_raw is None:
        raise VerifiedResearchReportInputError("verified report external boundary lineage is unreadable")
    return {
        "path": expected_boundary_path,
        "sha256": _sha256(boundary_raw),
        "upstream": {
            "external_boundary_input": {
                "path": expected_boundary_path,
                "sha256": boundary_input_sha,
            },
            "preverification_boundary_snapshot": {
                "path": _canonical_path(expected_snapshot),
                "sha256": boundary_input_sha,
            },
        },
        "options": {
            "verification_mode": VERIFICATION_MODE,
            "fixture_path": _canonical_path(expected_fixture),
            "fixture_sha256": fixture_sha,
        },
    }


def _stock_lens_input_set(
    stock: dict[str, Any], *, expected_inputs: dict[str, str]
) -> list[dict[str, str]]:
    """Compare hostile stock metadata against Core-derived inputs before reads."""

    expected_roles = {"industry_mapping", "external_boundary"}
    if set(expected_inputs) != expected_roles or not all(
        isinstance(path, str) and path for path in expected_inputs.values()
    ):
        raise VerifiedResearchReportInputError("verified report stock lens input set is invalid")
    raw_inputs = stock.get("input_set_lineage")
    if not isinstance(raw_inputs, list) or len(raw_inputs) != len(expected_roles):
        raise VerifiedResearchReportInputError("verified report stock lens input set is missing")
    inputs: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_inputs:
        if (
            not isinstance(item, dict)
            or set(item) != {"role", "path", "sha256"}
            or item.get("role") not in expected_roles
            or not isinstance(item.get("path"), str)
            or not _is_sha256(item.get("sha256"))
        ):
            raise VerifiedResearchReportInputError("verified report stock lens input set is invalid")
        role = item["role"]
        if role in seen or item["path"] != expected_inputs[role]:
            raise VerifiedResearchReportInputError("verified report stock lens input set is invalid")
        seen.add(role)
        # Read only after the recorded string exactly matches Core's canonical path.
        raw = _read_bytes(Path(expected_inputs[role]), role)
        if _sha256(raw) != item["sha256"]:
            raise VerifiedResearchReportInputError("verified report stock lens input set is stale")
        inputs.append({"role": role, "path": expected_inputs[role], "sha256": item["sha256"]})
    if seen != expected_roles:
        raise VerifiedResearchReportInputError("verified report stock lens input set is invalid")
    return sorted(inputs, key=lambda item: (item["role"], item["path"]))


def _is_in_place_fixture_commit(
    requested: set[str],
    current: dict[str, dict[str, Any]],
    existing: dict[str, Any],
    proofs: dict[str, dict[str, Any]],
) -> bool:
    """Permit only verifier-owned boundary replacement backed by its old snapshot."""

    if requested != {"external_boundary", "fixture"}:
        return False
    boundary = current.get("external_boundary")
    fixture = current.get("fixture")
    old_boundary = existing.get("external_boundary")
    boundary_proof = proofs.get("external_boundary")
    fixture_proof = proofs.get("fixture")
    if not all(
        isinstance(value, dict)
        for value in (boundary, fixture, old_boundary, boundary_proof, fixture_proof)
    ):
        return False
    try:
        checked_boundary = _validated_generation_proof("external_boundary", boundary, boundary_proof)
        checked_fixture = _validated_generation_proof("fixture", fixture, fixture_proof)
    except VerifiedResearchReportInputError:
        return False
    old_proof = old_boundary.get("generation_proof")
    old_entry = dict(old_boundary)
    old_entry.pop("generation_proof", None)
    fixture_input = fixture.get("upstream", {}).get("external_boundary_input")
    snapshot = fixture.get("upstream", {}).get("preverification_boundary_snapshot")
    return (
        checked_boundary["execution"] == checked_fixture["execution"] == "generated"
        and isinstance(checked_boundary["pre_sha256"], str)
        and checked_boundary["pre_sha256"] == checked_fixture["pre_sha256"]
        and checked_boundary["post_sha256"] == checked_fixture["post_sha256"]
        and checked_boundary["expected_path"] == checked_fixture["expected_path"]
        and old_entry.get("sha256") == checked_boundary["pre_sha256"]
        and _generation_proof_matches_current("external_boundary", old_entry, old_proof)
        and isinstance(fixture_input, dict)
        and fixture_input.get("sha256") == checked_boundary["pre_sha256"]
        and isinstance(snapshot, dict)
        and snapshot.get("sha256") == checked_boundary["pre_sha256"]
    )


def _is_recorded_in_place_fixture_proof(role: str, artifacts: dict[str, Any]) -> bool:
    """Validate the persisted paired proof and fixture snapshot after a resume."""

    if role not in {"external_boundary", "fixture"}:
        return False
    boundary = artifacts.get("external_boundary")
    fixture = artifacts.get("fixture")
    if not isinstance(boundary, dict) or not isinstance(fixture, dict):
        return False
    try:
        boundary_entry = dict(boundary)
        boundary_proof = boundary_entry.pop("generation_proof")
        fixture_entry = dict(fixture)
        fixture_proof = fixture_entry.pop("generation_proof")
        checked_boundary = _validated_generation_proof(
            "external_boundary", boundary_entry, boundary_proof
        )
        checked_fixture = _validated_generation_proof("fixture", fixture_entry, fixture_proof)
    except (KeyError, VerifiedResearchReportInputError):
        return False
    fixture_input = fixture_entry.get("upstream", {}).get("external_boundary_input")
    snapshot = fixture_entry.get("upstream", {}).get("preverification_boundary_snapshot")
    return (
        checked_boundary["execution"] == checked_fixture["execution"] == "generated"
        and isinstance(checked_boundary["pre_sha256"], str)
        and checked_boundary["pre_sha256"] == checked_fixture["pre_sha256"]
        and checked_boundary["post_sha256"] == checked_fixture["post_sha256"]
        and checked_boundary["expected_path"] == checked_fixture["expected_path"]
        and isinstance(fixture_input, dict)
        and fixture_input.get("sha256") == checked_boundary["pre_sha256"]
        and isinstance(snapshot, dict)
        and snapshot.get("sha256") == checked_boundary["pre_sha256"]
    )


def _validated_generation_proof(
    role: str, entry: dict[str, Any], proof: dict[str, Any],
) -> dict[str, Any]:
    """Accept only a role-bound controlled-write proof for this exact output."""

    if not isinstance(proof, dict) or set(proof) != {
        "expected_path", "pre_sha256", "post_sha256", "execution"
    }:
        raise VerifiedResearchReportInputError("verified report generation proof is invalid")
    expected_path = proof.get("expected_path")
    pre_sha256 = proof.get("pre_sha256")
    post_sha256 = proof.get("post_sha256")
    execution = proof.get("execution")
    if (
        not isinstance(expected_path, str)
        or expected_path != entry["path"]
        or pre_sha256 is not None and not _is_sha256(pre_sha256)
        or not isinstance(post_sha256, str)
        or post_sha256 != entry["sha256"]
        or not isinstance(execution, str)
        or execution not in {
            "generated", "external_selector", "reused_current_lineage", "regenerated"
        }
        or (
            execution == "regenerated"
            and (
                role != "semantic_summary"
                or not isinstance(pre_sha256, str)
                or pre_sha256 == post_sha256
            )
        )
    ):
        raise VerifiedResearchReportInputError("verified report generation proof is invalid")
    return {
        "expected_path": expected_path,
        "pre_sha256": pre_sha256,
        "post_sha256": post_sha256,
        "execution": execution,
    }


def _generation_proof_matches_current(
    role: str, entry: dict[str, Any], proof: object
) -> bool:
    try:
        _validated_generation_proof(role, entry, proof)  # type: ignore[arg-type]
    except VerifiedResearchReportInputError:
        return False
    return True


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _entry(
    path: Path,
    raw: bytes,
    *,
    upstream: dict[str, Any] | None = None,
    options: dict[str, Any],
) -> dict[str, Any]:
    return {
        "path": _canonical_path(path),
        "sha256": _sha256(raw),
        "upstream": upstream or {},
        "options": options,
    }


def _reference(entry: dict[str, Any]) -> dict[str, str]:
    return {"path": entry["path"], "sha256": entry["sha256"]}


def _summary_options(value: dict[str, Any] | None) -> dict[str, Any]:
    """Validate and normalize semantic request identity without endpoint secrets.

    Sidecars recorded before controlled regeneration omitted the two Luna request
    controls.  They are read as the original defaults, rather than rewritten.
    """

    if not isinstance(value, dict):
        raise VerifiedResearchReportInputError("verified report semantic summary lineage options are missing")
    legacy_requested_keys = {
        "summary_mode",
        "requested_provider",
        "requested_model",
        "requested_base_url_identity_sha256",
        "requested_chunk_seconds",
        "requested_max_segments_per_chunk",
    }
    new_requested_keys = {
        "requested_reasoning_effort", "requested_read_timeout_seconds"
    }
    requested_keys = legacy_requested_keys | new_requested_keys
    actual_keys = {"actual_provider", "actual_model"}
    actual_present = actual_keys & set(value)
    supplied_requested = set(value) - actual_present
    if (
        actual_present not in (set(), actual_keys)
        or (
            supplied_requested != legacy_requested_keys
            and supplied_requested != requested_keys
        )
    ):
        raise VerifiedResearchReportInputError("verified report semantic summary lineage options are invalid")
    normalized = {
        **value,
        "requested_reasoning_effort": value.get("requested_reasoning_effort", None),
        "requested_read_timeout_seconds": value.get("requested_read_timeout_seconds", 120),
    }
    if (
        normalized.get("summary_mode") != "semantic-llm"
        or not isinstance(normalized.get("requested_provider"), str)
        or not normalized["requested_provider"]
        or (
            normalized.get("requested_model") is not None
            and not isinstance(normalized.get("requested_model"), str)
        )
        or (
            normalized.get("requested_base_url_identity_sha256") is not None
            and not _is_sha256(normalized.get("requested_base_url_identity_sha256"))
        )
        or (
            normalized.get("requested_reasoning_effort") is not None
            and (
                not isinstance(normalized.get("requested_reasoning_effort"), str)
                or not normalized["requested_reasoning_effort"]
            )
        )
        or not isinstance(normalized.get("requested_read_timeout_seconds"), int)
        or isinstance(normalized.get("requested_read_timeout_seconds"), bool)
        or not 1 <= normalized["requested_read_timeout_seconds"] <= 3_600
        or not isinstance(normalized.get("requested_chunk_seconds"), int)
        or not isinstance(normalized.get("requested_max_segments_per_chunk"), int)
        or normalized["requested_chunk_seconds"] < 1
        or normalized["requested_max_segments_per_chunk"] < 1
        or (
            "actual_provider" in normalized
            and (not isinstance(normalized["actual_provider"], str) or not normalized["actual_provider"])
        )
        or (
            "actual_model" in normalized
            and normalized["actual_model"] is not None
            and not isinstance(normalized["actual_model"], str)
        )
    ):
        raise VerifiedResearchReportInputError("verified report semantic summary lineage options are invalid")
    return {key: normalized[key] for key in requested_keys}


def _normalized_current_entry(role: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize only legacy semantic options before immutable entry comparison."""

    normalized = dict(entry)
    if role == "semantic_summary" and isinstance(normalized.get("options"), dict):
        raw_options = normalized["options"]
        requested = _summary_options(raw_options)
        normalized["options"] = {
            **requested,
            **{
                key: raw_options[key]
                for key in ("actual_provider", "actual_model")
                if key in raw_options
            },
        }
    return normalized


def _semantic_summary_actual_dependency_identity(raw: bytes) -> dict[str, str | None]:
    """Read committed provider/model separately from the caller's request identity."""

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerifiedResearchReportInputError(
            "verified report semantic summary metadata is invalid"
        ) from exc
    values: dict[str, str | None] = {}
    for key, label in (("actual_provider", "Provider"), ("actual_model", "Model")):
        match = re.search(rf"(?m)^-?\s*{label}:\s*(.*)$", text)
        if match is None:
            raise VerifiedResearchReportInputError(
                "verified report semantic summary metadata is invalid"
            )
        value = match.group(1).strip()
        values[key] = value or None
    if values["actual_provider"] is None:
        raise VerifiedResearchReportInputError(
            "verified report semantic summary metadata is invalid"
        )
    return values


def _artifact_positive_option(payload: dict[str, Any], key: str, default: int) -> int:
    options = payload.get("generation_options")
    value = options.get(key) if isinstance(options, dict) else default
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise VerifiedResearchReportInputError("verified report generation options are invalid")
    return value


def _config_identity(path: Path) -> dict[str, str | None]:
    # Config locations are imported Core constants.  Their parent is therefore
    # the narrow allowed root; a missing safety proof is represented as absent
    # identity rather than following a link or reopening an untrusted location.
    raw = secure_read_bytes(path.parent, path, max_bytes=_MAX_LINEAGE_INPUT_BYTES)
    return {
        "path": _canonical_path(path),
        "sha256": _sha256(raw) if raw is not None else None,
    }


def _mapping_config_path() -> Path:
    from .industry_mapping import DEFAULT_MAPPING_CONFIG_PATH

    return Path(DEFAULT_MAPPING_CONFIG_PATH)


def _boundary_config_path() -> Path:
    from .external_data_boundary import DEFAULT_BOUNDARY_CONFIG_PATH

    return Path(DEFAULT_BOUNDARY_CONFIG_PATH)


def _lens_config_path() -> Path:
    from .gooaye_lens import DEFAULT_GOOAYE_LENS_CONFIG_PATH

    return Path(DEFAULT_GOOAYE_LENS_CONFIG_PATH)


def _required_mode(payload: dict[str, Any], key: str, role: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise VerifiedResearchReportInputError(f"verified report {role} lineage mode is invalid")
    return value


def _identity_title(payload: dict[str, Any], podcast_id: str, episode_ref: str, role: str) -> str:
    title = payload.get("title")
    if (
        payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or not isinstance(title, str)
        or not title.strip()
    ):
        raise VerifiedResearchReportInputError(f"verified report {role} lineage identity is invalid")
    return title


def _read_json(raw: bytes, role: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifiedResearchReportInputError(f"verified report {role} lineage is unreadable") from exc
    if not isinstance(payload, dict):
        raise VerifiedResearchReportInputError(f"verified report {role} lineage is invalid")
    return payload


def _read_bytes(path: Path, role: str) -> bytes:
    """Read only a current Core-derived artifact through the snapshot boundary."""

    root = _lineage_allowed_root(path)
    raw = secure_read_bytes(root, path, max_bytes=_MAX_LINEAGE_INPUT_BYTES)
    if raw is None:
        raise VerifiedResearchReportInputError(f"verified report {role} lineage is unreadable")
    return raw


def _lineage_allowed_root(path: Path) -> Path:
    """Choose a fixed Core storage root, never a root inferred from metadata."""

    roots = (
        storage.TRANSCRIPTS_DIR,
        storage.SUMMARIES_DIR,
        storage.MENTIONS_DIR,
        storage.REPORTS_DIR,
        storage.MAPPINGS_DIR,
        storage.EXTERNAL_DIR,
        storage.STOCK_LENS_DIR,
        storage.CORPUS_DIR,
        _semantic_review_reports_dir(),
        _default_fixture_path().parent,
    )
    candidate = Path(path).absolute()
    for root in roots:
        checked_root = Path(root).absolute()
        try:
            candidate.relative_to(checked_root)
        except ValueError:
            continue
        return checked_root
    # Keep the final check deliberately disjoint from any unknown candidate.
    return Path(storage.CORPUS_DIR)


def _load_existing_sidecar(path: Path, podcast_id: str, episode_ref: str) -> dict[str, Any] | None:
    raw = secure_read_bytes(storage.CORPUS_DIR, path, max_bytes=_MAX_LINEAGE_INPUT_BYTES)
    if raw is None:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != LINEAGE_SCHEMA_VERSION
        or payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or payload.get("not_investment_advice") is not True
        or not isinstance(payload.get("artifacts"), dict)
    ):
        return None
    return payload


def _write_atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(f"{path.name}.{uuid.uuid4().hex}.part")
    try:
        part.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        part.replace(path)
    except OSError as exc:
        raise VerifiedResearchReportInputError("verified report lineage write failed") from exc
    finally:
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass


def _semantic_review_reports_dir() -> Path:
    from .semantic_summary_smoke_review import REPORTS_DIR

    return REPORTS_DIR


def _default_fixture_path() -> Path:
    # Resolve dynamically so test sandboxes and a future explicitly configured
    # local fixture use the exact file the verification marker names.
    from .external_data_verification import DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH

    return Path(DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH)


def _canonical_path(path: Path) -> str:
    return path.resolve(strict=False).as_posix()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
