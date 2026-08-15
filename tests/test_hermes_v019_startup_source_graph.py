"""Focused public-seam contracts for Spec034's static source graph audit."""
from __future__ import annotations


def test_spec034_public_validator_fails_closed_without_a_published_bundle(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    monkeypatch.setattr(graph, "BUNDLE_ROOT", tmp_path / "absent")
    monkeypatch.setattr(graph, "SOURCE_MANIFEST_PATH", tmp_path / "manifest.json")

    decision = graph.validate_spec034_source_bundle()

    assert type(decision) is graph.SourceCatalogDecision
    assert decision.status == "BLOCKED_SOURCE_GRAPH"
    assert decision.bundle_valid is False
    assert decision.runtime_status == "not_run"
    assert decision.live_actions_authorized is False


def test_spec034_acquisition_rejects_existing_target_without_overwrite(monkeypatch, tmp_path):
    from scripts import acquire_spec_034_hermes_source as acquisition

    target = tmp_path / "published"
    target.mkdir()
    sentinel = target / "keep"
    sentinel.write_text("unchanged", encoding="utf-8")
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", target)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", tmp_path / "manifest.json")

    assert acquisition.main(("--write",)) == 1
    assert sentinel.read_text(encoding="utf-8") == "unchanged"


def test_spec034_graph_and_plugin_audit_are_static_claim_scoped_only():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    bundle = graph.validate_spec034_source_bundle()
    audited = graph.audit_spec034_startup_source_graph(bundle)
    plugin = graph.audit_spec034_bundled_plugin(bundle, audited)

    assert audited.status == "BLOCKED_SOURCE_GRAPH"
    assert audited.claim_graph_status == "BLOCKED_SOURCE_GRAPH"
    assert audited.claim_statuses == (
        "STATIC_SOURCE_GRAPH_CLOSED", "BLOCKED_SOURCE_GRAPH",
        "STATIC_SOURCE_GRAPH_CLOSED",
    )
    details = {name: {"complete": complete, "verdict": verdict, "blocked_reasons": reasons} for name, complete, verdict, reasons in audited.claim_details}
    assert details["credential_provider_boundary"]["complete"] is False
    assert "provider_agent_construction_dataflow_unproven_in_h2_scope" in details["credential_provider_boundary"]["blocked_reasons"]
    assert audited.whole_program_source_graph_closed is False
    assert audited.runtime_status == "not_run"
    assert audited.live_actions_authorized is False
    assert plugin.registration_status == "conditional_registration_path_verified"
    assert plugin.actual_activation_observed is False
    assert plugin.dynamic_plugin_status == "BLOCKED_DYNAMIC_PLUGIN_TARGET"


def test_spec034_receipt_rejects_forged_and_copied_decisions():
    import copy
    import pytest
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    bundle = graph.validate_spec034_source_bundle()
    audited = graph.audit_spec034_startup_source_graph(bundle)
    plugin = graph.audit_spec034_bundled_plugin(bundle, audited)

    with pytest.raises(TypeError):
        graph.project_spec034_source_graph_receipt(copy.copy(bundle), audited, plugin)
    other_bundle = graph.validate_spec034_source_bundle()
    with pytest.raises(TypeError):
        graph.project_spec034_source_graph_receipt(other_bundle, audited, plugin)
    receipt = graph.project_spec034_source_graph_receipt(bundle, audited, plugin)
    assert set(receipt) == {
        "spec_id", "status", "terminal_status", "claim_statuses", "bundle_valid",
        "whole_program_source_graph_closed", "startup_order_status", "config_status",
        "credential_status", "provider_status", "plugin_registration_status",
        "actual_activation_observed", "dynamic_plugin_status",
        "unknown_external_secret_runtime_edges", "runtime_status", "live_actions_authorized", "claim_details",
    }
    assert "plugins/" not in repr(receipt)
    assert receipt["unknown_external_secret_runtime_edges"] == "BLOCKED_SOURCE_GRAPH"
