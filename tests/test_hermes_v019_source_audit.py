"""Focused public-seam tests for Spec033's static Hermes source audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def test_acquisition_rejects_existing_target_without_overwriting_or_reporting_acquired(monkeypatch, tmp_path):
    from scripts import acquire_spec_033_hermes_source as acquisition

    target = tmp_path / "published"
    target.mkdir()
    sentinel = target / "sentinel"
    sentinel.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", tmp_path / "manifest.json")
    monkeypatch.setattr(acquisition, "_acquire", lambda: {"_staged": []})

    assert acquisition.main(("--write",)) == 1
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_acquisition_cleans_partial_staging_after_injected_write_failure(monkeypatch, tmp_path):
    from scripts import acquire_spec_033_hermes_source as acquisition

    target = tmp_path / "published"
    manifest = tmp_path / "manifest.json"
    bundle = {"files": [], "_staged": list(zip(acquisition.ALLOWLIST, (b"x",) * len(acquisition.ALLOWLIST), strict=True))}
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "_write_file", lambda *_args: (_ for _ in ()).throw(OSError("injected")))

    try:
        acquisition._write(bundle)
    except OSError:
        pass
    else:
        raise AssertionError("injected write failure was accepted")
    assert not target.exists() and not manifest.exists()


def test_acquisition_cleans_published_bundle_when_manifest_publication_fails(monkeypatch, tmp_path):
    from scripts import acquire_spec_033_hermes_source as acquisition

    target, manifest = tmp_path / "published", tmp_path / "manifest.json"
    bundle = {"files": [], "_staged": list(zip(acquisition.ALLOWLIST, (b"x",) * len(acquisition.ALLOWLIST), strict=True))}
    published = False

    def fail_manifest_publish(_path, _data):
        raise OSError("injected manifest publication failure")

    original_rename = acquisition.os.rename

    def track_bundle_publish(source, destination):
        nonlocal published
        published = True
        return original_rename(source, destination)

    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", tmp_path / "publication.lock")
    monkeypatch.setattr(acquisition, "_staging_valid", lambda *_args: True)
    monkeypatch.setattr(acquisition, "_publish_manifest_exclusive", fail_manifest_publish)
    monkeypatch.setattr(acquisition.os, "rename", track_bundle_publish)
    try:
        acquisition._write(bundle)
    except OSError:
        pass
    else:
        raise AssertionError("split publication failure was accepted")
    assert published is True and not target.exists() and not manifest.exists()


def test_acquisition_reports_cleanup_failure_and_leaves_lock_as_recovery_marker(monkeypatch, tmp_path):
    from scripts import acquire_spec_033_hermes_source as acquisition

    target, manifest = tmp_path / "published", tmp_path / "manifest.json"
    bundle = {"files": [], "_staged": list(zip(acquisition.ALLOWLIST, (b"x",) * len(acquisition.ALLOWLIST), strict=True))}
    original_rmtree = acquisition.shutil.rmtree

    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", tmp_path / "publication.lock")
    monkeypatch.setattr(acquisition, "_staging_valid", lambda *_args: True)
    monkeypatch.setattr(acquisition, "_publish_manifest_exclusive", lambda *_args: (_ for _ in ()).throw(OSError("publish failed")))

    def fail_published_cleanup(path, *args, **kwargs):
        if path == target:
            raise OSError("cleanup failed")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(acquisition.shutil, "rmtree", fail_published_cleanup)
    try:
        acquisition._write(bundle)
    except acquisition.PublicationCleanupError as error:
        assert error.residual_paths == (target,)
    else:
        raise AssertionError("cleanup failure was not reported")

    assert target.exists() and acquisition.PUBLICATION_LOCK_PATH.exists()


def test_acquisition_requires_post_publication_validation_before_success(monkeypatch, tmp_path):
    from scripts import acquire_spec_033_hermes_source as acquisition

    target, manifest = tmp_path / "published", tmp_path / "manifest.json"
    bundle = {"files": [], "_staged": list(zip(acquisition.ALLOWLIST, (b"x",) * len(acquisition.ALLOWLIST), strict=True))}
    calls: list[Path] = []
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", tmp_path / "publication.lock")
    monkeypatch.setattr(acquisition, "_staging_valid", lambda *_args: True)
    monkeypatch.setattr(acquisition, "_post_publication_valid", lambda: calls.append(target) or True)

    acquisition._write(bundle)

    assert calls == [target] and target.is_dir() and manifest.is_file()
    assert not acquisition.PUBLICATION_LOCK_PATH.exists()


def test_acquisition_rejects_manifest_created_during_publication_race(monkeypatch, tmp_path):
    from scripts import acquire_spec_033_hermes_source as acquisition

    target, manifest = tmp_path / "published", tmp_path / "manifest.json"
    bundle = {"files": [], "_staged": list(zip(acquisition.ALLOWLIST, (b"x",) * len(acquisition.ALLOWLIST), strict=True))}
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", tmp_path / "publication.lock")
    monkeypatch.setattr(acquisition, "_staging_valid", lambda *_args: True)

    original_publish = acquisition._publish_manifest_exclusive

    def race_publish(path, data):
        path.write_text("concurrent", encoding="utf-8")
        return original_publish(path, data)

    monkeypatch.setattr(acquisition, "_publish_manifest_exclusive", race_publish)
    try:
        acquisition._write(bundle)
    except FileExistsError:
        pass
    else:
        raise AssertionError("concurrent manifest publication was overwritten")

    assert manifest.read_text(encoding="utf-8") == "concurrent"
    assert not target.exists() and not acquisition.PUBLICATION_LOCK_PATH.exists()


def test_validate_bundle_fail_closes_when_the_fixed_bundle_is_absent(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    monkeypatch.setattr(audit, "BUNDLE_ROOT", tmp_path / "missing")
    monkeypatch.setattr(audit, "SOURCE_MANIFEST_PATH", tmp_path / "source-bundle-manifest.json")
    decision = audit.validate_hermes_v019_source_bundle()

    assert type(decision) is audit.SourceBundleDecision
    assert decision.status == "BLOCKED_SOURCE_GRAPH"
    assert decision.runtime_status == "not_run"
    assert decision.live_actions_authorized is False


def test_validate_bundle_rejects_manifest_digest_drift(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    source_root = audit.BUNDLE_ROOT
    manifest = json.loads(audit.SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    target_root = tmp_path / "bundle"
    for record in manifest["files"]:
        source = source_root / record["path"]
        target = target_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    manifest["files"][0]["sha256"] = "0" * 64
    target_manifest = tmp_path / "manifest.json"
    target_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(audit, "BUNDLE_ROOT", target_root)
    monkeypatch.setattr(audit, "SOURCE_MANIFEST_PATH", target_manifest)

    decision = audit.validate_hermes_v019_source_bundle()

    assert decision.status == "BLOCKED_SOURCE_GRAPH"
    assert decision.reason == "source_integrity_mismatch"


def test_validate_bundle_rejects_tree_identity_drift(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    manifest = json.loads(audit.SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["tree_sha"] = "0" * 40
    target_manifest = tmp_path / "manifest.json"
    target_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(audit, "SOURCE_MANIFEST_PATH", target_manifest)

    decision = audit.validate_hermes_v019_source_bundle()

    assert decision.status == "BLOCKED_SOURCE_GRAPH"
    assert decision.reason == "bundle_identity_mismatch"


def test_validate_bundle_rejects_extra_saved_source_path(tmp_path, monkeypatch):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    source_root = audit.BUNDLE_ROOT
    manifest = audit.SOURCE_MANIFEST_PATH
    target_root = tmp_path / "bundle"
    for record in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
        source = source_root / record["path"]
        target = target_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    (target_root / "unapproved.py").write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(audit, "BUNDLE_ROOT", target_root)

    decision = audit.validate_hermes_v019_source_bundle()

    assert decision.status == "BLOCKED_SOURCE_GRAPH"
    assert decision.reason == "bundle_filesystem_allowlist_mismatch"


def test_validate_bundle_rejects_coordinated_manifest_and_source_mutation(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    manifest = json.loads(audit.SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    root = tmp_path / "bundle"
    for record in manifest["files"]:
        source = audit.BUNDLE_ROOT / record["path"]
        target = root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        if record["path"] == "model_tools.py":
            data += b"# coordinated mutation\n"
            record["git_blob_sha"] = hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
            record["sha256"] = hashlib.sha256(data).hexdigest()
            record["byte_length"] = len(data)
        target.write_bytes(data)
    target_manifest = tmp_path / "manifest.json"
    target_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(audit, "BUNDLE_ROOT", root)
    monkeypatch.setattr(audit, "SOURCE_MANIFEST_PATH", target_manifest)

    assert audit.validate_hermes_v019_source_bundle().reason == "authoritative_blob_identity_mismatch"


def test_validate_bundle_revalidates_fixed_manifest_and_pinned_pyproject_bytes():
    from podcast_ingest_core import hermes_v019_source_audit as audit

    decision = audit.validate_hermes_v019_source_bundle()

    assert decision.bundle_valid is True
    assert decision.project_name == "hermes-agent"
    assert decision.project_version == "0.19.0"
    assert decision.cli_entrypoints == ("hermes", "hermes-acp", "hermes-agent")


def test_ast_caller_and_loader_edge_models_exclude_nested_scope_calls():
    from podcast_ingest_core import hermes_v019_source_audit as audit

    nested_only = b"def caller():\n    def nested():\n        discover_plugins()\n"
    nested_edges = b"def caller(force=False):\n    def nested():\n        required_edge()\n        manager.discover_and_load(force=force)\n"
    assert audit._function_has_call(nested_only, "caller", "discover_plugins") is False
    assert audit._function_edges(nested_edges, None, "caller") == set()
    assert audit._function_has_keyword_call(
        nested_edges,
        None,
        "caller",
        "discover_and_load",
        "force",
        "force",
    ) is False


def test_loader_audit_fail_closes_when_source_changes_after_bundle_validation(monkeypatch):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    bundle = audit.validate_hermes_v019_source_bundle()
    original_read_bytes = Path.read_bytes
    plugin_reads = 0

    def mutate_after_validation(path):
        nonlocal plugin_reads
        data = original_read_bytes(path)
        if path == audit.BUNDLE_ROOT / "hermes_cli/plugins.py":
            plugin_reads += 1
            if plugin_reads == 2:
                return data + b"\n# changed after validation\n"
        return data

    monkeypatch.setattr(Path, "read_bytes", mutate_after_validation)
    result = audit.audit_hermes_v019_loader_order(bundle)

    assert plugin_reads == 2
    assert result.status == "BLOCKED_SOURCE_GRAPH"
    assert result.reason == "bundle_revalidation_failed"
    assert result.bounded_loader_edges_verified is False


def test_loader_audit_rejects_coordinated_manifest_and_source_change_after_validation(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_source_audit as audit

    bundle = audit.validate_hermes_v019_source_bundle()
    manifest = json.loads(audit.SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    original_manifest = audit.SOURCE_MANIFEST_PATH
    replacement_manifest = tmp_path / "replacement-manifest.json"
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    plugin_reads = 0
    manifest_reads = 0
    changed_data = original_read_bytes(audit.BUNDLE_ROOT / "hermes_cli/plugins.py") + b"\n# coordinated post-validation change\n"
    for record in manifest["files"]:
        if record["path"] == "hermes_cli/plugins.py":
            record["git_blob_sha"] = hashlib.sha1(f"blob {len(changed_data)}\0".encode("ascii") + changed_data).hexdigest()
            record["sha256"] = hashlib.sha256(changed_data).hexdigest()
            record["byte_length"] = len(changed_data)
    replacement_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    def coordinated_read_bytes(path):
        nonlocal plugin_reads
        data = original_read_bytes(path)
        if path == audit.BUNDLE_ROOT / "hermes_cli/plugins.py":
            plugin_reads += 1
            if plugin_reads == 2:
                return changed_data
        return data

    def coordinated_read_text(path, *args, **kwargs):
        nonlocal manifest_reads
        if path == original_manifest:
            manifest_reads += 1
            if manifest_reads == 2:
                return original_read_text(replacement_manifest, *args, **kwargs)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", coordinated_read_bytes)
    monkeypatch.setattr(Path, "read_text", coordinated_read_text)
    result = audit.audit_hermes_v019_loader_order(bundle)

    assert manifest_reads == 2 and plugin_reads == 1
    assert result.status == "BLOCKED_SOURCE_GRAPH"
    assert result.reason == "bundle_revalidation_failed"
    assert result.bounded_loader_edges_verified is False


def test_loader_audit_proves_bounded_loader_edges_but_fails_closed_at_plugin_execution():
    from podcast_ingest_core import hermes_v019_source_audit as audit

    result = audit.audit_hermes_v019_loader_order(audit.validate_hermes_v019_source_bundle())

    assert type(result) is audit.LoaderAuditDecision
    assert result.loader_path_verified is False
    assert result.bounded_loader_edges_verified is True
    assert result.force_propagation_verified is True
    assert result.plugin_context_hook_api_verified is True
    assert result.required_hook_registration_verified is False
    assert result.status == "BLOCKED_SOURCE_GRAPH"
    assert (result.import_time_status, result.call_time_status) == ("BLOCKED_SOURCE_GRAPH", "BLOCKED_SOURCE_GRAPH")
    assert result.dynamic_execution_status == "unresolved"
    assert result.official_callers == ("model_tools.py", "hermes_cli/main.py", "hermes_cli/oneshot.py")
    assert result.import_time_callers == ("model_tools.py",)
    # Pinned `oneshot.py` owns discovery in its `_validate_explicit_toolsets`
    # preflight, not in the `run_oneshot` runtime body.
    assert result.call_time_callers == ("hermes_cli/main.py", "hermes_cli/oneshot.py")
    assert result.unresolved_entrypoints == ("run_agent.py",)
    assert result.plugins_list_status == "manifest_only_not_loader_proof"


def test_projector_rejects_forged_mutated_and_mismatched_factory_decisions():
    from podcast_ingest_core import hermes_v019_source_audit as audit

    bundle = audit.validate_hermes_v019_source_bundle()
    loader = audit.audit_hermes_v019_loader_order(bundle)
    forged_bundle = object.__new__(audit.SourceBundleDecision)
    forged_loader = object.__new__(audit.LoaderAuditDecision)
    for decision, fields in ((forged_bundle, ("status", "runtime_status", "live_actions_authorized", "reason", "bundle_valid", "project_name", "project_version", "cli_entrypoints")), (forged_loader, ("status", "runtime_status", "live_actions_authorized", "loader_path_verified", "bounded_loader_edges_verified", "force_propagation_verified", "plugin_context_hook_api_verified", "required_hook_registration_verified", "import_time_status", "call_time_status", "dynamic_execution_status", "official_callers", "import_time_callers", "call_time_callers", "unresolved_entrypoints", "plugins_list_status", "reason"))):
        for field in fields:
            object.__setattr__(decision, field, getattr(bundle if decision is forged_bundle else loader, field))
    object.__setattr__(bundle, "reason", "hostile-path/credential=secret")

    for bad_bundle, bad_loader in ((forged_bundle, loader), (bundle, forged_loader), (bundle, loader)):
        try:
            audit.project_hermes_v019_source_audit_receipt(bad_bundle, bad_loader)
        except TypeError:
            pass
        else:
            raise AssertionError("forged or mutated decision was projected")


def test_projector_rejects_copied_subclassed_and_direct_constructor_decisions():
    import copy
    from podcast_ingest_core import hermes_v019_source_audit as audit

    # Even introspected issuance helpers accept only the closed factual vocabulary;
    # they cannot issue arbitrary receipt-bearing strings.
    issue_bundle = audit.validate_hermes_v019_source_bundle.__defaults__[0]
    try:
        issue_bundle(
            "BLOCKED_SOURCE_GRAPH",
            "loader_audit_pending",
            bundle_valid=True,
            project_name="hermes-agent",
            project_version="hostile-path/credential=secret",
            cli_entrypoints=("hermes",),
        )
    except TypeError:
        pass
    else:
        raise AssertionError("introspected authority issued hostile facts")
    bundle = audit.validate_hermes_v019_source_bundle()
    loader = audit.audit_hermes_v019_loader_order(bundle)

    try:
        audit.SourceBundleDecision(None, "BLOCKED_SOURCE_GRAPH", "forged")
    except TypeError:
        pass
    else:
        raise AssertionError("direct bundle construction was accepted")
    try:
        audit.LoaderAuditDecision(None, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "forged")
    except TypeError:
        pass
    else:
        raise AssertionError("direct loader construction was accepted")

    copied_bundle = copy.copy(bundle)
    copied_loader = copy.copy(loader)
    paired_bundle = audit.validate_hermes_v019_source_bundle()
    paired_loader = audit.audit_hermes_v019_loader_order(paired_bundle)
    for bad_bundle, bad_loader in ((copied_bundle, loader), (bundle, copied_loader), (bundle, paired_loader)):
        try:
            audit.project_hermes_v019_source_audit_receipt(bad_bundle, bad_loader)
        except TypeError:
            pass
        else:
            raise AssertionError("copied or mismatched decision was projected")

    class DerivedBundle(audit.SourceBundleDecision):
        __slots__ = ()

    forged_subclass = object.__new__(DerivedBundle)
    for field in ("status", "runtime_status", "live_actions_authorized", "reason", "bundle_valid", "project_name", "project_version", "cli_entrypoints", "_factory_token"):
        object.__setattr__(forged_subclass, field, getattr(bundle, field))
    try:
        audit.project_hermes_v019_source_audit_receipt(forged_subclass, loader)
    except TypeError:
        pass
    else:
        raise AssertionError("subclass decision was projected")


def test_receipt_has_exact_safe_keyset_and_never_contains_source_bytes_or_paths():
    from podcast_ingest_core import hermes_v019_source_audit as audit

    bundle = audit.validate_hermes_v019_source_bundle()
    loader = audit.audit_hermes_v019_loader_order(bundle)
    receipt = audit.project_hermes_v019_source_audit_receipt(bundle, loader)

    assert set(receipt) == {
        "spec_id", "status", "terminal_status", "bundle_valid", "project_version",
        "pinned_commit", "loader_path_verified", "import_time_plugin_discovery_present", "call_time_plugin_discovery_present", "import_time_status", "call_time_status",
        "runtime_status", "live_actions_authorized",
    }
    assert receipt["pinned_commit"] == "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
    assert receipt["terminal_status"] == "BLOCKED_SOURCE_GRAPH"
    assert receipt["import_time_plugin_discovery_present"] is True and receipt["call_time_plugin_discovery_present"] is True
    assert receipt["runtime_status"] == "not_run" and receipt["live_actions_authorized"] is False
    assert all("/" not in str(value) and "\\" not in str(value) for value in receipt.values())
