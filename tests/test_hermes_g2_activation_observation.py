"""Public closed observation and safe-receipt seams for Spec031."""
from __future__ import annotations
import json

def test_credential_and_approval_gates_are_factory_sealed_and_not_ready():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    feasibility=obs.evaluate_credentialless_feasibility(); approval=obs.evaluate_g2_approval_gates("SPEC031_G2_CREDENTIALLESS_ACTIVATION_ACK")
    assert feasibility.status is obs.CredentialFeasibilityStatus.BLOCKED_CREDENTIAL_SEAM
    assert feasibility.official_loader_verified is False and feasibility.provider_construction_absent is False
    assert approval.status is obs.G2ApprovalStatus.BLOCKED_REVIEW_GATE
    assert (approval.reviews_passed,approval.human_approval_verified,approval.reviewed_revision_verified,approval.fixture_identity_verified,approval.baseline_selector_verified)==(False,False,False,False,False)
    assert obs.is_factory_issued_credential_feasibility(feasibility) and obs.is_factory_issued_g2_approval(approval)

def test_live_start_unknown_and_rollback_quarantine_take_terminal_precedence():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    feasibility=obs.evaluate_credentialless_feasibility(); eligibility=obs.evaluate_g2_eligibility(feasibility)
    runtime=obs.observe_g2_runtime(obs.G2RuntimeSignal.UNKNOWN,live_start_observed=True)
    complete=obs.evaluate_g2_owned_rollback(obs.issue_g2_owned_rollback_facts(True,True,True,True,True,True,True,False))
    assert obs.evaluate_g2_activation(feasibility,eligibility,runtime,complete).status is obs.G2ActivationStatus.FAILED_ACTIVATION_QUARANTINED
    failed=obs.evaluate_g2_owned_rollback(obs.issue_g2_owned_rollback_facts(False,False,False,False,False,False,False,True))
    assert obs.evaluate_g2_activation(feasibility,eligibility,runtime,failed).status is obs.G2ActivationStatus.FAILED_ROLLBACK_QUARANTINED
    assert failed.writers_may_resume is False and failed.quarantine_required is True

def test_forgery_copy_subclass_mutation_and_poison_values_project_only_safe_receipt():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    value=obs.evaluate_credentialless_feasibility(); copied=object.__new__(obs.CredentialFeasibilityEvaluation)
    for key,item in value.__dict__.items():object.__setattr__(copied,key,item)
    assert obs.is_factory_issued_credential_feasibility(copied) is False
    subclass=type("Sub",(obs.CredentialFeasibilityEvaluation,),{}); forged=object.__new__(subclass)
    assert obs.is_factory_issued_credential_feasibility(forged) is False
    class Poison:
        def __eq__(self,other):raise AssertionError("poison-equality")
        def __hash__(self):raise AssertionError("poison-hash")
    object.__setattr__(value,"status",Poison())
    assert obs.is_factory_issued_credential_feasibility(value) is False
    receipt=obs.build_g2_safe_receipt(object())
    assert set(receipt)==obs.SAFE_G2_RECEIPT_KEYS and "poison" not in json.dumps(receipt)


def test_blocked_and_quarantined_receipts_do_not_overclaim_runtime_or_rollback():
    from podcast_ingest_core import hermes_g2_activation_observation as obs

    feasibility = obs.evaluate_credentialless_feasibility()
    eligibility = obs.evaluate_g2_eligibility(feasibility)
    blocked = obs.evaluate_g2_activation(
        feasibility,
        eligibility,
        obs.observe_g2_runtime(obs.G2RuntimeSignal.NOT_RUN, live_start_observed=False),
        obs.not_required_g2_owned_rollback(),
    )
    blocked_receipt = obs.build_g2_safe_receipt(blocked)
    assert blocked_receipt["runtime_status"] == "not_run"
    assert blocked_receipt["runtime_status_not_run"] is True
    assert blocked_receipt["runtime_counts_observed"] is False
    assert blocked_receipt["g2_rollback_status"] == "NOT_REQUIRED"
    assert blocked_receipt["rollback_required"] is False
    assert blocked_receipt["rollback_quarantined"] is False
    assert blocked_receipt["writers_may_resume"] is False

    quarantined = obs.evaluate_g2_activation(
        feasibility,
        eligibility,
        obs.observe_g2_runtime(obs.G2RuntimeSignal.UNKNOWN, live_start_observed=True),
        obs.evaluate_g2_owned_rollback(
            obs.issue_g2_owned_rollback_facts(
                False, False, False, False, False, False, False, True
            )
        ),
    )
    quarantined_receipt = obs.build_g2_safe_receipt(quarantined)
    assert quarantined_receipt["runtime_status"] == "quarantined"
    assert quarantined_receipt["runtime_status_not_run"] is False
    assert quarantined_receipt["runtime_counts_observed"] is False
    assert quarantined_receipt["rollback_required"] is True
    assert quarantined_receipt["rollback_quarantined"] is True
    assert quarantined_receipt["writers_may_resume"] is False


def test_incompatible_runtime_control_and_rollback_evidence_fails_closed():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES

    feasibility = obs.evaluate_credentialless_feasibility()
    eligibility = obs.evaluate_g2_eligibility(feasibility)
    started = obs.evaluate_g2_activation(
        feasibility,
        eligibility,
        obs.observe_g2_runtime(obs.G2RuntimeSignal.UNKNOWN, live_start_observed=True),
        obs.not_required_g2_owned_rollback(),
    )
    started_receipt = obs.build_g2_safe_receipt(started)
    assert started.status is obs.G2ActivationStatus.FAILED_ROLLBACK_QUARANTINED
    assert started_receipt["g2_rollback_status"] == "QUARANTINED"
    assert started_receipt["rollback_required"] is True
    assert started_receipt["rollback_quarantined"] is True

    controls = obs.issue_g2_runtime_control_facts(
        True, REQUIRED_TMPFS_ROLES, 0, 0, 0, True, 0,
        True, True, True, True, True, True, 0, 0, 0, 0, 0, True,
    )
    not_run = obs.evaluate_g2_activation(
        feasibility,
        eligibility,
        obs.observe_g2_runtime(obs.G2RuntimeSignal.NOT_RUN, live_start_observed=False),
        obs.not_required_g2_owned_rollback(),
        controls=controls,
    )
    not_run_receipt = obs.build_g2_safe_receipt(not_run)
    assert not_run.runtime_control_status is obs.G2RuntimeControlStatus.NOT_RUN
    assert not_run_receipt["runtime_counts_observed"] is False

    unknown_before_start = obs.evaluate_g2_activation(
        feasibility,
        eligibility,
        obs.observe_g2_runtime(obs.G2RuntimeSignal.UNKNOWN, live_start_observed=False),
        obs.not_required_g2_owned_rollback(),
    )
    unknown_receipt = obs.build_g2_safe_receipt(unknown_before_start)
    assert unknown_receipt["rollback_required"] is False
    assert unknown_receipt["g2_rollback_status"] == "NOT_REQUIRED"


def test_bare_rollback_signal_cannot_claim_completed_cleanup():
    from podcast_ingest_core import hermes_g2_activation_observation as obs

    evaluation = obs.evaluate_g2_owned_rollback(obs.G2RollbackSignal.COMPLETE)
    assert evaluation.status is obs.G2RollbackStatus.QUARANTINED
    assert evaluation.g2_owned_rollback_completed is False
    assert evaluation.writers_may_resume is False
    assert evaluation.quarantine_required is True


def test_untrusted_pinned_source_shape_cannot_claim_source_contract_verified():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    from podcast_ingest_core.hermes_runtime_source_contract import (
        ContractVerdict,
        RuntimeContractEvaluation,
    )

    mismatched = RuntimeContractEvaluation(ContractVerdict.VERIFIED, True, True, True)
    exact_values = RuntimeContractEvaluation(
        ContractVerdict.BLOCKED_RUNTIME_SEAM,
        True,
        False,
        False,
    )
    for forged in (mismatched, exact_values):
        evaluation = obs.evaluate_credentialless_feasibility(forged)
        assert evaluation.source_contract_verified is False
        assert evaluation.status is obs.CredentialFeasibilityStatus.BLOCKED_CREDENTIAL_SEAM
