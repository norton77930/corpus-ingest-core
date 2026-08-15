"""Pure in-memory, single-process concurrency seams for the Spec032 ledger."""
from __future__ import annotations


def test_offline_ledger_factory_accepts_only_scope_and_creates_no_files(tmp_path):
    import inspect
    from podcast_ingest_core import hermes_g2_attempt_ledger as ledger
    from podcast_ingest_core.hermes_g2_activation_authority import Spec032Scope

    assert not hasattr(ledger, "Spec032TestStorage")
    assert not hasattr(ledger, "issue_test_storage_root")
    assert tuple(inspect.signature(ledger.create_offline_temporary_ledger).parameters) == ("scope",)
    assert ledger.create_offline_temporary_ledger(object()) is None
    attempt = ledger.create_offline_temporary_ledger(Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    assert ledger.is_factory_issued_attempt_ledger(attempt)
    assert list(tmp_path.iterdir()) == []


def test_in_memory_ledger_claim_is_absent_only_then_indeterminate_then_replays_after_terminalization():
    from podcast_ingest_core import hermes_g2_attempt_ledger as ledger
    from podcast_ingest_core.hermes_g2_activation_authority import Spec032Scope

    attempt = ledger.create_offline_temporary_ledger(Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    assert ledger.claim_attempt(attempt).status is ledger.AttemptLedgerStatus.CLAIMED
    assert ledger.claim_attempt(attempt).status is ledger.AttemptLedgerStatus.QUARANTINED_INDETERMINATE_ATTEMPT
    assert ledger.terminalize_attempt(attempt, ledger.AttemptLedgerStatus.PASS_OFFLINE_EXECUTOR_CONTRACT).status is ledger.AttemptLedgerStatus.PASS_OFFLINE_EXECUTOR_CONTRACT
    assert ledger.claim_attempt(attempt).status is ledger.AttemptLedgerStatus.BLOCKED_REPLAY


def test_parallel_claim_has_exactly_one_winner_and_terminalization_has_one_winner():
    from concurrent.futures import ThreadPoolExecutor
    from podcast_ingest_core import hermes_g2_attempt_ledger as ledger
    from podcast_ingest_core.hermes_g2_activation_authority import Spec032Scope

    attempt = ledger.create_offline_temporary_ledger(Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda _unused: ledger.claim_attempt(attempt).status, range(8)))
    assert claims.count(ledger.AttemptLedgerStatus.CLAIMED) == 1
    assert claims.count(ledger.AttemptLedgerStatus.QUARANTINED_INDETERMINATE_ATTEMPT) == 7

    requested = (
        ledger.AttemptLedgerStatus.PASS_OFFLINE_EXECUTOR_CONTRACT,
        ledger.AttemptLedgerStatus.FAILED_ACTIVATION_QUARANTINED,
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        terminal = list(pool.map(lambda status: ledger.terminalize_attempt(attempt, status).status, requested))
    assert sum(status in requested for status in terminal) == 1
    assert terminal.count(ledger.AttemptLedgerStatus.FAILED_LEDGER_TERMINALIZATION_QUARANTINED) == 1
