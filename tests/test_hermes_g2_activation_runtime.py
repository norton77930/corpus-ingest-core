"""Public closed-plan and zero-side-effect seams for Spec031 G2."""
from __future__ import annotations


def test_blocked_review_gate_precedes_marker_lease_and_driver_calls(monkeypatch):
    from podcast_ingest_core import hermes_g2_activation_runtime as runtime

    class FakeDriver:
        def __init__(self): self.operations = []
        def apply_g2_command(self, command): self.operations.append(command.operation)

    def marker_must_not_run():
        raise AssertionError("blocked gates must not claim a marker")

    monkeypatch.setattr(runtime, "_claim_persistent_attempt_marker", marker_must_not_run)
    result = runtime.run_g2_activation_once(runtime.EXACT_G2_ACTIVATION_ACK, FakeDriver())
    assert result.status is runtime.G2AttemptStatus.BLOCKED_REVIEW_GATE
    assert (result.attempt_count, result.retry_count, result.runtime_status) == (0, 0, "not_run")
    assert result.driver_call_count == 0


def test_closed_runtime_controls_and_rollback_facts_fail_closed_and_quarantine_precedes_credential():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES

    controls = obs.issue_g2_runtime_control_facts(
        True, REQUIRED_TMPFS_ROLES, 0, 0, 0, True, 0,
        True, True, True, True, True, True, 0, 0, 0, 0, 0, True,
    )
    assessed = obs.assess_g2_runtime_controls(controls)
    assert assessed.status is obs.G2RuntimeControlStatus.PASS
    object.__setattr__(controls, "host_port_count", 1)
    assert obs.assess_g2_runtime_controls(controls).status is obs.G2RuntimeControlStatus.QUARANTINED

    complete = obs.issue_g2_owned_rollback_facts(True, True, True, True, True, True, True, False)
    rollback = obs.evaluate_g2_owned_rollback(complete)
    assert rollback.status is obs.G2RollbackStatus.COMPLETE and rollback.writers_may_resume is True
    incomplete = obs.issue_g2_owned_rollback_facts(False, False, False, False, False, False, False, True)
    assert obs.evaluate_g2_owned_rollback(incomplete).writers_may_resume is False

    feasibility = obs.evaluate_credentialless_feasibility()
    eligibility = obs.evaluate_g2_eligibility(feasibility)
    started_unknown = obs.observe_g2_runtime(obs.G2RuntimeSignal.UNKNOWN, live_start_observed=True)
    evaluation = obs.evaluate_g2_activation(feasibility, eligibility, started_unknown, rollback)
    assert evaluation.status is obs.G2ActivationStatus.FAILED_ACTIVATION_QUARANTINED


def test_safe_receipt_is_exact_and_runner_never_accepts_ack_as_authorization():
    from podcast_ingest_core import hermes_g2_activation_observation as obs
    from podcast_ingest_core import hermes_g2_activation_runtime as runtime

    approval = obs.evaluate_g2_approval_gates(runtime.EXACT_G2_ACTIVATION_ACK)
    assert approval.status is obs.G2ApprovalStatus.BLOCKED_REVIEW_GATE
    assert approval.exact_acknowledgement is True and approval.reviews_passed is False
    receipt = obs.build_g2_safe_receipt(
        obs.evaluate_g2_activation(
            obs.evaluate_credentialless_feasibility(),
            obs.evaluate_g2_eligibility(obs.evaluate_credentialless_feasibility()),
            obs.observe_g2_runtime(obs.G2RuntimeSignal.NOT_RUN, live_start_observed=False),
            obs.not_required_g2_owned_rollback(),
            approval,
        )
    )
    assert set(receipt) == obs.SAFE_G2_RECEIPT_KEYS
    assert receipt["attempt_count"] == receipt["retry_count"] == receipt["driver_call_count"] == 0
    assert receipt["fixture_build_authorized"] is False
    assert receipt["official_loader_verified"] is False
    assert receipt["provider_materialization_status"] == "blocked_unknown"
    assert receipt["g2_rollback_status"] == "NOT_REQUIRED"
    assert all(term not in receipt for term in ("error", "path", "endpoint", "env", "argv", "session", "prompt", "tool", "timestamp", "host"))


def test_runtime_plan_seal_rejects_poisoned_equality_without_calling_it():
    from podcast_ingest_core import hermes_g2_activation_runtime as runtime

    class Poison:
        def __eq__(self, _other):
            raise AssertionError("runtime-seal-poison")

    plan = runtime.build_g2_activation_plan()
    object.__setattr__(plan, "read_only_rootfs", Poison())
    assert runtime.is_factory_issued_g2_activation_plan(plan) is False
