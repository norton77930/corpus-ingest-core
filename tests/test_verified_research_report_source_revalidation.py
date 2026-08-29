"""Focused Core contracts for SPEC 021 source revalidation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


_DIGEST = "a" * 64


@pytest.mark.parametrize("field", ["podcast_id", "episode_ref"])
def test_oversized_locator_is_rejected_before_exact_bundle_evidence(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    monkeypatch.setattr(
        revalidation, "_exact_bundle_evidence", lambda locator: pytest.fail("oversized locator read storage")
    )
    locator = {"podcast_id": "show", "episode_ref": "EP1", "source_digest": _DIGEST}
    locator[field] = "a" * 129

    with pytest.raises(revalidation.VerifiedResearchReportSourceRevalidationInputError):
        revalidation.revalidate_verified_research_report_sources(**locator)


def test_missing_bundle_stops_before_any_current_source_or_lineage_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing exact bundle is not evidence that permits external reads."""
    from corpus_ingest_core import storage
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation
    from corpus_ingest_core import revalidate_verified_research_report_sources

    monkeypatch.setattr(storage, "RESEARCH_REPORTS_DIR", tmp_path / "research-reports")
    monkeypatch.setattr(
        revalidation,
        "_current_verified_research_source_snapshot",
        lambda *args, **kwargs: pytest.fail("missing bundle read current sources"),
    )

    result = revalidate_verified_research_report_sources("show", "EP1", _DIGEST)

    assert result.bundle_self_consistency_status == "not_found"
    assert result.lineage_revalidation_status == "not_evaluated"
    assert result.source_currentness_status == "not_evaluated"
    assert result.checks == {
        "bundle_self_consistency": "not_found",
        "assembly_options": "not_evaluated",
        "current_lineage": "not_evaluated",
        "published_lineage_match": "not_evaluated",
        "source_artifact_metadata_match": "not_evaluated",
        "source_digest_match": "not_evaluated",
    }
    assert result.failed_roles == []
    assert result.safe_metadata is None
    assert result.not_investment_advice is None


def _valid_evidence_and_snapshot(
    tmp_path: Path,
    *,
    roles: tuple[str, ...] = ("transcript",),
    stock_query: str | None = None,
    legacy_safe_paths: bool = False,
    safe_metadata: object | None = None,
):
    from types import SimpleNamespace

    from corpus_ingest_core.verified_research_report import _safe_path, _source_digest

    sources = []
    for index, role in enumerate(roles):
        path = Path(f"legacy-{role}.json") if legacy_safe_paths else tmp_path / f"canonical-{role}.json"
        sources.append(
            SimpleNamespace(
                role=role,
                path=path,
                sha256=("bcdef"[index] * 64),
                size_bytes=index + 7,
                identity_valid=True,
                raw_bytes=b"fixture",
            )
        )
    lineage = {"schema_version": "lineage-v2", "artifacts": {role: {} for role in roles}}
    digest = _source_digest(
        podcast_id="show",
        episode_ref="EP1",
        stock_query=stock_query,
        include_fixture_verification=False,
        sources=sources,
    )
    manifest = {
        "assembly_options": {
            "stock_query": stock_query,
            "include_fixture_verification": False,
            "verification_scope": "local_artifact_and_fixture",
        },
        "lineage": lineage,
        "source_artifacts": [
            {
                "role": source.role,
                "path": _safe_path(source.path) if legacy_safe_paths else source.path.resolve().as_posix(),
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
                "identity_valid": True,
            }
            for source in sources
        ],
    }
    evidence = SimpleNamespace(status="valid", manifest=manifest, safe_metadata=safe_metadata)
    snapshot = SimpleNamespace(lineage_manifest=lineage, source_artifacts=sources)
    return digest, evidence, snapshot


def test_valid_bundle_requires_matching_current_lineage_sources_and_shared_digest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, snapshot = _valid_evidence_and_snapshot(tmp_path)
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.bundle_self_consistency_status == "valid"
    assert result.lineage_revalidation_status == "current"
    assert result.source_currentness_status == "current"
    assert set(result.checks) == {
        "bundle_self_consistency", "assembly_options", "current_lineage",
        "published_lineage_match", "source_artifact_metadata_match", "source_digest_match",
    }
    assert all(value in {"valid", "current", "match"} for value in result.checks.values())
    assert result.failed_roles == []


def test_published_hostile_source_path_is_comparison_only_not_a_read_authority(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, snapshot = _valid_evidence_and_snapshot(tmp_path)
    hostile = "HOSTILE-MANIFEST-PATH-SENTINEL"
    evidence.manifest["source_artifacts"][0]["path"] = hostile
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if hostile in str(path):
            raise AssertionError("manifest path was dereferenced")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.source_currentness_status == "stale_or_invalid"
    assert result.checks["source_artifact_metadata_match"] == "mismatch"
    assert result.failed_roles == ["transcript"]
    assert hostile not in repr(result)


def test_stock_lens_input_set_requires_core_derived_paths_before_any_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Stock artifact metadata must not turn a hostile path into read authority."""
    import hashlib

    from corpus_ingest_core import VerifiedResearchReportInputError
    import corpus_ingest_core.verified_research_lineage as lineage

    expected_mapping = tmp_path / "canonical-mapping.json"
    expected_boundary = tmp_path / "canonical-boundary.json"
    expected_mapping.write_bytes(b"mapping")
    expected_boundary.write_bytes(b"boundary")
    hostile = tmp_path / "HOSTILE-STOCK-INPUT-SENTINEL.json"
    hostile.write_bytes(b"hostile")
    stock = {
        "input_set_lineage": [
            {"role": "industry_mapping", "path": hostile.resolve().as_posix(), "sha256": hashlib.sha256(b"hostile").hexdigest()},
            {"role": "external_boundary", "path": expected_boundary.resolve().as_posix(), "sha256": hashlib.sha256(b"boundary").hexdigest()},
        ]
    }
    expected_inputs = {
        "industry_mapping": expected_mapping.resolve().as_posix(),
        "external_boundary": expected_boundary.resolve().as_posix(),
    }
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path == hostile:
            raise AssertionError("hostile stock input path was read")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(
        lineage, "secure_read_bytes", lambda *args, **kwargs: pytest.fail("hostile stock input triggered secure read")
    )

    with pytest.raises(VerifiedResearchReportInputError):
        lineage._stock_lens_input_set(stock, expected_inputs=expected_inputs)


def test_safe_serializer_omits_tainted_values_and_keeps_only_bounded_contract() -> None:
    from corpus_ingest_core.models import VerifiedResearchReportSourceRevalidation
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    result = VerifiedResearchReportSourceRevalidation(
        locator={"podcast_id": "show", "episode_ref": "EP1", "source_digest": _DIGEST},
        bundle_self_consistency_status="traceback HOSTILE-ABSOLUTE-PATH",
        lineage_revalidation_status="unbounded",
        source_currentness_status="unbounded",
        checks={"stock_query": "SECRET-STOCK", "bundle_self_consistency": "unbounded"},
        failed_roles=["transcript", "../HOSTILE-PATH", "exception message"],
        safe_metadata=None,
        not_investment_advice=False,
    )

    serialized = revalidation.result_to_dict(result)

    assert set(serialized) == {
        "locator", "bundle_self_consistency_status", "lineage_revalidation_status",
        "source_currentness_status", "checks", "failed_roles", "safe_metadata",
        "not_investment_advice",
    }
    assert serialized["failed_roles"] == ["transcript"]
    assert set(serialized["checks"]) == {
        "bundle_self_consistency", "assembly_options", "current_lineage",
        "published_lineage_match", "source_artifact_metadata_match", "source_digest_match",
    }
    assert "HOSTILE" not in repr(serialized)
    assert "SECRET-STOCK" not in repr(serialized)


def test_publisher_manifest_preserves_legacy_safe_source_path_representation() -> None:
    from types import SimpleNamespace

    from corpus_ingest_core.verified_research_report import (
        _manifest_payload_from_metadata,
        _safe_path,
    )

    relative_path = Path("relative-source-artifact.json")
    source = SimpleNamespace(
        role="semantic_summary", path=relative_path, sha256="c" * 64,
        size_bytes=1, identity_valid=True,
    )
    assembly = SimpleNamespace(
        report_version="v1-" + "d" * 64,
        source_digest="d" * 64,
        podcast_id="show",
        episode_ref="EP1",
        stock_query=None,
        include_fixture_verification=False,
        source_artifacts=[source],
        lineage_manifest={},
    )

    manifest = _manifest_payload_from_metadata(
        assembly,
        report_json_metadata={"sha256": "e" * 64, "size_bytes": 1},
        report_markdown_metadata={"sha256": "f" * 64, "size_bytes": 1},
    )

    assert manifest["source_artifacts"][0]["path"] == _safe_path(relative_path)


def test_current_source_snapshot_uses_fresh_evidence_not_persisted_lineage_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from types import SimpleNamespace
    import corpus_ingest_core.verified_research_report as report

    roles = (
        "transcript", "semantic_summary", "semantic_review", "mentions",
        "intelligence", "industry_mapping", "external_boundary",
    )
    current_paths = {role: tmp_path / f"current-{role}.json" for role in roles}
    evidence = SimpleNamespace(
        publisher_manifest={
            "sidecar_path": "HOSTILE-PERSISTED-SIDECAR-PATH",
            "artifacts": {
                role: {
                    "path": "HOSTILE-PERSISTED-PATH",
                    "sha256": "a" * 64,
                    "generation_proof": {"persisted": True},
                }
                for role in roles
            },
        },
        current_artifacts={
            role: {"path": path.resolve().as_posix(), "sha256": "a" * 64}
            for role, path in current_paths.items()
        },
    )
    selected: list[Path] = []

    def source_from_fresh_path(role: str, path: Path, identity_valid: bool):
        selected.append(path)
        return SimpleNamespace(
            role=role, path=path, sha256="a" * 64, size_bytes=0,
            identity_valid=identity_valid, raw_bytes=b"",
        )

    monkeypatch.setattr(report, "_current_verified_research_lineage_evidence", lambda *args, **kwargs: evidence)
    monkeypatch.setattr(report, "_source_artifact", source_from_fresh_path)

    snapshot = report._current_verified_research_source_snapshot(
        "show", "EP1", stock_query=None, include_fixture_verification=False
    )

    assert selected == [current_paths[role] for role in roles]
    assert snapshot.lineage_manifest is evidence.publisher_manifest


def test_publisher_lineage_manifest_keeps_sidecar_and_generation_proofs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from tests.test_latest_episode_verified_research_report_workflow_runner import _write_completed_artifacts
    from corpus_ingest_core.verified_research_report import assemble_verified_research_report

    _write_completed_artifacts(monkeypatch, tmp_path)

    assembly = assemble_verified_research_report("gooaye", "EP700", stock_query=None)

    lineage = assembly.lineage_manifest
    assert lineage["sidecar_path"].endswith("EP700.lineage.json")
    assert all(
        isinstance(entry.get("generation_proof"), dict)
        for entry in lineage["artifacts"].values()
    )


def test_external_default_fixture_path_supports_public_assembly_and_revalidation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from tests.test_latest_episode_verified_research_report_workflow_runner import (
        _mark_boundary_fixture_verified,
        _record_current_018_lineage,
        _write_completed_artifacts,
    )
    from corpus_ingest_core import revalidate_verified_research_report_sources
    from corpus_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    fixture = _mark_boundary_fixture_verified(monkeypatch, tmp_path)
    assert fixture.parent != tmp_path / "corpus"
    _record_current_018_lineage(include_fixture_verification=True)
    bundle = publish_verified_research_report_bundle(
        assemble_verified_research_report(
            "gooaye", "EP700", stock_query=None, include_fixture_verification=True
        )
    )

    result = revalidate_verified_research_report_sources("gooaye", "EP700", bundle.source_digest)

    assert result.source_currentness_status == "current"
    assert result.failed_roles == []


def test_external_default_fixture_symlink_is_rejected_by_public_assembly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from tests.test_latest_episode_verified_research_report_workflow_runner import (
        _mark_boundary_fixture_verified,
        _record_current_018_lineage,
        _write_completed_artifacts,
    )
    from corpus_ingest_core import VerifiedResearchReportInputError
    from corpus_ingest_core.verified_research_report import assemble_verified_research_report

    _write_completed_artifacts(monkeypatch, tmp_path)
    fixture = _mark_boundary_fixture_verified(monkeypatch, tmp_path)
    _record_current_018_lineage(include_fixture_verification=True)
    outside = tmp_path / "outside-fixture.yaml"
    outside.write_text("HOSTILE-FIXTURE-BODY-SENTINEL", encoding="utf-8")
    fixture.unlink()
    try:
        fixture.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"fixture symlink creation is unavailable: {exc.__class__.__name__}")

    with pytest.raises(VerifiedResearchReportInputError):
        assemble_verified_research_report(
            "gooaye", "EP700", stock_query=None, include_fixture_verification=True
        )


def test_public_revalidation_accepts_an_unchanged_publisher_bundle_without_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from tests.test_latest_episode_verified_research_report_workflow_runner import (
        _manifest,
        _write_completed_artifacts,
    )

    from corpus_ingest_core import revalidate_verified_research_report_sources
    from corpus_ingest_core.verified_research_report import (
        assemble_verified_research_report,
        publish_verified_research_report_bundle,
    )

    _write_completed_artifacts(monkeypatch, tmp_path)
    bundle = publish_verified_research_report_bundle(
        assemble_verified_research_report("gooaye", "EP700", stock_query=None)
    )
    before = _manifest(tmp_path)

    result = revalidate_verified_research_report_sources(
        "gooaye", "EP700", bundle.source_digest
    )

    assert result.bundle_self_consistency_status == "valid"
    assert result.lineage_revalidation_status == "current"
    assert result.source_currentness_status == "current"
    assert result.failed_roles == []
    assert _manifest(tmp_path) == before


@pytest.mark.parametrize("hostile_field", ["fixture_path", "snapshot_path", "boundary_input_path"])
def test_fixture_marker_paths_are_rejected_before_any_fixture_or_snapshot_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, hostile_field: str
) -> None:
    """Lineage marker paths remain comparison data, never read selectors."""
    import corpus_ingest_core.verified_research_lineage as lineage
    from corpus_ingest_core import storage
    from corpus_ingest_core import VerifiedResearchReportInputError

    fixture = tmp_path / "canonical-fixture.yaml"
    corpus = tmp_path / "corpus"
    boundary_path = (tmp_path / "canonical-boundary.json").resolve().as_posix()
    snapshot = (
        corpus / "show" / "verified-research" / "preverification-boundaries"
        / f"{storage.title_slug('EP1', 'episode')}-{'a' * 64}.json"
    ).resolve().as_posix()
    marker = {
        "verification_mode": lineage.VERIFICATION_MODE,
        "fixture_path": fixture.resolve().as_posix(),
        "fixture_sha256": "b" * 64,
        "boundary_input_path": boundary_path,
        "boundary_input_sha256": "a" * 64,
        "preverification_snapshot_path": snapshot,
        "preverification_snapshot_sha256": "a" * 64,
    }
    marker[{"fixture_path": "fixture_path", "snapshot_path": "preverification_snapshot_path", "boundary_input_path": "boundary_input_path"}[hostile_field]] = "HOSTILE-LINEAGE-PATH-SENTINEL"
    boundary = {
        "podcast_id": "show", "episode_ref": "EP1", "title": "Episode 1",
        "external_data_verification": marker,
    }
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus)
    monkeypatch.setattr(lineage, "_default_fixture_path", lambda: fixture)
    monkeypatch.setattr(
        lineage, "_read_bytes", lambda path, role: pytest.fail(f"hostile marker triggered {role} read")
    )
    monkeypatch.setattr(
        lineage, "secure_read_bytes", lambda *args, **kwargs: pytest.fail("hostile marker triggered secure read")
    )

    with pytest.raises(VerifiedResearchReportInputError):
        lineage._fixture_entry({"path": boundary_path}, boundary)


def test_fixture_marker_rejects_non_sha_boundary_digest_before_any_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A marker digest is shape-validated before constructing any snapshot selector."""
    import corpus_ingest_core.verified_research_lineage as lineage
    from corpus_ingest_core import VerifiedResearchReportInputError, storage

    fixture = tmp_path / "fixture.yaml"
    corpus = tmp_path / "corpus"
    boundary_path = (tmp_path / "canonical-boundary.json").resolve().as_posix()
    hostile_digest = "../HOSTILE-SNAPSHOT-SELECTOR"
    expected_snapshot = (
        corpus / "show" / "verified-research" / "preverification-boundaries"
        / f"{storage.title_slug('EP1', 'episode')}-{hostile_digest}.json"
    )
    marker = {
        "verification_mode": lineage.VERIFICATION_MODE,
        "fixture_path": fixture.resolve().as_posix(),
        "fixture_sha256": "b" * 64,
        "boundary_input_path": boundary_path,
        "boundary_input_sha256": hostile_digest,
        "preverification_snapshot_path": lineage._canonical_path(expected_snapshot),
        "preverification_snapshot_sha256": hostile_digest,
    }
    boundary = {
        "podcast_id": "show",
        "episode_ref": "EP1",
        "title": "Episode 1",
        "external_data_verification": marker,
    }
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus)
    monkeypatch.setattr(lineage, "_default_fixture_path", lambda: fixture)
    monkeypatch.setattr(
        lineage, "_read_bytes", lambda path, role: pytest.fail("invalid digest triggered a read")
    )

    with pytest.raises(VerifiedResearchReportInputError):
        lineage._fixture_entry({"path": boundary_path}, boundary)


def test_invalid_bundle_stops_before_any_current_source_or_lineage_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Invalid exact bundle evidence cannot authorize downstream artifact reads."""
    from corpus_ingest_core import revalidate_verified_research_report_sources, storage
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    bundle = tmp_path / "research-reports" / "show" / "EP1" / f"v1-{_DIGEST}"
    bundle.mkdir(parents=True)
    (bundle / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(storage, "RESEARCH_REPORTS_DIR", tmp_path / "research-reports")
    monkeypatch.setattr(
        revalidation,
        "_current_verified_research_source_snapshot",
        lambda *args, **kwargs: pytest.fail("invalid bundle read current sources"),
    )

    result = revalidate_verified_research_report_sources("show", "EP1", _DIGEST)

    assert result.bundle_self_consistency_status == "invalid"
    assert result.lineage_revalidation_status == "not_evaluated"
    assert result.source_currentness_status == "not_evaluated"
    assert all(value == "not_evaluated" for name, value in result.checks.items() if name != "bundle_self_consistency")


@pytest.mark.parametrize(
    ("podcast_id", "episode_ref", "digest"),
    [
        ("../show", "EP1", _DIGEST),
        ("show", "latest", _DIGEST),
        ("show", "NEXT", _DIGEST),
        ("show", "EP1", _DIGEST.upper()),
    ],
)
def test_public_seam_rejects_invalid_or_reserved_exact_locator(
    podcast_id: str, episode_ref: str, digest: str
) -> None:
    from corpus_ingest_core import (
        VerifiedResearchReportSourceRevalidationInputError,
        revalidate_verified_research_report_sources,
    )

    with pytest.raises(VerifiedResearchReportSourceRevalidationInputError):
        revalidate_verified_research_report_sources(podcast_id, episode_ref, digest)


def test_unsupported_assembly_options_short_circuit_before_current_lineage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, _snapshot = _valid_evidence_and_snapshot(tmp_path)
    evidence.manifest["assembly_options"] = {"stock_query": "SECRET-STOCK"}
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation,
        "_current_verified_research_source_snapshot",
        lambda *args, **kwargs: pytest.fail("unsupported options read current lineage"),
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.checks["assembly_options"] == "invalid"
    assert result.lineage_revalidation_status == "not_evaluated"
    assert result.source_currentness_status == "stale_or_invalid"
    assert "SECRET-STOCK" not in repr(result)


@pytest.mark.parametrize(
    ("message", "status"),
    [
        ("verified report lineage is missing or untrusted", "missing"),
        ("verified report transcript lineage is stale or invalid", "stale_or_invalid"),
    ],
)
def test_current_lineage_failure_is_bounded_and_classified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, message: str, status: str
) -> None:
    from corpus_ingest_core import VerifiedResearchReportInputError
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, _snapshot = _valid_evidence_and_snapshot(tmp_path)
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation,
        "_current_verified_research_source_snapshot",
        lambda *args, **kwargs: (_ for _ in ()).throw(VerifiedResearchReportInputError(message)),
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.lineage_revalidation_status == status
    assert result.checks["current_lineage"] == status
    assert result.source_currentness_status == "stale_or_invalid"
    assert result.failed_roles == ["lineage"]
    assert message not in repr(result)


def test_malformed_empty_current_snapshot_cannot_be_reported_current(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from corpus_ingest_core.verified_research_report import _source_digest
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    lineage = {"schema_version": "lineage-v2", "artifacts": {}}
    digest = _source_digest(
        podcast_id="show", episode_ref="EP1", stock_query=None,
        include_fixture_verification=False, sources=[],
    )
    evidence = SimpleNamespace(
        status="valid",
        manifest={
            "assembly_options": {
                "stock_query": None,
                "include_fixture_verification": False,
                "verification_scope": "local_artifact_and_fixture",
            },
            "lineage": lineage,
            "source_artifacts": [],
        },
        safe_metadata=None,
    )
    snapshot = SimpleNamespace(lineage_manifest=lineage, source_artifacts=[])
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.source_currentness_status == "stale_or_invalid"
    assert result.checks["source_artifact_metadata_match"] == "mismatch"
    assert result.failed_roles


def test_published_lineage_and_digest_mismatches_have_closed_failed_roles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, snapshot = _valid_evidence_and_snapshot(tmp_path)
    evidence.manifest["lineage"] = {"hostile": "published-lineage"}
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", "f" * 64)

    assert result.lineage_revalidation_status == "mismatch"
    assert result.checks["source_digest_match"] == "mismatch"
    assert result.source_currentness_status == "stale_or_invalid"
    assert result.failed_roles == ["lineage", "source_digest"]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "hash", "size", "path"])
def test_malformed_or_tampered_source_metadata_never_becomes_current(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, snapshot = _valid_evidence_and_snapshot(
        tmp_path, roles=("transcript", "mentions")
    )
    metadata = evidence.manifest["source_artifacts"]
    if mutation == "missing":
        metadata.pop()
    elif mutation == "duplicate":
        metadata[1] = dict(metadata[0])
    elif mutation == "unknown":
        metadata[0] = {**metadata[0], "role": "unapproved-role"}
    elif mutation == "hash":
        metadata[0]["sha256"] = "0" * 64
    elif mutation == "size":
        metadata[0]["size_bytes"] += 1
    else:
        metadata[0]["path"] = "HOSTILE-MANIFEST-PATH-SENTINEL"
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.checks["source_artifact_metadata_match"] == "mismatch"
    assert result.source_currentness_status == "stale_or_invalid"
    assert result.failed_roles
    assert set(result.failed_roles) <= {
        "transcript", "mentions", "lineage", "source_digest",
    }
    assert "HOSTILE-MANIFEST-PATH-SENTINEL" not in repr(result)


def test_second_snapshot_replacement_race_fails_closed_with_source_role(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from types import SimpleNamespace
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, first = _valid_evidence_and_snapshot(tmp_path)
    original = first.source_artifacts[0]
    replacement = SimpleNamespace(
        role=original.role, path=original.path, sha256="f" * 64,
        size_bytes=original.size_bytes + 1, identity_valid=True, raw_bytes=b"replacement",
    )
    second = SimpleNamespace(lineage_manifest=first.lineage_manifest, source_artifacts=[replacement])
    snapshots = iter((first, second))
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: next(snapshots)
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.source_currentness_status == "stale_or_invalid"
    assert result.checks["source_artifact_metadata_match"] == "mismatch"
    assert result.failed_roles == ["transcript"]


def test_second_snapshot_lineage_replacement_downgrades_lineage_verdict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, first = _valid_evidence_and_snapshot(tmp_path)
    second = SimpleNamespace(
        lineage_manifest={**first.lineage_manifest, "replacement": True},
        source_artifacts=first.source_artifacts,
    )
    snapshots = iter((first, second))
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: next(snapshots)
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.lineage_revalidation_status == "stale_or_invalid"
    assert result.checks["current_lineage"] == "stale_or_invalid"
    assert result.source_currentness_status == "stale_or_invalid"
    assert result.failed_roles == ["lineage"]


def test_second_snapshot_exception_downgrades_lineage_verdict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, first = _valid_evidence_and_snapshot(tmp_path)
    calls = iter((first, RuntimeError("second snapshot sentinel")))

    def snapshots(*args, **kwargs):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(revalidation, "_current_verified_research_source_snapshot", snapshots)

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert result.lineage_revalidation_status == "stale_or_invalid"
    assert result.checks["current_lineage"] == "stale_or_invalid"
    assert result.source_currentness_status == "stale_or_invalid"
    assert result.failed_roles == ["transcript", "lineage"]


def test_public_seam_accepts_legacy_safe_and_canonical_published_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, snapshot = _valid_evidence_and_snapshot(tmp_path, legacy_safe_paths=True)
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    legacy = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)
    evidence.manifest["source_artifacts"][0]["path"] = snapshot.source_artifacts[0].path.resolve().as_posix()
    canonical = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)

    assert legacy.source_currentness_status == "current"
    assert canonical.source_currentness_status == "current"


def test_safe_metadata_discloses_stock_presence_without_stock_query_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corpus_ingest_core.models import VerifiedResearchReportCatalogItem
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    digest, evidence, snapshot = _valid_evidence_and_snapshot(tmp_path, stock_query="SECRET-STOCK")
    evidence.safe_metadata = VerifiedResearchReportCatalogItem(
        podcast_id="show", episode_ref="EP1", report_version=f"v1-{digest}",
        source_digest=digest, schema_version="latest-episode-verified-research-report-v1",
        include_fixture_verification=False, stock_query_present=True,
        semantic_review_status="passed", not_investment_advice=True,
    )
    monkeypatch.setattr(revalidation, "_exact_bundle_evidence", lambda locator: evidence)
    monkeypatch.setattr(
        revalidation, "_current_verified_research_source_snapshot", lambda *args, **kwargs: snapshot
    )

    result = revalidation.revalidate_verified_research_report_sources("show", "EP1", digest)
    serialized = revalidation.result_to_dict(result)

    assert result.safe_metadata is not None and result.safe_metadata.stock_query_present is True
    assert "SECRET-STOCK" not in repr(result)
    assert "SECRET-STOCK" not in repr(serialized)
