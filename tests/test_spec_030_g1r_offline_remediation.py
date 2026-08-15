"""Approved public seams for the static-only Spec030 G1R gate."""
from __future__ import annotations
import hashlib
import json
from dataclasses import replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def _facts(plan, *, rollback=True):
    from podcast_ingest_core.hermes_runtime_deployment import BaselineOverlayFacts, evaluate_offline_overlay_preflight
    from podcast_ingest_core.hermes_runtime_source_contract import evaluate_pinned_runtime_contract
    source = evaluate_pinned_runtime_contract()
    preflight = evaluate_offline_overlay_preflight(BaselineOverlayFacts("sha256:" + "a" * 64, True, True, True, True, True, True, True), source)
    ledger = plan.issue_g1r_owner_ledger("spec030-controller")
    return plan.ControllerPlanFacts(source, preflight, ledger, plan.issue_opaque_credential_reference(ledger, plan.ControllerStaticAdapter.HERMES_PROVIDER_BINDING), plan.REQUIRED_OPERATION_ORDER, plan.REQUIRED_TMPFS_ROLES, plan.InputMode.ONE_SHOT_STDIN, plan.LogSink.NONE, plan.CredentialBindingKind.READ_ONLY_REFERENCE, True, True, True, True, 0, 0, 0, True, True, True, plan.G1RRollbackPlanFacts(plan.G1RBaselineRollbackIntentFacts(True, True, True, True, True), True, True, True, rollback, True, True))

def test_spec029_historical_g1_receipts_are_exact_bytes():
    base = ROOT / "specs/029-hermes-blocked-tool-attempt-runtime-smoke"
    expected = {"contracts/g1-read-only-preflight-receipt.json": (512, "5017094ef7fd979d4e6ae582e8666766096b350879221e98d275717f54af1f08"), "g1-read-only-preflight.md": (2196, "cfdc918d5ce1b2e546af13ff9b17f0fc6cf8db6ece0712c419c382d118e453ce")}
    for path, (size, digest) in expected.items():
        raw = (base / path).read_bytes(); assert len(raw) == size and hashlib.sha256(raw).hexdigest() == digest

def test_approved_closed_vocabulary_and_structured_plan_contract():
    from podcast_ingest_core import hermes_runtime_controller_plan as plan
    command = plan.build_controller_command_plan(_facts(plan))
    assert tuple(plan.ControllerOperation) == (plan.ControllerOperation.CREATE_DISPOSABLE, plan.ControllerOperation.ATTACH_ONE_SHOT_INPUT, plan.ControllerOperation.WAIT_FOR_SAFE_PROJECTION, plan.ControllerOperation.DESTROY_DISPOSABLE)
    assert tuple(plan.TmpfsRole) == (plan.TmpfsRole.RAW_INPUT, plan.TmpfsRole.RAW_OUTPUT, plan.TmpfsRole.SESSION_STATE, plan.TmpfsRole.PROFILE_STATE, plan.TmpfsRole.DATABASE_STATE, plan.TmpfsRole.TEMPORARY_WORK)
    assert command.operation_order == plan.REQUIRED_OPERATION_ORDER and command.tmpfs_roles == plan.REQUIRED_TMPFS_ROLES
    assert command.input_mode is plan.InputMode.ONE_SHOT_STDIN and command.log_sink is plan.LogSink.NONE
    assert command.credential_binding_kind is plan.CredentialBindingKind.READ_ONLY_REFERENCE
    assert all(getattr(command, name) is True for name in ("read_only_rootfs", "auto_remove", "destroy_disposable_intent", "raw_argv_absent", "tty_absent", "shell_absent", "fresh_session_only"))
    assert (command.writable_durable_mount_count, command.persistent_volume_count, command.host_port_count) == (0, 0, 0)
    assert all(name not in command.__dict__ for name in ("path", "endpoint", "value", "runtime_id"))

def test_ledger_bound_opaque_reference_and_all_pass_evidence_are_sealed():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan
    facts = _facts(plan); command = plan.build_controller_command_plan(facts)
    assert command.credential_reference.ledger is command.deployment_ledger is facts.deployment_ledger
    assert plan.assess_opaque_credential_passthrough(command.credential_reference, command.deployment_ledger).binding_reference_only is True
    other = plan.issue_g1r_owner_ledger("other")
    try: plan.build_controller_command_plan(replace(facts, deployment_ledger=other))
    except ValueError: pass
    else: raise AssertionError("ledger mismatch must block")
    evidence = g1r.build_g1r_offline_remediation_evidence(g1r.evaluate_g1r_offline_remediation(command))
    assert set(evidence) == g1r.SAFE_G1R_EVIDENCE_KEYS
    assert evidence == {**evidence, "status": "PASS_OFFLINE_REMEDIATION", "predecessor_spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke", "gate": "G1R_OFFLINE_REMEDIATION", "evidence_basis": "static_command_plan_contract", "source_identity_reused": True, "historical_g1_status": "BLOCKED_CONTROL_PLANE", "offline_baseline_preflight_status": "BLOCKED_RUNTIME_SEAM", "owner_ledger_present": True, "command_plan_factory_issued": True, "input_seam_assessment": True, "no_durable_persistence_static_contract_satisfied": True, "ephemeral_storage_plan_complete": True, "log_sink_absent_static_contract_satisfied": True, "fresh_session_static_contract_satisfied": True, "opaque_credential_passthrough_assessment": True, "credential_value_read": False, "credential_value_copied": False, "credential_value_projected": False, "credential_value_logged": False, "binding_reference_only": True, "rollback_plan_complete": True, "runtime_observation_status": "not_run", "docker_runtime_observed": False, "credential_runtime_observed": False, "raw_persisted": False, "raw_persisted_scope": "safe_evidence_projection_only", "g2_authorized": False, "g3a_authorized": False, "live_actions_authorized": False}

def test_rollback_extension_and_fixed_precedence_quarantine():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan
    from podcast_ingest_core.hermes_runtime_source_contract import ContractVerdict, RuntimeContractEvaluation
    complete = plan.assess_g1r_rollback_plan(_facts(plan).rollback_plan_facts)
    assert complete.rollback_plan_complete is True and complete.quarantine_required is False
    assert "writers_may_resume" not in complete.__dict__
    quarantine_facts = _facts(plan, rollback=False)
    quarantined = plan.assess_g1r_rollback_plan(quarantine_facts.rollback_plan_facts)
    assert quarantined.quarantine_required is True
    assert "writers_may_resume" not in quarantined.__dict__
    assert g1r.evaluate_g1r_offline_remediation(plan.build_controller_command_plan(quarantine_facts)).status is g1r.G1RStatus.BLOCKED_ROLLBACK_QUARANTINED
    source_first = replace(_facts(plan), source_evaluation=RuntimeContractEvaluation(ContractVerdict.VERIFIED, True, True, True), raw_argv_absent=False)
    assert g1r.evaluate_g1r_offline_remediation(plan.build_controller_command_plan(source_first)).status is g1r.G1RStatus.BLOCKED_SOURCE_CONTRACT

def test_factory_copy_token_and_field_mutations_fail_closed_without_leak():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan
    command = plan.build_controller_command_plan(_facts(plan)); copied = object.__new__(plan.ControllerCommandPlan)
    for name, value in command.__dict__.items(): object.__setattr__(copied, name, value)
    assert plan.assess_static_controller_plan(copied).status is plan.StaticPlanStatus.INVALID_PROVENANCE
    reference = command.credential_reference; object.__setattr__(reference, "poison", "opaque-poison")
    assert plan.assess_opaque_credential_passthrough(reference, command.deployment_ledger).status is plan.CredentialPassthroughStatus.INVALID_REFERENCE
    evaluation = g1r.evaluate_g1r_offline_remediation(copied); forged = object.__new__(g1r.G1ROfflineRemediationEvaluation)
    for name, value in evaluation.__dict__.items(): object.__setattr__(forged, name, value)
    safe = g1r.build_g1r_offline_remediation_evidence(forged)
    assert safe["status"] == "BLOCKED_INVALID_PROVENANCE" and "opaque-poison" not in json.dumps(safe)

def test_closed_cli_static_guards_docs_receipt_and_later_verifier_scope():
    import subprocess, sys
    script = ROOT / "scripts/validate_hermes_g1r_offline_remediation.py"; bad = subprocess.run([sys.executable, str(script), "opaque-poison"], capture_output=True, text=True)
    assert bad.returncode == 2 and "opaque-poison" not in bad.stdout + bad.stderr
    good = subprocess.run([sys.executable, str(script), "offline-remediation-plan"], capture_output=True, text=True)
    assert good.returncode == 0 and json.loads(good.stdout)["status"] == "PASS_OFFLINE_REMEDIATION"
    for relative in ("src/podcast_ingest_core/hermes_runtime_controller_plan.py", "src/podcast_ingest_core/hermes_g1r_offline_remediation.py"):
        source = (ROOT / relative).read_text(encoding="utf-8").lower(); assert all(term not in source for term in ("import subprocess", "import socket", "import urllib", "import requests", "import docker"))
    receipt = json.loads((ROOT / "specs/030-hermes-g1r-offline-remediation/contracts/g1r-offline-remediation-receipt.json").read_text(encoding="utf-8"))
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan
    assert receipt == g1r.build_g1r_offline_remediation_evidence(
        g1r.evaluate_g1r_offline_remediation(plan.build_controller_command_plan(_facts(plan)))
    )
    verifier = (ROOT / "scripts/verify_spec_030.py").read_text(encoding="utf-8")
    assert "_changed_paths" not in verifier and "git diff --check --" in verifier and "Docker/Hermes/network/inference/C6" in verifier
    for relative in ("spec.md", "plan.md", "tasks.md", "data-model.md", "checklists/requirements.md", "contracts/g1r-offline-remediation-contract.md"):
        assert "static" in (ROOT / "specs/030-hermes-g1r-offline-remediation" / relative).read_text(encoding="utf-8").lower()


def test_task42_invalid_provenance_rollback_intents_and_private_evaluation_contract():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    baseline = plan.G1RBaselineRollbackIntentFacts(True, True, True, True, True)
    intents = plan.G1RRollbackPlanFacts(baseline, True, True, True, True, True, True)
    rollback = plan.assess_g1r_rollback_plan(intents)
    assert rollback.rollback_plan_complete is True
    assert rollback.quarantine_required is False
    assert "writers_may_resume" not in rollback.__dict__

    command = plan.build_controller_command_plan(_facts(plan))
    object.__setattr__(command, "preflight_status", "raw-task42-sentinel")
    evaluation = g1r.evaluate_g1r_offline_remediation(command)
    evidence = g1r.build_g1r_offline_remediation_evidence(evaluation)
    assert evaluation.status is g1r.G1RStatus.BLOCKED_INVALID_PROVENANCE
    assert "raw-task42-sentinel" not in repr(evaluation) + json.dumps(evidence)
    assert "evidence" not in evaluation.__dict__


def test_task42_deep_ledger_adapter_hash_and_verifier_guards():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    hashes = {
        "specs/029-hermes-blocked-tool-attempt-runtime-smoke/contracts/hermes-v0.19.0-runtime-source-manifest.json": "5342110449737d80d5d67390bb4ad4c9e26fd4983314b6c4d4e25912c214e7ee",
        "deploy/hermes/spec029/plugin/spec029_all_block.py": "b6ee543a95f8651941608fdd846f00aa27d03e9da933e8324c419e872c67e991",
        "deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json": "e7ce54129eb824e1f711277bc1fac59104dcdb597728bd6a87ba7c7f77b10b74",
        "deploy/hermes/spec029/spec029_mcp_deny_adapter.py": "4d590082de3687a6e60e1547b0c6df91b9e02f3d4aac152f03f6d99ab6debf7d",
    }
    assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in hashes.items())

    blocked_facts = _facts(plan, rollback=False)
    command = plan.build_controller_command_plan(blocked_facts)
    object.__setattr__(blocked_facts.rollback_plan_facts, "raw_ephemeral_surfaces_destroy_intent", True)
    assert g1r.evaluate_g1r_offline_remediation(command).status is g1r.G1RStatus.BLOCKED_ROLLBACK_QUARANTINED
    owner = command.deployment_ledger
    object.__setattr__(owner, "_owner", "owner-poison")
    assert plan.assess_static_controller_plan(command).status is plan.StaticPlanStatus.INVALID_PROVENANCE
    assert "owner-poison" not in repr(command) + str(command) + repr(command.credential_reference)

    assert plan.adapter_capability(object()).materializes_value is True
    try:
        plan.issue_opaque_credential_reference(plan.issue_g1r_owner_ledger("x"), object())
    except ValueError:
        pass
    else:
        raise AssertionError("unknown/materializing adapter must block")

    fresh = g1r.evaluate_g1r_offline_remediation(plan.build_controller_command_plan(_facts(plan, rollback=False)))
    object.__setattr__(fresh, "status", g1r.G1RStatus.PASS_OFFLINE_REMEDIATION)
    assert g1r.build_g1r_offline_remediation_evidence(fresh)["status"] == "BLOCKED_INVALID_PROVENANCE"
    verifier = (ROOT / "scripts/verify_spec_030.py").read_text(encoding="utf-8")
    assert "tests/test_spec_029_offline.py\",\n" in verifier
    assert "ast.parse" in verifier and "renderer" in verifier and "live transition" in verifier


def test_task42_first_ledger_seal_exact_intents_and_raw_repr_are_fail_closed():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    facts = _facts(plan)
    command = plan.build_controller_command_plan(facts)
    object.__setattr__(facts.deployment_ledger, "extra", "ledger-reseal-poison")
    try:
        plan.issue_opaque_credential_reference(
            facts.deployment_ledger, plan.ControllerStaticAdapter.HERMES_PROVIDER_BINDING
        )
    except ValueError:
        pass
    else:
        raise AssertionError("mutated ledger must not be re-sealed")
    assert plan.assess_static_controller_plan(command).status is plan.StaticPlanStatus.INVALID_PROVENANCE

    baseline = plan.G1RBaselineRollbackIntentFacts(True, True, True, True, True)
    cases = (
        object.__new__(plan.G1RBaselineRollbackIntentFacts),
        object.__new__(plan.G1RRollbackPlanFacts),
        plan.G1RBaselineRollbackIntentFacts(True, True, True, True, 1),
    )
    for case in cases:
        assert plan.assess_g1r_rollback_plan(case).rollback_plan_complete is False
    class BaselineSubclass(plan.G1RBaselineRollbackIntentFacts):
        pass
    class PlanSubclass(plan.G1RRollbackPlanFacts):
        pass
    exact_baseline = plan.G1RBaselineRollbackIntentFacts(True, True, True, True, True)
    adversarial = (
        BaselineSubclass(True, True, True, True, True),
        PlanSubclass(exact_baseline, True, True, True, True, True, True),
        plan.G1RRollbackPlanFacts(exact_baseline, True, True, True, True, True, 0),
    )
    for case in adversarial:
        assert plan.assess_g1r_rollback_plan(case).rollback_plan_complete is False
    object.__setattr__(baseline, "extra", True)
    assert plan.assess_g1r_rollback_plan(plan.G1RRollbackPlanFacts(baseline, True, True, True, True, True, True)).quarantine_required is True

    class LedgerSubclass(plan.G1ROwnerLedger):
        pass
    extra_ledger = plan.issue_g1r_owner_ledger("extra-owner")
    object.__setattr__(extra_ledger, "extra", True)
    for ledger in (object.__new__(LedgerSubclass), extra_ledger):
        try:
            plan.issue_opaque_credential_reference(ledger, plan.ControllerStaticAdapter.HERMES_PROVIDER_BINDING)
        except ValueError:
            pass
        else:
            raise AssertionError("subclass or extra-field ledger must block")
    clean_ledger = plan.issue_g1r_owner_ledger("repr-owner-sentinel")
    clean_reference = plan.issue_opaque_credential_reference(clean_ledger, plan.ControllerStaticAdapter.HERMES_PROVIDER_BINDING)
    assert "repr-owner-sentinel" not in repr(clean_ledger) + str(clean_ledger) + repr(clean_reference) + str(clean_reference)
    capability = plan.adapter_capability(object())
    assert capability.reference_only is False and capability.materializes_value is True

    evaluation = g1r.evaluate_g1r_offline_remediation(plan.build_controller_command_plan(_facts(plan, rollback=False)))
    object.__setattr__(evaluation, "status", "raw-status-sentinel")
    assert "raw-status-sentinel" not in repr(evaluation) + json.dumps(g1r.build_g1r_offline_remediation_evidence(evaluation))

    verifier = (ROOT / "scripts/verify_spec_030.py").read_text(encoding="utf-8")
    assert "any(term in node.name.lower()" in verifier


def test_task43_exact_class_guards_reject_subclass_and_class_mutation():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    try:
        plan.G1ROwnerLedger("owner-sentinel")
    except TypeError:
        pass
    else:
        raise AssertionError("owner ledger must be factory-only")
    owner_ledger = plan.issue_g1r_owner_ledger("owner-sentinel")
    assert set(owner_ledger.__dict__) == {"_factory_token"}
    assert "owner-sentinel" not in repr(owner_ledger) + str(owner_ledger)
    class OwnerLedgerSubclass(plan.G1ROwnerLedger):
        pass
    forged_ledger = object.__new__(OwnerLedgerSubclass)
    object.__setattr__(forged_ledger, "_factory_token", owner_ledger._factory_token)
    try:
        plan.issue_opaque_credential_reference(forged_ledger, plan.ControllerStaticAdapter.HERMES_PROVIDER_BINDING)
    except ValueError:
        pass
    else:
        raise AssertionError("subclass ledger must fail closed")

    command = plan.build_controller_command_plan(_facts(plan))
    static = plan.assess_static_controller_plan(command)
    credential = plan.assess_opaque_credential_passthrough(command.credential_reference, command.deployment_ledger)
    rollback = plan.assess_g1r_rollback_plan(_facts(plan).rollback_plan_facts)
    evaluation = g1r.evaluate_g1r_offline_remediation(command)
    cases = (
        (command, plan.ControllerCommandPlan, plan.assess_static_controller_plan, lambda value: value.status is plan.StaticPlanStatus.INVALID_PROVENANCE),
        (command.credential_reference, plan.OpaqueCredentialReference, lambda value: plan.assess_opaque_credential_passthrough(value, command.deployment_ledger), lambda value: value.status is plan.CredentialPassthroughStatus.INVALID_REFERENCE),
        (static, plan.StaticPlanAssessment, plan.is_factory_issued_static_plan_assessment, lambda value: value is False),
        (credential, plan.CredentialPassthroughAssessment, plan.is_factory_issued_credential_assessment, lambda value: value is False),
        (rollback, plan.G1RRollbackPlanAssessment, plan.is_factory_issued_rollback_assessment, lambda value: value is False),
        (evaluation, g1r.G1ROfflineRemediationEvaluation, g1r.build_g1r_offline_remediation_evidence, lambda value: value["status"] == "BLOCKED_INVALID_PROVENANCE"),
    )
    for original, base, assess, assertion in cases:
        subclass = type("CompatibleSubclass", (base,), {})
        forged = object.__new__(subclass)
        for name, value in original.__dict__.items():
            object.__setattr__(forged, name, value)
        assert assertion(assess(forged))
        try:
            object.__setattr__(original, "__class__", subclass)
        except TypeError:
            continue
        assert assertion(assess(original))


def test_task44_exact_class_guard_precedes_poisoned_factory_token_reads():
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    command = plan.build_controller_command_plan(_facts(plan))
    static = plan.assess_static_controller_plan(command)
    credential = plan.assess_opaque_credential_passthrough(command.credential_reference, command.deployment_ledger)
    rollback = plan.assess_g1r_rollback_plan(_facts(plan).rollback_plan_facts)

    def poison_factory_token(_value):
        raise AssertionError("factory token must not be read before exact-class rejection")

    cases = (
        (command.credential_reference, plan.OpaqueCredentialReference, plan._opaque_issued, lambda result: result is False),
        (command, plan.ControllerCommandPlan, plan._plan_issued, lambda result: result is False),
        (static, plan.StaticPlanAssessment, plan.is_factory_issued_static_plan_assessment, lambda result: result is False),
        (credential, plan.CredentialPassthroughAssessment, plan.is_factory_issued_credential_assessment, lambda result: result is False),
        (rollback, plan.G1RRollbackPlanAssessment, plan.is_factory_issued_rollback_assessment, lambda result: result is False),
    )
    for original, base, validator, assertion in cases:
        subclass = type("PoisonedFactoryTokenSubclass", (base,), {"_factory_token": property(poison_factory_token)})
        object.__setattr__(original, "__class__", subclass)
        assert assertion(validator(original))


def test_task44_plan_seal_rejects_poisoned_equality_without_leaking():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    sentinel = "task44-plan-equality-poison"

    class Poison:
        def __eq__(self, _other):
            raise AssertionError(sentinel)

    command = plan.build_controller_command_plan(_facts(plan))
    object.__setattr__(command, "source_contract_status", Poison())
    assert plan.assess_static_controller_plan(command).status is plan.StaticPlanStatus.INVALID_PROVENANCE
    evidence = g1r.build_g1r_offline_remediation_evidence(g1r.evaluate_g1r_offline_remediation(command))
    assert evidence["status"] == "BLOCKED_INVALID_PROVENANCE" and sentinel not in json.dumps(evidence)


def test_task44_adapter_capability_rejects_poisoned_hash_before_lookup():
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    sentinel = "task44-adapter-hash-poison"

    class Poison:
        def __hash__(self):
            raise AssertionError(sentinel)

    poisoned_adapter = Poison()
    capability = plan.adapter_capability(poisoned_adapter)
    assert capability.reference_only is False and capability.materializes_value is True
    ledger = plan.issue_g1r_owner_ledger("task44-adapter")
    try:
        plan.issue_opaque_credential_reference(ledger, poisoned_adapter)
    except ValueError:
        pass
    else:
        raise AssertionError("poisoned adapter must fail closed")
    reference = plan.issue_opaque_credential_reference(ledger, plan.ControllerStaticAdapter.HERMES_PROVIDER_BINDING)
    object.__setattr__(reference, "adapter", poisoned_adapter)
    assert plan.assess_opaque_credential_passthrough(reference, ledger).status is plan.CredentialPassthroughStatus.INVALID_REFERENCE


def test_task44_predecessor_evaluations_require_exact_classes_before_projection():
    from podcast_ingest_core import hermes_runtime_controller_plan as plan
    from podcast_ingest_core.hermes_runtime_deployment import PreflightEvaluation
    from podcast_ingest_core.hermes_runtime_source_contract import RuntimeContractEvaluation

    source_subclass = type("Task44SourceSubclass", (RuntimeContractEvaluation,), {})
    preflight_subclass = type("Task44PreflightSubclass", (PreflightEvaluation,), {})

    def compatible_copy(cls, value):
        copied = object.__new__(cls)
        for name, field_value in value.__dict__.items():
            object.__setattr__(copied, name, field_value)
        return copied

    facts = _facts(plan)
    for invalid_facts in (
        replace(facts, source_evaluation=compatible_copy(source_subclass, facts.source_evaluation)),
        replace(facts, preflight_evaluation=compatible_copy(preflight_subclass, facts.preflight_evaluation)),
    ):
        try:
            plan.build_controller_command_plan(invalid_facts)
        except ValueError:
            pass
        else:
            raise AssertionError("compatible predecessor subclass must fail closed")
    for field, subclass in (("source_evaluation", source_subclass), ("preflight_evaluation", preflight_subclass)):
        mutated = _facts(plan)
        object.__setattr__(getattr(mutated, field), "__class__", subclass)
        try:
            plan.build_controller_command_plan(mutated)
        except ValueError:
            pass
        else:
            raise AssertionError("mutated predecessor class must fail closed")


def test_task44_evaluation_seal_rejects_poisoned_status_equality_without_leaking():
    from podcast_ingest_core import hermes_g1r_offline_remediation as g1r
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    sentinel = "task44-evaluation-equality-poison"

    class Poison:
        def __eq__(self, _other):
            raise AssertionError(sentinel)

    evaluation = g1r.evaluate_g1r_offline_remediation(plan.build_controller_command_plan(_facts(plan)))
    object.__setattr__(evaluation, "status", Poison())
    evidence = g1r.build_g1r_offline_remediation_evidence(evaluation)
    assert evidence["status"] == "BLOCKED_INVALID_PROVENANCE" and sentinel not in json.dumps(evidence)


def test_task45_closed_fact_shapes_reject_stateful_poison_keys_without_leak():
    from podcast_ingest_core import hermes_runtime_controller_plan as plan

    sentinel = "task45-stateful-key-poison"

    class PoisonKey:
        def __init__(self, collided_field):
            self.hash_calls = 0
            self.collided_field_hash = hash(collided_field)

        def __hash__(self):
            self.hash_calls += 1
            if self.hash_calls == 1:
                return self.collided_field_hash
            raise AssertionError(sentinel)

        def __eq__(self, _other):
            raise AssertionError(sentinel)

    def contaminate(value, removed_field):
        key = PoisonKey(removed_field)
        vars(value).pop(removed_field)
        vars(value)[key] = sentinel
        assert key.hash_calls == 1
        return key

    controller_facts = _facts(plan)
    controller_key = contaminate(controller_facts, "raw_argv_absent")
    try:
        plan.build_controller_command_plan(controller_facts)
    except ValueError as error:
        assert str(error) == "closed controller plan facts required" and sentinel not in str(error)
    else:
        raise AssertionError("invalid controller fact shape must fail closed")
    assert controller_key.hash_calls == 1

    outer_rollback = _facts(plan).rollback_plan_facts
    outer_key = contaminate(outer_rollback, "fresh_session_destroy_intent")
    outer_assessment = plan.assess_g1r_rollback_plan(outer_rollback)
    assert outer_assessment.status is plan.RollbackPlanStatus.QUARANTINED and sentinel not in repr(outer_assessment)
    assert outer_key.hash_calls == 1

    nested_rollback = _facts(plan).rollback_plan_facts
    nested_key = contaminate(nested_rollback.baseline_intents, "controls_restore_intent")
    nested_assessment = plan.assess_g1r_rollback_plan(nested_rollback)
    assert nested_assessment.status is plan.RollbackPlanStatus.QUARANTINED and sentinel not in repr(nested_assessment)
    assert nested_key.hash_calls == 1
