"""Focused public seams for Spec032's sealed offline executor."""
from __future__ import annotations


def _passing_driver():
    from podcast_ingest_core import hermes_g2_activation_executor as executor
    from podcast_ingest_core import hermes_g2_docker_commands as commands
    from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES
    candidate=commands.issue_bounded_metadata_candidate(True,REQUIRED_TMPFS_ROLES,0,0,0,True,True,True,True,True,True,0,0,0)
    return executor.issue_offline_synthetic_driver(candidate,True,True)


def _attempt():
    from podcast_ingest_core import hermes_g2_attempt_ledger as ledger
    from podcast_ingest_core.hermes_g2_activation_authority import Spec032Scope
    return ledger.create_offline_temporary_ledger(Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)


def test_executor_blocks_before_lease_ledger_driver_then_runs_once_and_rolls_back():
    from podcast_ingest_core import hermes_g2_activation_authority as authority
    from podcast_ingest_core import hermes_g2_activation_executor as executor
    blocked=executor.execute_spec032_offline_attempt(object(),object(),object(),object())
    assert blocked.status is executor.Spec032ExecutorStatus.BLOCKED_INVALID_AUTHORITY
    approval=authority.issue_offline_executor_approval();lease=authority.issue_spec032_attempt_lease(approval,authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    result=executor.execute_spec032_offline_attempt(approval,lease,_attempt(),_passing_driver())
    assert result.status is executor.Spec032ExecutorStatus.PASS_OFFLINE_EXECUTOR_CONTRACT
    assert (result.attempt_count,result.retry_count,result.driver_call_count,result.runtime_status,result.ledger_terminalized,result.rollback_status.value)==(1,0,3,"offline_synthetic_driver",True,"PASS")
    receipt=executor.build_spec032_safe_receipt(result)
    assert receipt["status"]=="PASS_OFFLINE_EXECUTOR_CONTRACT" and receipt["live_actions_authorized"] is False
    assert not hasattr(executor, "issue_driver_observation")


def test_executor_rejects_duck_driver_before_lease_and_uses_sealed_metadata_driver():
    from podcast_ingest_core import hermes_g2_activation_authority as authority
    from podcast_ingest_core import hermes_g2_activation_executor as executor
    from podcast_ingest_core import hermes_g2_docker_commands as commands
    from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES
    approval=authority.issue_offline_executor_approval();lease=authority.issue_spec032_attempt_lease(approval,authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    blocked=executor.execute_spec032_offline_attempt(approval,lease,_attempt(),object())
    assert blocked.status is executor.Spec032ExecutorStatus.BLOCKED_INVALID_DRIVER
    assert authority.consume_spec032_attempt_lease(
        lease, approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION
    ) is False
    candidate=commands.issue_bounded_metadata_candidate(True,REQUIRED_TMPFS_ROLES,0,0,0,True,True,True,True,True,True,0,0,0)
    driver=executor.issue_offline_synthetic_driver(candidate,True,True);lease=authority.issue_spec032_attempt_lease(approval,authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    result=executor.execute_spec032_offline_attempt(approval,lease,_attempt(),driver)
    assert result.status is executor.Spec032ExecutorStatus.PASS_OFFLINE_EXECUTOR_CONTRACT
    assert result.runtime_status=="offline_synthetic_driver" and result.ledger_terminalized is True


def test_base_exception_still_rolls_back_and_terminalizes_with_rollback_precedence(monkeypatch):
    from podcast_ingest_core import hermes_g2_activation_authority as authority
    from podcast_ingest_core import hermes_g2_activation_executor as executor

    class HarnessInterrupt(BaseException):
        pass

    approval = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    driver = _passing_driver()
    calls = []
    def rollback_once(_self, _command):
        calls.append("rollback")
        raise HarnessInterrupt()
    monkeypatch.setattr(executor.OfflineSyntheticDriver, "rollback", rollback_once)
    result = executor.execute_spec032_offline_attempt(approval, lease, _attempt(), driver)
    assert result.status is executor.Spec032ExecutorStatus.FAILED_ROLLBACK_QUARANTINED
    assert result.rollback_status is executor.Spec032RollbackStatus.QUARANTINED
    assert result.ledger_terminalized is True and calls == ["rollback"]


def test_terminalization_base_exception_is_normalized_after_one_attempt(monkeypatch):
    from podcast_ingest_core import hermes_g2_activation_authority as authority
    from podcast_ingest_core import hermes_g2_activation_executor as executor
    from podcast_ingest_core import hermes_g2_attempt_ledger as ledger

    class HarnessInterrupt(BaseException):
        pass

    approval = authority.issue_offline_executor_approval()
    lease = authority.issue_spec032_attempt_lease(approval, authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    monkeypatch.setattr(ledger, "terminalize_attempt", lambda *_args: (_ for _ in ()).throw(HarnessInterrupt()))
    result = executor.execute_spec032_offline_attempt(approval, lease, _attempt(), _passing_driver())
    assert result.status is executor.Spec032ExecutorStatus.FAILED_LEDGER_TERMINALIZATION_QUARANTINED
    assert result.rollback_status is executor.Spec032RollbackStatus.PASS
    assert result.ledger_terminalized is False
