"""Offline-only contracts for Spec 029; no network, Docker, or Hermes runtime."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "deploy/hermes/spec029/plugin/spec029_all_block.py"


def _load_plugin(name: str):
    spec = importlib.util.spec_from_file_location(name, PLUGIN)
    assert spec and spec.loader
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    return plugin


def test_source_contract_is_pinned_but_runtime_seam_and_activation_remain_blocked():
    from podcast_ingest_core import hermes_runtime_source_contract as contract

    manifest = contract.load_pinned_runtime_manifest()
    evaluation = contract.evaluate_pinned_runtime_contract()

    assert manifest.target_commit_sha == "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
    assert evaluation.verdict is contract.ContractVerdict.BLOCKED_RUNTIME_SEAM
    assert evaluation.pinned_manifest_identity_verified is True
    assert evaluation.safe_one_shot_input_seam_verified is False
    assert evaluation.plugin_live_activation_authorized is False
    assert contract.evaluate_pinned_runtime_contract({"extra": "drift"}).verdict is contract.ContractVerdict.BLOCKED_SOURCE_DRIFT

    safe = contract.build_contract_evidence(evaluation)
    assert set(safe) == contract.SAFE_EVIDENCE_KEYS
    assert safe["pinned_manifest_identity_verified"] is True
    assert safe["plugin_live_activation_authorized"] is False
    assert "raw-source-sentinel" not in json.dumps(safe)


def test_source_evidence_rejects_forged_verified_cross_fields():
    from podcast_ingest_core import hermes_runtime_source_contract as contract

    forged = contract.RuntimeContractEvaluation(
        contract.ContractVerdict.VERIFIED,
        True,
        True,
        True,
    )
    safe = contract.build_contract_evidence(forged)

    assert safe["verdict"] == "BLOCKED_SOURCE_DRIFT"
    assert safe["pinned_manifest_identity_verified"] is False
    assert safe["safe_one_shot_input_seam_verified"] is False
    assert safe["plugin_live_activation_authorized"] is False
    assert safe["live_actions_authorized"] is False


def test_scenario_policy_is_factory_sealed_binding_derived_and_projector_is_strict():
    from podcast_ingest_core import hermes_blocked_runtime_smoke as smoke

    policy = smoke.scenario_policy(smoke.ScenarioId.S016_PREVIEW_BLOCKED)
    assert policy.expected_tool.value == "run_corpus_episode_completion_workflow"
    raw = {
        "name": policy.expected_tool.value,
        "arguments": {
            "confirm": False,
            "action": "next",
            "leak": "raw-source-sentinel",
        },
    }
    projected = smoke.project_pre_tool_attempt(policy, raw)
    assert projected.status is smoke.ProjectionStatus.ACCEPTED
    assert projected.confirm is False
    assert "raw-source-sentinel" not in json.dumps(projected.to_evidence())
    assert smoke.project_pre_tool_attempt(
        policy,
        {
            "name": policy.expected_tool.value,
            "arguments": {"confirm": 0, "action": "next"},
        },
    ).status is smoke.ProjectionStatus.ABORTED

    try:
        smoke.ScenarioPolicy(
            smoke.ScenarioId.S016_PREVIEW_BLOCKED,
            smoke.Tool.NAMED_VERIFIED_REPORT,
            False,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("ScenarioPolicy must only be created by scenario_policy()")


def test_scenario_requires_provenanced_tripwire_observation_and_preserves_failures():
    from podcast_ingest_core import hermes_blocked_runtime_smoke as smoke
    from podcast_ingest_core import hermes_mcp_deny_interposer as deny
    from podcast_ingest_core.hermes_skill_protocol import canonical_registry_tool_names_from_source

    names = canonical_registry_tool_names_from_source()
    interposer = deny.DenyInterposer.from_preflight_snapshot(names)
    policy = smoke.scenario_policy(smoke.ScenarioId.S017_CONFIRMED_BLOCKED)
    raw = {
        "name": policy.expected_tool.value,
        "arguments": {"confirm": True},
    }

    passed = smoke.evaluate_scenario(
        policy,
        (raw,),
        mcp_tripwire_observation=interposer.observe_tripwire(),
    )
    assert passed.status is smoke.ScenarioStatus.PASS
    assert smoke.build_smoke_evidence(passed)["mcp_tripwire_call_count"] == 0

    try:
        deny.TripwireObservation(0, interposer)
    except TypeError:
        pass
    else:
        raise AssertionError("TripwireObservation must be factory-issued")
    rejected = smoke.evaluate_scenario(
        policy,
        (raw,),
        mcp_tripwire_observation=object(),
    )
    rejected_evidence = smoke.build_smoke_evidence(rejected)
    assert rejected.status is smoke.ScenarioStatus.FAIL
    assert rejected_evidence["mcp_tripwire_call_count"] is None

    interposer.handle("tools/call", {"name": "raw-source-sentinel"})
    tripped = smoke.evaluate_scenario(
        policy,
        (raw,),
        mcp_tripwire_observation=interposer.observe_tripwire(),
    )
    assert tripped.status is smoke.ScenarioStatus.FAIL
    assert smoke.build_smoke_evidence(tripped)["mcp_tripwire_call_count"] == 1


def test_s019_evidence_keeps_canonical_expectation_without_ephemeral_ref():
    from podcast_ingest_core import hermes_blocked_runtime_smoke as smoke
    from podcast_ingest_core import hermes_mcp_deny_interposer as deny
    from podcast_ingest_core.hermes_skill_protocol import canonical_registry_tool_names_from_source

    policy = smoke.scenario_policy(
        smoke.ScenarioId.S019_PREVIEW_BLOCKED,
        ephemeral_episode_ref="ephemeral-ref",
    )
    interposer = deny.DenyInterposer.from_preflight_snapshot(
        canonical_registry_tool_names_from_source()
    )
    result = smoke.evaluate_scenario(
        policy,
        (
            {
                "name": policy.expected_tool.value,
                "arguments": {
                    "confirm": False,
                    "episode_ref": "ephemeral-ref",
                },
            },
        ),
        mcp_tripwire_observation=interposer.observe_tripwire(),
    )
    evidence = smoke.build_smoke_evidence(result)

    assert evidence["expected_tool"] == policy.expected_tool.value
    assert evidence["expected_confirm"] is False
    assert "ephemeral-ref" not in json.dumps(evidence)


def test_terminal_shell_exclusion_is_a_structural_control_not_an_absence_scenario():
    from podcast_ingest_core import hermes_blocked_runtime_smoke as smoke
    from podcast_ingest_core.hermes_skill_protocol import canonical_registry_tool_names_from_source

    names = canonical_registry_tool_names_from_source()
    assert smoke.ScenarioId.__members__.get("TERMINAL_FALLBACK_REJECTED") is None

    passed = smoke.evaluate_tool_surface(names, names)
    failed = smoke.evaluate_tool_surface(names | {"terminal"}, names)

    assert passed.status is smoke.SurfaceStatus.PASS
    assert passed.terminal_shell_exposed is False
    assert failed.status is smoke.SurfaceStatus.FAIL
    assert failed.terminal_shell_exposed is True
    assert smoke.build_surface_evidence(passed)["fallback_usage_claim"] is False


def test_plugin_registers_from_loader_shaped_context_with_ephemeral_control(monkeypatch):
    plugin = _load_plugin("spec029_all_block_registration")

    class FailingContext:
        def register_hook(self, _name, _callback):
            raise RuntimeError("synthetic registration failure")

    class Context:
        def __init__(self):
            self.calls = []

        def register_hook(self, name, callback):
            self.calls.append((name, callback))

    # Hermes-like contexts have no controller-added private plugin object.
    for control in (None, "wrong-control"):
        if control is None:
            monkeypatch.delenv("SPEC029_EXPECTED_TOOL", raising=False)
        else:
            monkeypatch.setenv("SPEC029_EXPECTED_TOOL", control)
        try:
            plugin.register(Context())
        except RuntimeError:
            pass
        else:
            raise AssertionError("missing or malformed ephemeral control must fail loudly")

    monkeypatch.setenv("SPEC029_EXPECTED_TOOL", "spec029-s016-next:expected-tool")
    try:
        plugin.register(FailingContext())
    except RuntimeError:
        pass
    else:
        raise AssertionError("registration failure must remain observable")
    assert plugin.registration_receipt()["registered"] is False

    ctx = Context()
    plugin.register(ctx)
    plugin.register(ctx)
    assert [name for name, _ in ctx.calls] == ["pre_tool_call"]

    callback = ctx.calls[0][1]
    records = []
    plugin._projection_sink = records.append
    first = callback(
        object(),
        tool_name="expected-tool",
        args={"confirm": False, "action": "next", "raw": "raw-source-sentinel"},
    )
    assert first == {"action": "block", "message": "SPEC029_POLICY_BLOCK"}
    first["action"] = "allow"
    second = callback(
        object(),
        tool_name="expected-tool",
        args={"confirm": False, "action": "next"},
    )
    assert second == {"action": "block", "message": "SPEC029_POLICY_BLOCK"}
    assert records[0] == {
        "projection_status": "accepted",
        "tool_matched": True,
        "confirm": False,
        "action_next": True,
        "attempt_count": 1,
        "policy_blocked": True,
        "raw_persisted": False,
    }
    assert "expected-tool" not in json.dumps(records[0])
    assert "raw-source-sentinel" not in json.dumps(records[0])
    assert records[1]["projection_status"] == "aborted"


def test_plugin_confirm_true_is_aborted_but_never_weakens_block(monkeypatch):
    plugin = _load_plugin("spec029_confirm_true")
    monkeypatch.setenv("SPEC029_EXPECTED_TOOL", "spec029-s016-next:expected-tool")

    class Context:
        def __init__(self):
            self.callback = None

        def register_hook(self, _name, callback):
            self.callback = callback

    context = Context()
    plugin.register(context)
    records = []
    plugin._projection_sink = records.append
    assert context.callback(
        object(),
        tool_name="expected-tool",
        args={"confirm": True, "action": "next"},
    ) == {"action": "block", "message": "SPEC029_POLICY_BLOCK"}
    assert records == [
        {
            "projection_status": "aborted",
            "tool_matched": None,
            "confirm": None,
            "action_next": None,
            "attempt_count": 1,
            "policy_blocked": True,
            "raw_persisted": False,
        }
    ]


def test_plugin_projection_failure_still_blocks_and_contains_no_second_tool_registry(monkeypatch):
    plugin = _load_plugin("spec029_all_block_projection")
    source = PLUGIN.read_text(encoding="utf-8")
    monkeypatch.setenv("SPEC029_EXPECTED_TOOL", "spec029-s016-next:expected-tool")

    class Context:
        def __init__(self):
            self.callbacks = []

        def register_hook(self, _name, callback):
            self.callbacks.append(callback)

    ctx = Context()
    plugin.register(ctx)
    plugin._projection_sink = lambda _: (_ for _ in ()).throw(OSError())
    assert ctx.callbacks[0](object()) == {
        "action": "block",
        "message": "SPEC029_POLICY_BLOCK",
    }
    for tool_name in (
        "run_corpus_episode_completion_workflow",
        "run_corpus_latest_episode_deterministic_workflow",
        "run_latest_episode_verified_research_report_workflow",
        "run_episode_verified_research_report_workflow",
    ):
        assert source.count(tool_name) == 0


def test_deny_interposer_never_forwards_and_observation_is_instance_bound():
    from podcast_ingest_core import hermes_mcp_deny_interposer as deny
    from podcast_ingest_core.hermes_skill_protocol import canonical_registry_tool_names_from_source

    names = canonical_registry_tool_names_from_source()
    interposer = deny.DenyInterposer.from_preflight_snapshot(names)
    other = deny.DenyInterposer.from_preflight_snapshot(names)

    assert interposer.handle("initialize", {})["ok"] is True
    assert set(interposer.handle("tools/list", {})["tools"]) == names
    assert interposer.handle("tools/call", {"name": "raw-source-sentinel"}) == {
        "ok": False,
        "error": "policy_denied",
    }
    forged = object.__new__(deny.TripwireObservation)
    object.__setattr__(forged, "_count", 0)
    object.__setattr__(forged, "_owner", other)
    object.__setattr__(forged, "_issuance_token", None)
    assert deny.verified_tripwire_count(forged) is None

    observation = interposer.observe_tripwire()
    assert deny.verified_tripwire_count(observation) == 1
    assert deny.verified_tripwire_count(observation) is None
    assert deny.verified_tripwire_count(other.observe_tripwire()) == 0
    for attribute in ("tripwire_count", "_tripwire_count"):
        try:
            setattr(interposer, attribute, 0)
        except AttributeError:
            pass
        else:
            raise AssertionError("tripwire counter must not be object-mutable")
    assert "mcp_server" not in Path(deny.__file__).read_text(encoding="utf-8")


def test_read_only_preflight_cannot_reach_activation_while_runtime_seam_is_blocked():
    from podcast_ingest_core import hermes_runtime_deployment as deployment
    from podcast_ingest_core.hermes_runtime_source_contract import (
        evaluate_pinned_runtime_contract,
    )

    facts = deployment.BaselineOverlayFacts(
        baseline_v019_image="sha256:" + "a" * 64,
        disposable_overlay_prepared=True,
        overlay_isolated_from_production=True,
        controller_controls_resolved=True,
        interposer_placement_verified=True,
        interposer_non_forwarding_verified=True,
        terminal_shell_absent=True,
        rollback_recipe_complete=True,
    )
    result = deployment.evaluate_offline_overlay_preflight(
        facts,
        evaluate_pinned_runtime_contract(),
    )
    evidence = deployment.build_preflight_evidence(result)

    assert result.status is deployment.PreflightStatus.BLOCKED_RUNTIME_SEAM
    assert result.activation_authorized is False
    assert evidence["activation_authorized"] is False
    assert evidence["live_preflight_run"] is False
    assert "sha256:" not in json.dumps(evidence)

    malformed = deployment.BaselineOverlayFacts(
        **{**facts.__dict__, "disposable_overlay_prepared": 0}
    )
    assert deployment.evaluate_offline_overlay_preflight(
        malformed,
        evaluate_pinned_runtime_contract(),
    ).status is deployment.PreflightStatus.BLOCKED_INVALID_EVIDENCE


def test_rollback_projection_distinguishes_complete_from_failed_quarantine():
    from podcast_ingest_core import hermes_runtime_deployment as deployment

    complete = deployment.evaluate_rollback(
        deployment.RollbackFacts(True, True, True, True, True)
    )
    failed = deployment.evaluate_rollback(
        deployment.RollbackFacts(True, True, True, True, False)
    )

    assert complete.status is deployment.RollbackStatus.COMPLETE
    assert complete.prior_controls_restored is True
    assert failed.status is deployment.RollbackStatus.FAILED_QUARANTINED
    assert failed.prior_controls_restored is False
    assert failed.writers_may_resume is False


def test_private_deployment_ledger_and_receipts_never_project_identities():
    from podcast_ingest_core import hermes_runtime_deployment as deployment

    try:
        deployment.PrivateDeploymentLedger("owner-forged")
    except TypeError:
        pass
    else:
        raise AssertionError("ledger must only be factory-created")

    ledger = deployment.PrivateDeploymentLedger.create("owner-029")
    safe = deployment.build_deployment_evidence(ledger)
    forged = object.__new__(deployment.PrivateDeploymentLedger)
    copied = object.__new__(deployment.PrivateDeploymentLedger)
    for name, value in ledger.__dict__.items():
        object.__setattr__(copied, name, value)

    assert ledger.owner_only is True
    assert safe == {
        "schema_version": "hermes-runtime-deployment-evidence-v1",
        "owner_ledger_present": True,
        "live_preflight_run": False,
        "raw_persisted": False,
    }
    assert deployment.build_deployment_evidence(forged)["owner_ledger_present"] is False
    assert deployment.build_deployment_evidence(copied)["owner_ledger_present"] is False
    assert "owner-029" not in json.dumps(safe)


def test_safe_evaluation_models_reject_constructor_and_copied_token_forgeries():
    from podcast_ingest_core import hermes_blocked_runtime_smoke as smoke
    from podcast_ingest_core import hermes_mcp_deny_interposer as deny
    from podcast_ingest_core import hermes_runtime_deployment as deployment
    from podcast_ingest_core.hermes_runtime_source_contract import (
        evaluate_pinned_runtime_contract,
    )
    from podcast_ingest_core.hermes_skill_protocol import (
        canonical_registry_tool_names_from_source,
    )

    constructors = (
        lambda: smoke.ScenarioEvaluation(
            smoke.ScenarioStatus.PASS,
            smoke.ScenarioId.READ_ONLY_NO_SKILL,
            0,
            0,
            None,
        ),
        lambda: smoke.SurfaceEvaluation(smoke.SurfaceStatus.PASS, True, False),
        lambda: deployment.PreflightEvaluation(
            deployment.PreflightStatus.BLOCKED_RUNTIME_SEAM,
            True,
            True,
            True,
            True,
            True,
            True,
            False,
            False,
        ),
    )
    for constructor in constructors:
        try:
            constructor()
        except TypeError:
            pass
        else:
            raise AssertionError("safe evaluation must be evaluator-issued")

    names = canonical_registry_tool_names_from_source()
    interposer = deny.DenyInterposer.from_preflight_snapshot(names)
    legal_smoke = smoke.evaluate_scenario(
        smoke.scenario_policy(smoke.ScenarioId.READ_ONLY_NO_SKILL),
        (),
        mcp_tripwire_observation=interposer.observe_tripwire(),
    )
    legal_surface = smoke.evaluate_tool_surface(names, names)
    facts = deployment.BaselineOverlayFacts(
        baseline_v019_image="sha256:" + "a" * 64,
        disposable_overlay_prepared=True,
        overlay_isolated_from_production=True,
        controller_controls_resolved=True,
        interposer_placement_verified=True,
        interposer_non_forwarding_verified=True,
        terminal_shell_absent=True,
        rollback_recipe_complete=True,
    )
    legal_preflight = deployment.evaluate_offline_overlay_preflight(
        facts,
        evaluate_pinned_runtime_contract(),
    )

    def copied_token_forgery(original, **changes):
        forged = object.__new__(type(original))
        for name, value in original.__dict__.items():
            object.__setattr__(forged, name, value)
        for name, value in changes.items():
            object.__setattr__(forged, name, value)
        return forged

    forged_smoke = copied_token_forgery(
        legal_smoke,
        status=smoke.ScenarioStatus.PASS,
        mcp_tripwire_call_count=0,
    )
    forged_surface = copied_token_forgery(
        legal_surface,
        status=smoke.SurfaceStatus.PASS,
    )
    forged_preflight = copied_token_forgery(
        legal_preflight,
        status=deployment.PreflightStatus.BLOCKED_CONTROL_PLANE,
    )

    assert smoke.build_smoke_evidence(forged_smoke)["status"] == "fail"
    assert smoke.build_surface_evidence(forged_surface)["status"] == "fail"
    preflight_safe = deployment.build_preflight_evidence(forged_preflight)
    assert preflight_safe["status"] == "BLOCKED_INVALID_EVIDENCE"
    assert preflight_safe["activation_authorized"] is False
    assert smoke.build_smoke_evidence(object())["status"] == "fail"
    assert smoke.build_surface_evidence(object())["status"] == "fail"


def test_offline_clis_reject_invalid_argv_without_echo_and_docs_remain_consistent():
    sentinel = "raw-source-sentinel"
    for script in (
        "validate_hermes_blocked_runtime_contract.py",
        "run_hermes_blocked_runtime_smoke.py",
        "run_mcp_deny_interposer.py",
        "manage_hermes_runtime_smoke_deployment.py",
    ):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), sentinel],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2
        assert sentinel not in result.stdout + result.stderr

    spec = (
        ROOT / "specs/029-hermes-blocked-tool-attempt-runtime-smoke/spec.md"
    ).read_text(encoding="utf-8")
    registry = (ROOT / "specs/README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/roadmap.md").read_text(encoding="utf-8")

    assert "v0.19 G0 Offline Refactor" in spec
    assert "observed expected high-level MCP tool-call attempt, then policy-blocked before MCP dispatch" in spec
    assert "internal Skill selection" in spec
    assert "G1 read-only preflight completed with a blocked receipt" in spec
    receipt_path = ROOT / "specs/029-hermes-blocked-tool-attempt-runtime-smoke/contracts/g1-read-only-preflight-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    from podcast_ingest_core import hermes_runtime_deployment as deployment
    assert set(receipt) == deployment.SAFE_PREFLIGHT_EVIDENCE_KEYS
    assert receipt["status"] == "BLOCKED_CONTROL_PLANE"
    assert receipt["baseline_image_pinned"] is True
    assert receipt["activation_authorized"] is False
    assert receipt["live_preflight_run"] is True
    assert receipt["raw_persisted"] is False
    assert "029-hermes-blocked-tool-attempt-runtime-smoke" in registry
    assert "next unused feature package number is **030**" in roadmap


def test_g0_controller_closed_modes_emit_fixed_nonlive_evidence():
    expected = {
        "run_mcp_deny_interposer.py": (("offline-contract",), "offline_contract"),
        "manage_hermes_runtime_smoke_deployment.py": (
            ("offline-baseline-overlay-plan",),
            "BLOCKED_RUNTIME_SEAM",
        ),
        "run_hermes_blocked_runtime_smoke.py": (("offline-validate",), "BLOCKED_RUNTIME_SEAM"),
    }
    for script, (argv, status) in expected.items():
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *argv],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        evidence = json.loads(result.stdout)
        assert evidence["status"] == status
        assert evidence["live_actions_authorized"] is False
        assert evidence["raw_persisted"] is False


def test_scenario_evidence_is_fixed_and_closed_classifier_never_returns_raw_text():
    from podcast_ingest_core import hermes_blocked_runtime_smoke as smoke
    from podcast_ingest_core import hermes_mcp_deny_interposer as deny
    from podcast_ingest_core.hermes_skill_protocol import canonical_registry_tool_names_from_source

    policy = smoke.scenario_policy(smoke.ScenarioId.S017_CONFIRMED_BLOCKED)
    interposer = deny.DenyInterposer.from_preflight_snapshot(
        canonical_registry_tool_names_from_source()
    )
    result = smoke.evaluate_scenario(
        policy,
        (
            {
                "name": policy.expected_tool.value,
                "arguments": {"confirm": True},
            },
        ),
        mcp_tripwire_observation=interposer.observe_tripwire(),
    )
    evidence = smoke.build_smoke_evidence(result)

    assert set(evidence) == smoke.SAFE_SCENARIO_EVIDENCE_KEYS
    assert evidence["internal_skill_selection_claim"] is False
    assert evidence["fallback_usage_claim"] is False
    assert "raw-source-sentinel" not in json.dumps(evidence)
    classification = smoke.classify_ephemeral_response(
        (smoke.ResponseDisposition.CLARIFICATION_ONLY,)
    )
    assert classification is smoke.ResponseDisposition.CLARIFICATION_ONLY


def test_v019_source_contract_exactly_pins_known_clean_source_and_remains_blocked():
    from podcast_ingest_core import hermes_runtime_source_contract as contract

    manifest = contract.load_pinned_runtime_manifest()
    evaluation = contract.evaluate_pinned_runtime_contract()

    assert manifest.target_commit_sha == "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
    assert contract.EXPECTED_SOURCE_BLOBS == {
        "plugins_py_blob_sha": "6ca393fca53c1fd2b3479bed72180fedcc848c88",
        "model_tools_py_blob_sha": "32394a69eec64f3d676bedb1659a6f4e94887a74",
        "tool_executor_py_blob_sha": "d235de36c03dd668bfb10377ef51c7074368c6b9",
        "hooks_blob_sha": "d3f86bd00e80254b42ea9440cdcede4ab9a0c68b",
    }
    assert evaluation.verdict is contract.ContractVerdict.BLOCKED_RUNTIME_SEAM
    assert evaluation.plugin_live_activation_authorized is False
    manifest_text = contract._MANIFEST.read_text(encoding="utf-8")
    for clause in (
        "register(ctx)",
        "register_hook",
        "pre_tool_call",
        "post_tool_call",
        "action_block_message_SPEC029_POLICY_BLOCK",
        "block_before_execution",
        "callback_exception_fail_open",
    ):
        assert clause in manifest_text


def test_v019_plugin_registers_directly_from_loader_shape_and_uses_args_callback(monkeypatch):
    plugin = _load_plugin("spec029_v019_direct_registration")
    monkeypatch.setenv("SPEC029_EXPECTED_TOOL", "spec029-s016-next:expected-tool")

    class Context:
        def __init__(self):
            self.calls = []

        def register_hook(self, name, callback):
            self.calls.append((name, callback))

    context = Context()
    plugin.register(context)
    assert [name for name, _ in context.calls] == ["pre_tool_call"]
    assert plugin.registration_receipt() == {
        "registered": True,
        "pre_hook_registered": True,
        "raw_persisted": False,
    }
    pre_hook = context.calls[0][1]
    assert pre_hook(
        object(), tool_name="expected-tool", args={"confirm": False, "action": "next"}
    ) == {"action": "block", "message": "SPEC029_POLICY_BLOCK"}
    assert pre_hook(object(), tool_name="expected-tool", arguments={"confirm": False}) == {
        "action": "block",
        "message": "SPEC029_POLICY_BLOCK",
    }


def test_disposable_overlay_lease_uses_trusted_clock_and_fails_closed(monkeypatch):
    from podcast_ingest_core import hermes_runtime_deployment as deployment

    clock = {"now": 100.0}
    monkeypatch.setattr(deployment._time, "monotonic", lambda: clock["now"])
    lease = deployment.issue_offline_controller_lease("owner-a", ttl_seconds=5)
    assert deployment.consume_offline_controller_lease(lease, "owner-b") is False
    assert deployment.consume_offline_controller_lease(lease, "owner-a") is True
    assert deployment.consume_offline_controller_lease(lease, "owner-a") is False

    expired = deployment.issue_offline_controller_lease("owner-a", ttl_seconds=5)
    clock["now"] = 106.0
    assert deployment.consume_offline_controller_lease(expired, "owner-a") is False
    clock["now"] = 100.0
    assert deployment.consume_offline_controller_lease(expired, "owner-a") is False
    forged = object.__new__(deployment.OfflineControllerLease)
    assert deployment.consume_offline_controller_lease(forged, "owner-a") is False


def test_offline_controller_lease_concurrent_consume_has_one_winner(monkeypatch):
    from podcast_ingest_core import hermes_runtime_deployment as deployment

    monkeypatch.setattr(deployment._time, "monotonic", lambda: 100.0)
    lease = deployment.issue_offline_controller_lease("owner-a", ttl_seconds=5)
    barrier = threading.Barrier(3)
    results = []

    def consume():
        barrier.wait()
        results.append(deployment.consume_offline_controller_lease(lease, "owner-a"))

    workers = [threading.Thread(target=consume) for _ in range(2)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join()
    assert results.count(True) == 1
    assert results.count(False) == 1


def test_snapshot_and_lowlevel_adapter_are_exact_read_only_and_never_dispatch():
    import asyncio

    from podcast_ingest_core import mcp_server

    snapshot_path = ROOT / "deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    registry_tools = asyncio.run(mcp_server.mcp.list_tools())
    descriptors = [tool.model_dump(mode="json", exclude_none=True) for tool in registry_tools]
    assert snapshot == {
        "schema_version": "spec029-mcp-tool-descriptor-snapshot-v1",
        "tools": descriptors,
    }
    assert len(snapshot["tools"]) == 22
    # Spec027 static-source extraction remains the sole offline registry oracle.
    from podcast_ingest_core.hermes_skill_protocol import (
        canonical_registry_tool_names_from_source,
    )
    assert {item["name"] for item in snapshot["tools"]} == canonical_registry_tool_names_from_source()

    adapter_path = ROOT / "deploy/hermes/spec029/spec029_mcp_deny_adapter.py"
    spec = importlib.util.spec_from_file_location("spec029_mcp_deny_adapter", adapter_path)
    assert spec and spec.loader
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    assert [tool.name for tool in asyncio.run(adapter.list_tools())] == [
        item["name"] for item in descriptors
    ]
    denied = asyncio.run(adapter.deny_tool_call("raw-source-sentinel", {}))
    assert denied.isError is True
    assert adapter.tripwire_count() == 1
    source = adapter_path.read_text(encoding="utf-8")
    for forbidden in ("mcp_server", "mcp_tools_", "client", "endpoint", "proxy", "forward"):
        assert forbidden not in source
