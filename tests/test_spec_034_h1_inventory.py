"""Offline contract checks for the Spec034 H1 claim-scoped inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = (
    ROOT
    / "specs"
    / "034-hermes-v019-pinned-startup-source-graph"
    / "contracts"
    / "h1-source-inventory-proposal.json"
)
RECEIPT_PATH = INVENTORY_PATH.with_name("h1-discovery-receipt.json")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_h1_inventory_is_claim_scoped_and_receipt_is_safe() -> None:
    inventory = _read_json(INVENTORY_PATH)
    receipt = _read_json(RECEIPT_PATH)

    assert inventory["schema_version"] == "spec034-h1-claim-scoped-inventory-v2"
    assert inventory["whole_program_source_graph_closed"] is False
    assert receipt["whole_program_source_graph_closed"] is False
    claim_order = (
        "startup_source_ordering",
        "credential_provider_boundary",
        "security_guidance_plugin",
    )
    assert tuple(inventory["claim_order"]) == claim_order
    assert set(inventory["claims"]) == set(claim_order)
    assert receipt["inventory_sha256"] == hashlib.sha256(INVENTORY_PATH.read_bytes()).hexdigest()

    files = inventory["files"]
    paths = [record["path"] for record in files]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths)) == inventory["union"]["files"]
    assert inventory["union"]["total_bytes"] == sum(record["byte_length"] for record in files)
    assert inventory["union"]["files"] <= inventory["ceilings"]["max_files"]
    assert inventory["union"]["total_bytes"] <= inventory["ceilings"]["max_total_bytes"]
    assert inventory["union"]["max_observed_depth"] <= inventory["ceilings"]["max_internal_depth"]

    for claim_id in claim_order:
        claim = inventory["claims"][claim_id]
        assert claim["verdict"] == "PASS_CLAIM_SCOPED_SOURCE_CLOSURE"
        assert not claim["blocked_reasons"]
        assert all(edge["resolved"] for edge in claim["required_internal_edges"])
        assert all(leaf["leaf_type"] == "out_of_claim_internal_leaf" for leaf in claim["out_of_claim_internal_leaves"])
        assert all(leaf["leaf_type"] == "out_of_claim_dynamic_leaf" for leaf in claim["out_of_claim_dynamic_leaves"])

    plugin = inventory["fixed_plugin"]
    assert plugin["literal_hooks"] == ["pre_tool_call", "transform_tool_result"]
    assert plugin["call_time_environment_predicates"] == ["SECURITY_GUIDANCE_BLOCK", "SECURITY_GUIDANCE_DISABLE"]
    assert plugin["registration_claim"] == "conditional_registration_path_candidate"
    assert plugin["actual_activation_observed"] is False
    assert inventory["h2_inventory_approved"] is False
    assert inventory["runtime_status"] == "not_run"
    assert inventory["live_actions_authorized"] is False
    assert receipt["source_bytes_in_receipt"] is False
    assert receipt["h2_inventory_approved"] is False
    assert receipt["runtime_status"] == "not_run"
    assert receipt["live_actions_authorized"] is False
    receipt_text = RECEIPT_PATH.read_text(encoding="utf-8").lower()
    assert not any(marker in receipt_text for marker in ("http://", "https://", "traceback", "exception", "\\\\"))
