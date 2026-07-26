"""Focused Core contracts for SPEC 020 verified report catalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64


def _use_catalog_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    from podcast_ingest_core import storage

    root = tmp_path / "research-reports"
    monkeypatch.setattr(storage, "RESEARCH_REPORTS_DIR", root)
    return root


def _manifest(podcast_id: str, episode_ref: str, digest: str, **overrides: object) -> dict:
    payload = {
        "schema_version": "latest-episode-verified-research-report-v1",
        "report_version": f"v1-{digest}",
        "source_digest": digest,
        "episode_identity": {"podcast_id": podcast_id, "episode_ref": episode_ref},
        "assembly_options": {"include_fixture_verification": False, "stock_query": None},
        "quality_gates": {
            "semantic_review_status": "passed",
            "not_investment_advice": True,
        },
    }
    payload.update(overrides)
    return payload


def _write_manifest_bundle(
    root: Path, podcast_id: str, episode_ref: str, digest: str, **overrides: object
) -> Path:
    bundle = root / podcast_id / episode_ref / f"v1-{digest}"
    bundle.mkdir(parents=True)
    (bundle / "manifest.json").write_text(
        json.dumps(_manifest(podcast_id, episode_ref, digest, **overrides)), encoding="utf-8"
    )
    (bundle / "report.json").write_text("report body sentinel", encoding="utf-8")
    (bundle / "report.md").write_text("markdown body sentinel", encoding="utf-8")
    return bundle


def _write_inspectable_bundle(root: Path, podcast_id: str, episode_ref: str, digest: str) -> Path:
    import hashlib

    bundle = root / podcast_id / episode_ref / f"v1-{digest}"
    bundle.mkdir(parents=True)
    report_json = {
        "schema_version": "latest-episode-verified-research-report-v1",
        "report_version": f"v1-{digest}",
        "source_digest": digest,
        "episode_identity": {"podcast_id": podcast_id, "episode_ref": episode_ref},
        "not_investment_advice": True,
    }
    report_json_bytes = json.dumps(report_json, sort_keys=True).encode("utf-8")
    report_markdown_bytes = b"# Verified report\\n"
    (bundle / "report.json").write_bytes(report_json_bytes)
    (bundle / "report.md").write_bytes(report_markdown_bytes)
    manifest = _manifest(
        podcast_id,
        episode_ref,
        digest,
        bundle_files={
            "report.json": {
                "sha256": hashlib.sha256(report_json_bytes).hexdigest(),
                "size_bytes": len(report_json_bytes),
            },
            "report.md": {
                "sha256": hashlib.sha256(report_markdown_bytes).hexdigest(),
                "size_bytes": len(report_markdown_bytes),
            },
        },
    )
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return bundle


def test_list_discovers_only_safe_canonical_manifest_summaries_without_body_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """List is bounded, deterministic, safe-projection-only, and read-only."""
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    first = _write_manifest_bundle(root, "beta", "EP2", _DIGEST_B)
    _write_manifest_bundle(root, "alpha", "EP3", _DIGEST_A)
    _write_manifest_bundle(root, "alpha", "EP1", _DIGEST_B)
    _write_manifest_bundle(root, "alpha", "EP1", _DIGEST_A)
    malformed = root / "alpha" / "EP0" / f"v1-{_DIGEST_A}"
    malformed.mkdir(parents=True)
    (malformed / "manifest.json").write_text("{bad json", encoding="utf-8")
    noncanonical = root / "alpha" / "EP0" / f"v2-{_DIGEST_A}"
    noncanonical.mkdir(parents=True)
    (noncanonical / "manifest.json").write_text("{}", encoding="utf-8")
    (first / "report.json").write_text("report body sentinel", encoding="utf-8")
    (first / "report.md").write_text("markdown body sentinel", encoding="utf-8")

    page = list_verified_research_reports(limit=3)

    assert [(item.podcast_id, item.episode_ref, item.report_version) for item in page.items] == [
        ("alpha", "EP1", f"v1-{_DIGEST_A}"),
        ("alpha", "EP1", f"v1-{_DIGEST_B}"),
        ("alpha", "EP3", f"v1-{_DIGEST_A}"),
    ]
    assert page.limit == 3
    assert page.returned_count == 3
    assert page.catalog_root_status == "available"
    assert page.traversal_status == "complete"
    assert page.items[0].stock_query_present is False
    assert page.items[0].not_investment_advice is True
    assert "report body sentinel" not in repr(page)
    assert "markdown body sentinel" not in repr(page)

    filtered = list_verified_research_reports(podcast_id="alpha", episode_ref="EP3")
    assert [(item.podcast_id, item.episode_ref) for item in filtered.items] == [("alpha", "EP3")]


def test_list_missing_root_is_empty_and_input_is_bounded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        VerifiedResearchReportCatalogInputError,
        list_verified_research_reports,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    before = list(tmp_path.rglob("*"))

    page = list_verified_research_reports()

    assert page.items == []
    assert page.limit == 50
    assert page.returned_count == 0
    assert page.catalog_root_status == "missing"
    assert page.traversal_status == "complete"
    assert list(tmp_path.rglob("*")) == before
    for kwargs in (
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"podcast_id": "../escape"},
        {"episode_ref": "EP/1"},
    ):
        with pytest.raises(VerifiedResearchReportCatalogInputError):
            list_verified_research_reports(**kwargs)

    assert not root.exists()


def test_list_skips_unsafe_locator_directory_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    _write_manifest_bundle(root, "safe-show", "EP1", _DIGEST_A)
    _write_manifest_bundle(root, "unsafe_name", "EP2", _DIGEST_B)

    page = list_verified_research_reports()

    assert [(item.podcast_id, item.episode_ref) for item in page.items] == [("safe-show", "EP1")]


def test_list_fails_closed_at_the_per_level_entry_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    root.mkdir()
    for number in range(1_001):
        (root / f"show-{number}").mkdir()

    page = list_verified_research_reports()

    assert page.items == []
    assert page.catalog_root_status == "available"
    assert page.traversal_status == "incomplete_entry_cap"


def test_list_never_reads_report_or_source_bodies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_manifest_bundle(root, "show", "EP1", _DIGEST_A)
    artifacts = tmp_path / "source-artifacts"
    artifacts.mkdir()
    for name in ("transcript.json", "source.json"):
        (artifacts / name).write_text("body read sentinel", encoding="utf-8")
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.name in {"report.json", "report.md", "transcript.json", "source.json"}:
            raise AssertionError(f"catalog read forbidden body: {path.name}")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    page = list_verified_research_reports()

    assert page.returned_count == 1


def test_list_skips_symlinked_or_junctioned_podcast_directories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    _write_manifest_bundle(root, "safe-show", "EP1", _DIGEST_A)
    outside = tmp_path / "outside"
    _write_manifest_bundle(outside, "outside-show", "EP2", _DIGEST_B)
    linked = root / "linked-show"
    try:
        linked.symlink_to(outside / "outside-show", target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable on this platform: {exc.__class__.__name__}")

    page = list_verified_research_reports()

    assert [(item.podcast_id, item.episode_ref) for item in page.items] == [("safe-show", "EP1")]


def test_list_skips_windows_junctioned_podcast_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import os
    import subprocess

    from podcast_ingest_core import list_verified_research_reports

    if os.name != "nt":
        pytest.skip("Windows junction creation is unavailable on this platform")
    root = _use_catalog_root(monkeypatch, tmp_path)
    _write_manifest_bundle(root, "safe-show", "EP1", _DIGEST_A)
    outside = tmp_path / "outside"
    _write_manifest_bundle(outside, "outside-show", "EP2", _DIGEST_B)
    junction = root / "junction-show"
    created = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside / "outside-show")],
        capture_output=True,
        check=False,
        text=True,
    )
    if created.returncode != 0:
        pytest.skip("Windows junction creation is unavailable in this test environment")

    page = list_verified_research_reports()

    assert [(item.podcast_id, item.episode_ref) for item in page.items] == [("safe-show", "EP1")]


def test_search_matches_only_normalized_safe_locator_fields_without_body_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import search_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_manifest_bundle(
        root,
        "alpha-show",
        "EP7",
        _DIGEST_A,
        assembly_options={"include_fixture_verification": True, "stock_query": "secret-stock"},
        arbitrary_note="hidden manifest sentinel",
    )
    (bundle / "report.json").write_text("hidden report sentinel", encoding="utf-8")
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.name == "report.json":
            raise AssertionError("search read report body")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    safe_match = search_verified_research_reports("  alpha-show  ")
    stock_match = search_verified_research_reports("secret-stock")
    arbitrary_match = search_verified_research_reports("hidden manifest sentinel")
    body_match = search_verified_research_reports("hidden report sentinel")

    assert [(item.podcast_id, item.episode_ref) for item in safe_match.items] == [("alpha-show", "EP7")]
    assert stock_match.items == []
    assert arbitrary_match.items == []
    assert body_match.items == []


def test_search_rejects_blank_control_and_oversize_queries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        VerifiedResearchReportCatalogInputError,
        search_verified_research_reports,
    )

    _use_catalog_root(monkeypatch, tmp_path)

    for query in ("", " \t\n ", "bad\x00query", "x" * 257):
        with pytest.raises(VerifiedResearchReportCatalogInputError):
            search_verified_research_reports(query)


def test_inspect_verifies_exact_bundle_self_consistency_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        inspect_verified_research_report,
        verified_research_report_catalog_result_to_dict,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)
    serialized = verified_research_report_catalog_result_to_dict(inspection)

    assert inspection.locator == {
        "podcast_id": "show",
        "episode_ref": "EP1",
        "source_digest": _DIGEST_A,
    }
    assert inspection.bundle_self_consistency_status == "valid"
    assert inspection.source_currentness_status == "not_evaluated"
    assert all(inspection.checks.values())
    assert inspection.safe_metadata is not None
    assert inspection.not_investment_advice is True
    assert "manifest.json" not in repr(inspection)
    assert str(root) not in repr(inspection)
    assert serialized["source_currentness_status"] == "not_evaluated"
    assert str(root) not in repr(serialized)


@pytest.mark.parametrize(
    ("mutation", "failed_check"),
    [
        ("extra_file", "exact_file_set"),
        ("unsupported_schema", "manifest_schema"),
        ("manifest_identity", "identity"),
        ("report_identity", "report_json_integrity"),
        ("markdown_hash", "report_markdown_integrity"),
        ("malformed_manifest", "manifest_schema"),
    ],
)
def test_inspect_fail_closes_on_structural_and_integrity_tampering(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation: str,
    failed_check: str,
) -> None:
    import hashlib

    from podcast_ingest_core import inspect_verified_research_report

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    manifest_path = bundle / "manifest.json"
    if mutation == "extra_file":
        (bundle / "extra.txt").write_text("unexpected", encoding="utf-8")
    elif mutation == "unsupported_schema":
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema_version"] = "unsupported"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    elif mutation == "manifest_identity":
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["episode_identity"]["episode_ref"] = "EP2"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    elif mutation == "report_identity":
        report_path = bundle / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["episode_identity"]["episode_ref"] = "EP2"
        raw = json.dumps(report, sort_keys=True).encode("utf-8")
        report_path.write_bytes(raw)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["bundle_files"]["report.json"] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    elif mutation == "markdown_hash":
        (bundle / "report.md").write_text("tampered", encoding="utf-8")
    else:
        manifest_path.write_text("{bad json", encoding="utf-8")

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "invalid"
    assert inspection.source_currentness_status == "not_evaluated"
    assert inspection.checks[failed_check] is False
    assert inspection.safe_metadata is None or "source_artifacts" not in repr(inspection.safe_metadata)


def test_inspect_never_opens_source_or_lineage_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import inspect_verified_research_report

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    source_path = tmp_path / "source-artifact.json"
    source_path.write_text("source body sentinel", encoding="utf-8")
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_artifacts"] = [{"path": str(source_path), "role": "transcript"}]
    manifest["lineage"] = {"path": str(source_path)}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.name == "source-artifact.json":
            raise AssertionError("inspect read source artifact")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "valid"
    assert inspection.source_currentness_status == "not_evaluated"


def test_inspect_missing_bundle_and_invalid_locator_are_bounded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        VerifiedResearchReportCatalogInputError,
        inspect_verified_research_report,
    )

    _use_catalog_root(monkeypatch, tmp_path)

    missing = inspect_verified_research_report("show", "EP1", _DIGEST_A)
    assert missing.bundle_self_consistency_status == "not_found"
    assert missing.source_currentness_status == "not_evaluated"
    assert all(value is False for value in missing.checks.values())
    with pytest.raises(VerifiedResearchReportCatalogInputError):
        inspect_verified_research_report("../show", "EP1", "A" * 64)


def test_inspect_rejects_noncanonical_actual_version_name_on_windows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import os

    from podcast_ingest_core import inspect_verified_research_report

    if os.name != "nt":
        pytest.skip("case-insensitive Windows directory lookup is unavailable")
    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    bundle.rename(bundle.with_name(f"v1-{_DIGEST_A.upper()}"))

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status != "valid"
    assert inspection.checks["canonical_version"] is False


def test_inspect_rejects_out_of_root_symlinked_version_before_manifest_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import inspect_verified_research_report

    root = _use_catalog_root(monkeypatch, tmp_path)
    outside = tmp_path / "outside"
    target = _write_inspectable_bundle(outside, "outside", "EP1", _DIGEST_A)
    episode_dir = root / "show" / "EP1"
    episode_dir.mkdir(parents=True)
    version_link = episode_dir / f"v1-{_DIGEST_A}"
    try:
        version_link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable on this platform: {exc.__class__.__name__}")

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "invalid"
    assert inspection.source_currentness_status == "not_evaluated"
    assert inspection.checks["containment"] is False


def test_inspect_keeps_self_consistency_separate_from_list_eligibility(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import inspect_verified_research_report

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["quality_gates"]["semantic_review_status"] = "not-run"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "valid"
    assert inspection.checks["identity"] is True
    assert inspection.safe_metadata is None


def test_list_and_search_skip_bundles_without_exact_three_regular_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        list_verified_research_reports,
        search_verified_research_reports,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    missing_bundle = _write_manifest_bundle(root, "missing-files", "EP1", _DIGEST_A)
    (missing_bundle / "report.json").unlink()
    (missing_bundle / "report.md").unlink()
    extra_bundle = _write_manifest_bundle(root, "extra-file", "EP2", _DIGEST_B)
    (extra_bundle / "report.json").write_text("must not be read", encoding="utf-8")
    (extra_bundle / "report.md").write_text("must not be read", encoding="utf-8")
    (extra_bundle / "unexpected.bin").write_bytes(b"unexpected")
    nonregular_bundle = _write_manifest_bundle(root, "nonregular", "EP3", _DIGEST_A)
    (nonregular_bundle / "report.json").unlink()
    (nonregular_bundle / "report.json").mkdir()

    listed = list_verified_research_reports()
    searched = search_verified_research_reports("file")

    assert listed.items == []
    assert searched.items == []


@pytest.mark.parametrize("episode_ref", ["latest", "LATEST", "Next", "nExT"])
def test_catalog_rejects_reserved_episode_selectors_case_insensitively(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, episode_ref: str
) -> None:
    from podcast_ingest_core import (
        VerifiedResearchReportCatalogInputError,
        inspect_verified_research_report,
        list_verified_research_reports,
        search_verified_research_reports,
    )

    _use_catalog_root(monkeypatch, tmp_path)

    with pytest.raises(VerifiedResearchReportCatalogInputError):
        list_verified_research_reports(episode_ref=episode_ref)
    with pytest.raises(VerifiedResearchReportCatalogInputError):
        search_verified_research_reports("show", episode_ref=episode_ref)
    with pytest.raises(VerifiedResearchReportCatalogInputError):
        inspect_verified_research_report("show", episode_ref, _DIGEST_A)


def test_catalog_requires_storage_canonical_lowercase_podcast_slug(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        VerifiedResearchReportCatalogInputError,
        inspect_verified_research_report,
        list_verified_research_reports,
        search_verified_research_reports,
    )

    _use_catalog_root(monkeypatch, tmp_path)

    with pytest.raises(VerifiedResearchReportCatalogInputError):
        list_verified_research_reports(podcast_id="Upper-Show")
    with pytest.raises(VerifiedResearchReportCatalogInputError):
        search_verified_research_reports("show", podcast_id="Upper-Show")
    with pytest.raises(VerifiedResearchReportCatalogInputError):
        inspect_verified_research_report("Upper-Show", "EP1", _DIGEST_A)


def test_list_and_search_fail_closed_for_unsafe_catalog_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        list_verified_research_reports,
        search_verified_research_reports,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    root.write_text("not a directory", encoding="utf-8")

    listed = list_verified_research_reports()
    searched = search_verified_research_reports("show")

    for page in (listed, searched):
        assert page.items == []
        assert page.catalog_root_status == "invalid"
        assert page.traversal_status == "incomplete_catalog_root"
        assert str(root) not in repr(page)


def test_list_rejects_symlinked_catalog_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    target = tmp_path / "outside-root"
    target.mkdir()
    try:
        root.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable on this platform: {exc.__class__.__name__}")

    page = list_verified_research_reports()

    assert page.items == []
    assert page.catalog_root_status == "invalid"
    assert page.traversal_status == "incomplete_catalog_root"


def test_list_fails_closed_when_catalog_root_cannot_be_lstatd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import list_verified_research_reports

    root = _use_catalog_root(monkeypatch, tmp_path)
    root.mkdir()
    original_lstat = Path.lstat

    def denied_lstat(path: Path):
        if path == root:
            raise OSError("read denied")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", denied_lstat)

    page = list_verified_research_reports()

    assert page.items == []
    assert page.catalog_root_status == "invalid"
    assert page.traversal_status == "incomplete_catalog_root"


def test_untrusted_false_investment_disclaimer_is_not_catalog_safe_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from podcast_ingest_core import (
        inspect_verified_research_report,
        list_verified_research_reports,
        search_verified_research_reports,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["quality_gates"]["not_investment_advice"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    listed = list_verified_research_reports()
    searched = search_verified_research_reports("show")
    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert listed.items == []
    assert searched.items == []
    assert inspection.bundle_self_consistency_status == "valid"
    assert inspection.safe_metadata is None
    assert inspection.not_investment_advice is None


def test_list_and_search_never_open_report_bodies_through_common_file_apis(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Manifest reads are allowed; every report-body read route is forbidden."""
    import builtins
    import os

    from podcast_ingest_core import (
        list_verified_research_reports,
        search_verified_research_reports,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    _write_manifest_bundle(root, "show", "EP1", _DIGEST_A)
    body_names = {"report.json", "report.md", "transcript.json", "source.json"}
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    original_path_open = Path.open
    original_open = builtins.open
    original_os_open = os.open

    def forbid_body_path(path: object) -> None:
        if Path(path).name in body_names:
            raise AssertionError(f"catalog opened forbidden body: {path}")

    def guarded_read_bytes(path: Path) -> bytes:
        forbid_body_path(path)
        return original_read_bytes(path)

    def guarded_read_text(path: Path, *args: object, **kwargs: object) -> str:
        forbid_body_path(path)
        return original_read_text(path, *args, **kwargs)

    def guarded_path_open(path: Path, *args: object, **kwargs: object):
        forbid_body_path(path)
        return original_path_open(path, *args, **kwargs)

    def guarded_open(file: object, *args: object, **kwargs: object):
        forbid_body_path(file)
        return original_open(file, *args, **kwargs)

    def guarded_os_open(path: object, *args: object, **kwargs: object) -> int:
        forbid_body_path(path)
        return original_os_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(os, "open", guarded_os_open)

    assert list_verified_research_reports().returned_count == 1
    assert search_verified_research_reports("show").returned_count == 1


def test_inspect_rejects_manifest_size_mismatch_even_when_hash_matches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import hashlib

    from podcast_ingest_core import inspect_verified_research_report

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_bytes = (bundle / "report.json").read_bytes()
    manifest["bundle_files"]["report.json"] = {
        "sha256": hashlib.sha256(report_bytes).hexdigest(),
        "size_bytes": len(report_bytes) + 1,
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "invalid"
    assert inspection.checks["report_json_integrity"] is False


def test_inspect_opens_one_report_json_snapshot_for_hash_and_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The public inspect seam opens report.json once for its valid hash and identity."""
    import os

    from podcast_ingest_core import inspect_verified_research_report

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    report_path = bundle / "report.json"
    original_os_open = os.open
    report_open_count = 0

    def counting_os_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        nonlocal report_open_count
        if Path(path) == report_path:
            report_open_count += 1
        return original_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", counting_os_open)

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "valid"
    assert inspection.checks["report_json_integrity"] is True
    assert report_open_count == 1


def test_inspect_rejects_sparse_report_larger_than_the_documented_bound_before_body_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The public inspect seam bounds report bytes without allocating a large body."""
    import os

    from podcast_ingest_core import inspect_verified_research_report
    from podcast_ingest_core import verified_research_report_catalog as catalog

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    markdown_path = bundle / "report.md"
    markdown_path.write_bytes(b"oversized report body sentinel")
    with markdown_path.open("r+b") as stream:
        stream.truncate(catalog._MAX_REPORT_BYTES + 1)
    original_read_bytes = Path.read_bytes
    original_os_open = os.open

    def reject_body_read(path: Path) -> bytes:
        if path == markdown_path:
            raise AssertionError("oversized report body was read")
        return original_read_bytes(path)

    def reject_body_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if Path(path) == markdown_path:
            raise AssertionError("oversized report body was opened")
        return original_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", reject_body_read)
    monkeypatch.setattr(os, "open", reject_body_open)

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "invalid"
    assert inspection.checks["report_markdown_integrity"] is False
    assert "oversized report body sentinel" not in repr(inspection)
    assert str(root) not in repr(inspection)


@pytest.mark.parametrize(
    ("raw_path", "normalized"),
    [
        (r"\\?\C:\catalog\report.json", r"C:\catalog\report.json"),
        (r"\\?\UNC\server\share\report.json", r"\\server\share\report.json"),
        (r"\\.\PhysicalDrive0", None),
        (r"\\?\GLOBALROOT\Device\HarddiskVolume1", None),
    ],
)
def test_windows_final_path_normalizer_accepts_only_safe_dos_or_unc_forms(
    raw_path: str, normalized: str | None
) -> None:
    from podcast_ingest_core import verified_research_report_catalog as catalog

    assert catalog._normalize_windows_final_path(raw_path) == normalized


def test_windows_handle_final_path_uses_pointer_sized_ctypes_abi(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes
    from ctypes import wintypes
    import sys
    import types

    from podcast_ingest_core import verified_research_report_catalog as catalog

    observed: dict[str, object] = {}

    class _FakeGetFinalPathNameByHandle:
        argtypes: object = None
        restype: object = None

        def __call__(self, handle: object, buffer: object, size: object, flags: object) -> int:
            observed["handle"] = handle
            observed["size"] = size
            observed["flags"] = flags
            buffer.value = r"\\?\C:\catalog\report.json"
            return len(buffer.value)

    api = _FakeGetFinalPathNameByHandle()
    kernel32 = types.SimpleNamespace(GetFinalPathNameByHandleW=api)

    def fake_windll(name: str, *, use_last_error: bool) -> object:
        observed["dll"] = (name, use_last_error)
        return kernel32

    monkeypatch.setattr(ctypes, "WinDLL", fake_windll)
    monkeypatch.setitem(
        sys.modules,
        "msvcrt",
        types.SimpleNamespace(get_osfhandle=lambda descriptor: 0x1_0000_0001),
    )

    result = catalog._windows_final_path_from_descriptor(7)

    assert str(result) == r"C:\catalog\report.json"
    assert observed["dll"] == ("kernel32", True)
    assert api.argtypes == [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    assert api.restype is wintypes.DWORD
    assert observed["handle"].value == 0x1_0000_0001


def test_windows_handle_final_path_api_failure_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes
    import sys
    import types

    from podcast_ingest_core import verified_research_report_catalog as catalog

    api = types.SimpleNamespace()
    api.GetFinalPathNameByHandleW = lambda *args: 0
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: api)
    monkeypatch.setitem(sys.modules, "msvcrt", types.SimpleNamespace(get_osfhandle=lambda descriptor: 1))

    assert catalog._windows_final_path_from_descriptor(7) is None


@pytest.mark.parametrize("target", ["manifest.json", "report.json"])
def test_catalog_fails_closed_when_a_snapshot_target_is_replaced_before_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, target: str
) -> None:
    """The public seams reject a checked pathname replaced with a different file."""
    import os

    from podcast_ingest_core import (
        inspect_verified_research_report,
        list_verified_research_reports,
    )

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    target_path = bundle / target
    replacement = bundle / f"replacement-{target}"
    replacement.write_bytes(target_path.read_bytes())
    original_os_open = os.open
    replaced = False

    def replace_before_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        nonlocal replaced
        if not replaced and Path(path) == target_path:
            replaced = True
            replacement.replace(target_path)
        return original_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", replace_before_open)

    if target == "manifest.json":
        assert list_verified_research_reports().items == []
    else:
        inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)
        assert inspection.bundle_self_consistency_status == "invalid"
        assert inspection.checks["report_json_integrity"] is False


def test_catalog_rejects_mocked_reparse_attribute_without_symlink_privileges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The Windows reparse bit itself is fail-closed even without a real junction."""
    from podcast_ingest_core import inspect_verified_research_report
    from podcast_ingest_core import verified_research_report_catalog as catalog

    root = _use_catalog_root(monkeypatch, tmp_path)
    bundle = _write_inspectable_bundle(root, "show", "EP1", _DIGEST_A)
    manifest_path = bundle / "manifest.json"
    original_lstat = Path.lstat
    monkeypatch.setattr(catalog.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400, raising=False)

    class _ReparseStat:
        st_file_attributes = 0x400

        def __init__(self, original: object) -> None:
            self._original = original

        def __getattr__(self, name: str) -> object:
            return getattr(self._original, name)

    def mocked_lstat(path: Path):
        value = original_lstat(path)
        return _ReparseStat(value) if path == manifest_path else value

    monkeypatch.setattr(Path, "lstat", mocked_lstat)

    inspection = inspect_verified_research_report("show", "EP1", _DIGEST_A)

    assert inspection.bundle_self_consistency_status == "invalid"
