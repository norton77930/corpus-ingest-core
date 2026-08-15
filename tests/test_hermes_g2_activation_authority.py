"""Focused public-seam tests for Spec032 sealed offline authority."""
from __future__ import annotations


def test_production_source_gate_blocks_before_lease_ledger_or_driver_and_offline_lease_is_single_use():
    from podcast_ingest_core import hermes_g2_activation_authority as authority

    gate = authority.evaluate_spec032_production_gate()
    assert gate.status is authority.Spec032GateStatus.BLOCKED_CREDENTIAL_SEAM
    assert (gate.lease_issue_count, gate.ledger_claim_count, gate.driver_call_count) == (0, 0, 0)
    assert gate.runtime_status == "not_run"

    approval = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    assert authority.consume_spec032_attempt_lease(lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION) is True
    assert authority.consume_spec032_attempt_lease(lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION) is False
    assert authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.LIVE_H4_ONE_RUN) is None


def test_trusted_clock_rollback_fails_closed_before_consuming_the_lease(monkeypatch):
    from podcast_ingest_core import hermes_g2_activation_authority as authority

    ticks = iter((100.0, 99.0))
    monkeypatch.setattr(authority, "_trusted_monotonic", lambda: next(ticks))
    approval = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(
        approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    )
    assert lease is not None
    assert authority.consume_spec032_attempt_lease(lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION) is False


def test_lease_is_bound_to_exact_approval_and_clock_failure_permanently_revokes(monkeypatch):
    from podcast_ingest_core import hermes_g2_activation_authority as authority

    approval = authority.issue_offline_executor_approval()
    other = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    assert authority.consume_spec032_attempt_lease(lease, other, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION) is False

    ticks = iter((100.0, 99.0, 101.0))
    monkeypatch.setattr(authority, "_trusted_monotonic", lambda: next(ticks))
    doomed = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    assert authority.consume_spec032_attempt_lease(doomed, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION) is False
    assert authority.consume_spec032_attempt_lease(doomed, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION) is False


def test_lease_exact_expiry_fails_closed_and_permanently_revokes(monkeypatch):
    from podcast_ingest_core import hermes_g2_activation_authority as authority

    ticks = iter((100.0, 130.0, 129.0, 131.0))
    calls: list[float] = []

    def fake_monotonic() -> float:
        tick = next(ticks)
        calls.append(tick)
        return tick

    monkeypatch.setattr(authority, "_trusted_monotonic", fake_monotonic)
    approval = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(
        approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    )

    assert authority.consume_spec032_attempt_lease(
        lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    ) is False
    assert authority.consume_spec032_attempt_lease(
        lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    ) is False
    assert authority.consume_spec032_attempt_lease(
        lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    ) is False
    assert calls == [100.0, 130.0]


def test_lease_revoke_and_concurrent_consume_have_exactly_one_terminal_winner():
    from concurrent.futures import ThreadPoolExecutor
    from podcast_ingest_core import hermes_g2_activation_authority as authority

    approval = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(
            lambda _unused: authority.consume_spec032_attempt_lease(
                lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
            ),
            range(2),
        ))
    assert outcomes.count(True) == 1 and outcomes.count(False) == 1

    revocable = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    assert authority.revoke_spec032_attempt_lease(
        revocable, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    ) is True
    assert authority.consume_spec032_attempt_lease(
        revocable, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    ) is False
