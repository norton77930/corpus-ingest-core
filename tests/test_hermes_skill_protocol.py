"""Assurance-only contracts for the four Hermes-managed portable Skills."""

from __future__ import annotations


def test_intent_oracle_routes_only_closed_intents_and_fails_closed():
    from podcast_ingest_core.hermes_skill_protocol import (
        Intent,
        RouteDisposition,
        Skill,
        expected_skill_for_intent,
    )

    assert expected_skill_for_intent(Intent.ONE_STEP_ADVANCE).skill is Skill.COMPLETION
    assert expected_skill_for_intent(Intent.LATEST_DETERMINISTIC).skill is Skill.LATEST_DETERMINISTIC
    assert expected_skill_for_intent(Intent.LATEST_VERIFIED_REPORT).skill is Skill.LATEST_VERIFIED_REPORT
    assert expected_skill_for_intent(Intent.NAMED_VERIFIED_REPORT).skill is Skill.NAMED_VERIFIED_REPORT
    assert expected_skill_for_intent(Intent.READ_ONLY).disposition is RouteDisposition.NO_SIDE_EFFECT_SKILL

    rejected = expected_skill_for_intent("process the latest episode")
    assert rejected.disposition is RouteDisposition.CLARIFICATION_REQUIRED
    assert rejected.skill is None
    assert "process the latest episode" not in repr(rejected)


def test_skill_artifacts_require_the_exact_allowlist_tools_and_ordered_clauses():
    from pathlib import Path

    from podcast_ingest_core.hermes_skill_protocol import (
        FailureCode,
        Skill,
        SkillArtifact,
        Tool,
        validate_skill_artifacts,
    )

    root = Path(__file__).resolve().parents[1]
    artifacts = (
        SkillArtifact(
            Skill.COMPLETION,
            (root / ".agents/skills/corpus-episode-completion/SKILL.md").read_text(encoding="utf-8"),
        ),
        SkillArtifact(
            Skill.LATEST_DETERMINISTIC,
            (root / ".agents/skills/corpus-latest-episode-processing/SKILL.md").read_text(encoding="utf-8"),
        ),
        SkillArtifact(
            Skill.LATEST_VERIFIED_REPORT,
            (root / ".agents/skills/latest-episode-verified-research-report/SKILL.md").read_text(encoding="utf-8"),
        ),
        SkillArtifact(
            Skill.NAMED_VERIFIED_REPORT,
            (root / ".agents/skills/episode-verified-research-report/SKILL.md").read_text(encoding="utf-8"),
        ),
    )

    validation = validate_skill_artifacts(artifacts)

    assert validation.ok is True
    assert validation.failure is FailureCode.NONE
    assert [(binding.skill, binding.tool) for binding in validation.bindings] == [
        (Skill.COMPLETION, Tool.COMPLETION),
        (Skill.LATEST_DETERMINISTIC, Tool.LATEST_DETERMINISTIC),
        (Skill.LATEST_VERIFIED_REPORT, Tool.LATEST_VERIFIED_REPORT),
        (Skill.NAMED_VERIFIED_REPORT, Tool.NAMED_VERIFIED_REPORT),
    ]
    duplicate = artifacts[:-1] + artifacts[:1]
    assert validate_skill_artifacts(duplicate).failure is FailureCode.INVALID_ARTIFACT_SET


def test_event_reducers_enforce_each_skill_approval_shape_and_call_budget():
    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        CompletionAction,
        EventKind,
        FailureCode,
        PreviewOutcome,
        ProtocolEvent,
        Skill,
        Tool,
        verify_event_sequence,
    )

    sequences = {
        Skill.COMPLETION: (
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
        Skill.LATEST_DETERMINISTIC: (
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.LATEST_DETERMINISTIC, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
        Skill.LATEST_VERIFIED_REPORT: (
            ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, False),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXACT_REFERENCE_AND_ACK),
            ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
        Skill.NAMED_VERIFIED_REPORT: (
            ProtocolEvent(
                EventKind.CALL,
                Tool.NAMED_VERIFIED_REPORT,
                False,
                preview_outcome=PreviewOutcome.READY,
            ),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXACT_REFERENCE),
            ProtocolEvent(EventKind.CALL, Tool.NAMED_VERIFIED_REPORT, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
    }

    expected_calls = {
        Skill.COMPLETION: 2,
        Skill.LATEST_DETERMINISTIC: 1,
        Skill.LATEST_VERIFIED_REPORT: 2,
        Skill.NAMED_VERIFIED_REPORT: 2,
    }
    for skill, events in sequences.items():
        verification = verify_event_sequence(skill, events)
        assert verification.ok is True
        assert verification.failure is FailureCode.NONE
        assert verification.observed_call_count == expected_calls[skill]
        assert verification.call_budget == expected_calls[skill]

    non_boolean_confirm = sequences[Skill.COMPLETION][:2] + (
        ProtocolEvent(EventKind.CALL, Tool.COMPLETION, 1, Approval.NONE, CompletionAction.DETERMINISTIC),
        ProtocolEvent(EventKind.REPORT),
        ProtocolEvent(EventKind.STOP),
    )
    assert verify_event_sequence(Skill.COMPLETION, non_boolean_confirm).failure is FailureCode.INVALID_CONFIRM
    assert verify_event_sequence(
        Skill.LATEST_DETERMINISTIC,
        sequences[Skill.LATEST_DETERMINISTIC] + (ProtocolEvent(EventKind.CALL, Tool.LATEST_DETERMINISTIC, True),),
    ).failure is FailureCode.CALL_BUDGET_EXCEEDED


def test_contract_evidence_uses_only_bounded_fields_and_never_echoes_artifact_text():
    import json

    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        ArtifactValidation,
        CompletionAction,
        EventKind,
        FailureCode,
        ProtocolEvent,
        Skill,
        Tool,
        build_contract_evidence,
        canonical_skill_bindings,
        expected_skill_for_intent,
        Intent,
        verify_event_sequence,
    )

    route = expected_skill_for_intent(Intent.ONE_STEP_ADVANCE)
    artifacts = ArtifactValidation(
        True,
        FailureCode.NONE,
        canonical_skill_bindings(),
        True,
    )
    sequence = verify_event_sequence(
        Skill.COMPLETION,
        (
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
    )

    payload = build_contract_evidence(route, artifacts, sequence).to_dict()

    assert payload == {
        "schema_version": "hermes-skill-protocol-evidence-v1",
        "ok": True,
        "route": "route",
        "skill": "corpus-episode-completion",
        "artifact_ok": True,
        "managed_allowlist_ok": True,
        "sequence_ok": True,
        "failure_code": "none",
        "call_count": 2,
        "hermes_runtime_observation": "not_evaluated",
    }
    assert "private prompt or raw event" not in json.dumps(payload)


def test_contract_evidence_rejects_forged_success_counts_for_every_skill():
    from podcast_ingest_core.hermes_skill_protocol import (
        ArtifactValidation,
        FailureCode,
        RouteDisposition,
        SequenceVerification,
        Skill,
        SkillRoute,
        build_contract_evidence,
        canonical_skill_bindings,
    )

    artifacts = ArtifactValidation(
        True,
        FailureCode.NONE,
        canonical_skill_bindings(),
        True,
    )
    expected_success_counts = {
        Skill.COMPLETION: frozenset({2}),
        Skill.LATEST_DETERMINISTIC: frozenset({1}),
        Skill.LATEST_VERIFIED_REPORT: frozenset({2}),
        Skill.NAMED_VERIFIED_REPORT: frozenset({1, 2}),
    }
    for skill, success_counts in expected_success_counts.items():
        call_budget = max(success_counts)
        route = SkillRoute(RouteDisposition.ROUTE, skill)
        forged = SequenceVerification(
            skill,
            True,
            FailureCode.NONE,
            call_budget + 1,
            call_budget,
        )
        forged_payload = build_contract_evidence(route, artifacts, forged).to_dict()
        assert forged_payload["ok"] is False
        assert forged_payload["failure_code"] == "invalid_evidence"

        for observed_call_count in range(call_budget + 1):
            payload = build_contract_evidence(
                route,
                artifacts,
                SequenceVerification(
                    skill,
                    True,
                    FailureCode.NONE,
                    observed_call_count,
                    call_budget,
                ),
            ).to_dict()
            assert payload["ok"] is (observed_call_count in success_counts)


def test_protocol_cli_accepts_only_fixed_modes_and_emits_a_fixed_safe_schema(capsys):
    import json

    from scripts import validate_hermes_skill_protocol as cli

    assert cli.main(["contracts"]) == 0
    contracts = json.loads(capsys.readouterr().out)
    assert contracts["schema_version"] == "hermes-skill-protocol-cli-v1"
    assert contracts["ok"] is True
    assert contracts["mode"] == "contracts"
    assert contracts["failure_code"] == "none"
    assert contracts["managed_allowlist_ok"] is True
    assert contracts["hermes_runtime_observation"] == "not_evaluated"
    assert len(contracts["evidence"]) == 4
    assert all(item["schema_version"] == "hermes-skill-protocol-evidence-v1" for item in contracts["evidence"])
    assert all(item["hermes_runtime_observation"] == "not_evaluated" for item in contracts["evidence"])

    assert cli.main(["synthetic"]) == 0
    synthetic = json.loads(capsys.readouterr().out)
    assert synthetic["ok"] is True
    assert synthetic["mode"] == "synthetic"
    assert synthetic["synthetic_protocols_pass"] is True
    assert synthetic["unknown_event_fail_closed"] is True
    assert synthetic["non_boolean_fail_closed"] is True
    assert synthetic["hermes_runtime_observation"] == "not_evaluated"

    forbidden = "--endpoint=private-prompt-or-session"
    assert cli.main(["contracts", forbidden]) == 2
    rejected = json.loads(capsys.readouterr().out)
    assert rejected == {
        "schema_version": "hermes-skill-protocol-cli-v1",
        "ok": False,
        "mode": "rejected",
        "failure_code": "invalid_mode",
        "managed_allowlist_ok": False,
        "hermes_runtime_observation": "not_evaluated",
        "evidence": [],
    }
    assert forbidden not in json.dumps(rejected)


def test_contracts_cli_reports_managed_allowlist_drift_without_echoing_it(monkeypatch, capsys):
    import json

    from scripts import validate_hermes_skill_protocol as cli

    monkeypatch.setattr(cli.hermes_integration, "MANAGED_SKILLS", ("unexpected-managed-skill",))

    assert cli.main(["contracts"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["managed_allowlist_ok"] is False
    assert payload["hermes_runtime_observation"] == "not_evaluated"
    assert "unexpected-managed-skill" not in json.dumps(payload)


def test_malformed_public_models_fail_closed_without_returning_caller_values():
    from podcast_ingest_core.hermes_skill_protocol import (
        ArtifactValidation,
        FailureCode,
        SequenceVerification,
        Skill,
        SkillRoute,
        build_contract_evidence,
    )

    evidence = build_contract_evidence(
        SkillRoute("caller-supplied-raw-value"),
        ArtifactValidation(True, FailureCode.NONE, ()),
        SequenceVerification(Skill.COMPLETION, True, FailureCode.NONE, 99, 2),
    ).to_dict()

    assert evidence == {
        "schema_version": "hermes-skill-protocol-evidence-v1",
        "ok": False,
        "route": "clarification_required",
        "skill": None,
        "artifact_ok": False,
        "managed_allowlist_ok": False,
        "sequence_ok": False,
        "failure_code": "invalid_evidence",
        "call_count": 0,
        "hermes_runtime_observation": "not_evaluated",
    }
    assert "caller-supplied-raw-value" not in repr(evidence)


def test_artifacts_bind_the_actual_managed_allowlist_and_fail_closed_on_malformed_sources(monkeypatch):
    from pathlib import Path

    from podcast_ingest_core import hermes_integration
    from podcast_ingest_core.hermes_skill_protocol import (
        FailureCode,
        Skill,
        SkillArtifact,
        Tool,
        validate_skill_artifacts,
    )

    root = Path(__file__).resolve().parents[1]
    artifacts = tuple(
        SkillArtifact(skill, (root / ".agents" / "skills" / skill.value / "SKILL.md").read_text(encoding="utf-8"))
        for skill in Skill
    )
    validation = validate_skill_artifacts(artifacts)

    assert hermes_integration.MANAGED_SKILLS == (
        "corpus-episode-completion",
        "corpus-latest-episode-processing",
        "latest-episode-verified-research-report",
        "episode-verified-research-report",
    )
    assert validation.ok is True
    assert validation.managed_allowlist_ok is True
    assert [(binding.skill, binding.tool) for binding in validation.bindings] == [
        (Skill.COMPLETION, Tool.COMPLETION),
        (Skill.LATEST_DETERMINISTIC, Tool.LATEST_DETERMINISTIC),
        (Skill.LATEST_VERIFIED_REPORT, Tool.LATEST_VERIFIED_REPORT),
        (Skill.NAMED_VERIFIED_REPORT, Tool.NAMED_VERIFIED_REPORT),
    ]

    with monkeypatch.context() as patched:
        patched.setattr(hermes_integration, "MANAGED_SKILLS", ("corpus-episode-completion",))
        drifted = validate_skill_artifacts(artifacts)
        assert drifted.ok is False
        assert drifted.managed_allowlist_ok is False
        assert drifted.failure is FailureCode.INVALID_MANAGED_ALLOWLIST

    malformed = validate_skill_artifacts(
        tuple(SkillArtifact(skill, object()) for skill in Skill)
    )
    assert malformed.failure is FailureCode.MALFORMED_ARTIFACT
    assert malformed.managed_allowlist_ok is True

    bad_frontmatter = (SkillArtifact(Skill.COMPLETION, artifacts[0].text.removeprefix("---\n")),) + artifacts[1:]
    assert validate_skill_artifacts(bad_frontmatter).failure is FailureCode.MALFORMED_ARTIFACT

    cross_mapped = (SkillArtifact(Skill.COMPLETION, artifacts[0].text.replace(Tool.COMPLETION.value, Tool.LATEST_DETERMINISTIC.value)),) + artifacts[1:]
    assert validate_skill_artifacts(cross_mapped).failure is FailureCode.WRONG_TOOL_MAPPING


def test_protocol_reducers_fail_closed_for_blocked_019_and_bounded_hostile_events():
    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        CompletionAction,
        EventKind,
        FailureCode,
        PreviewOutcome,
        ProtocolEvent,
        Skill,
        Tool,
        verify_event_sequence,
    )

    blocked_019 = (
        ProtocolEvent(
            EventKind.CALL,
            Tool.NAMED_VERIFIED_REPORT,
            False,
            preview_outcome=PreviewOutcome.BLOCKED,
        ),
        ProtocolEvent(EventKind.REPORT),
        ProtocolEvent(EventKind.STOP),
    )
    blocked_result = verify_event_sequence(Skill.NAMED_VERIFIED_REPORT, blocked_019)
    assert blocked_result.ok is True
    assert blocked_result.observed_call_count == 1
    assert blocked_result.call_budget == 2

    completion_happy = (
        ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
        ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
        ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
        ProtocolEvent(EventKind.REPORT),
        ProtocolEvent(EventKind.STOP),
    )
    latest_verified_preview = ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, False)
    hostile_sequences = (
        (Skill.COMPLETION, (ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),)),
        (Skill.LATEST_VERIFIED_REPORT, (latest_verified_preview, ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, True), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
        (Skill.LATEST_VERIFIED_REPORT, (latest_verified_preview, ProtocolEvent(EventKind.APPROVAL, approval=Approval.REJECTED), ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, True), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
        (Skill.NAMED_VERIFIED_REPORT, (ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, preview_outcome=PreviewOutcome.READY), ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT), ProtocolEvent(EventKind.CALL, Tool.NAMED_VERIFIED_REPORT, True), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
        (Skill.COMPLETION, completion_happy[:2] + (ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.NEXT), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
        (Skill.LATEST_DETERMINISTIC, (ProtocolEvent(EventKind.CALL, Tool.LATEST_DETERMINISTIC, False), ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT), ProtocolEvent(EventKind.CALL, Tool.LATEST_DETERMINISTIC, True), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
        (Skill.LATEST_VERIFIED_REPORT, (latest_verified_preview, ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT), ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, True), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
        (Skill.COMPLETION, completion_happy + (ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),)),
        (Skill.COMPLETION, completion_happy + (ProtocolEvent(EventKind.FALLBACK),)),
        (Skill.COMPLETION, completion_happy + (ProtocolEvent(EventKind.RETRY),)),
        (Skill.NAMED_VERIFIED_REPORT, blocked_019[:1] + (ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT), ProtocolEvent(EventKind.CALL, Tool.NAMED_VERIFIED_REPORT, True), ProtocolEvent(EventKind.REPORT), ProtocolEvent(EventKind.STOP))),
    )
    for skill, events in hostile_sequences:
        result = verify_event_sequence(skill, events)
        assert result.ok is False
        assert result.failure is not FailureCode.NONE


def test_contract_evidence_requires_exact_managed_bindings_and_consistent_success_state():
    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        ArtifactValidation,
        CompletionAction,
        EventKind,
        FailureCode,
        ProtocolEvent,
        Skill,
        SkillRoute,
        Tool,
        build_contract_evidence,
        canonical_skill_bindings,
        verify_event_sequence,
        RouteDisposition,
    )

    sequence = verify_event_sequence(
        Skill.COMPLETION,
        (
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
    )
    route = SkillRoute(RouteDisposition.ROUTE, Skill.COMPLETION)
    complete = ArtifactValidation(True, FailureCode.NONE, canonical_skill_bindings(), True)

    valid = build_contract_evidence(route, complete, sequence).to_dict()
    assert valid["ok"] is True
    assert valid["managed_allowlist_ok"] is True
    assert valid["hermes_runtime_observation"] == "not_evaluated"

    incomplete = ArtifactValidation(True, FailureCode.NONE, canonical_skill_bindings()[:1], True)
    inconsistent = ArtifactValidation(True, FailureCode.MISSING_REQUIRED_CLAUSE, canonical_skill_bindings(), True)
    for artifacts in (incomplete, inconsistent):
        payload = build_contract_evidence(route, artifacts, sequence).to_dict()
        assert payload["ok"] is False
        assert payload["failure_code"] == "invalid_evidence"
        assert payload["artifact_ok"] is False
        assert payload["managed_allowlist_ok"] is False


def test_contract_evidence_rejects_cross_skill_sequence_substitution_for_all_skills():
    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        ArtifactValidation,
        CompletionAction,
        EventKind,
        FailureCode,
        PreviewOutcome,
        ProtocolEvent,
        RouteDisposition,
        Skill,
        SkillRoute,
        Tool,
        build_contract_evidence,
        canonical_skill_bindings,
        verify_event_sequence,
    )

    events_by_skill = {
        Skill.COMPLETION: (
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
        Skill.LATEST_DETERMINISTIC: (
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.LATEST_DETERMINISTIC, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
        Skill.LATEST_VERIFIED_REPORT: (
            ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, False),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXACT_REFERENCE_AND_ACK),
            ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
        Skill.NAMED_VERIFIED_REPORT: (
            ProtocolEvent(EventKind.CALL, Tool.NAMED_VERIFIED_REPORT, False, preview_outcome=PreviewOutcome.READY),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXACT_REFERENCE),
            ProtocolEvent(EventKind.CALL, Tool.NAMED_VERIFIED_REPORT, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        ),
    }
    artifacts = ArtifactValidation(True, FailureCode.NONE, canonical_skill_bindings(), True)
    sequences = {
        skill: verify_event_sequence(skill, events)
        for skill, events in events_by_skill.items()
    }

    for route_skill, route_sequence in sequences.items():
        assert route_sequence.skill is route_skill
        assert build_contract_evidence(
            SkillRoute(RouteDisposition.ROUTE, route_skill), artifacts, route_sequence
        ).to_dict()["ok"] is True
        for substituted_skill, substituted_sequence in sequences.items():
            if substituted_skill is route_skill:
                continue
            payload = build_contract_evidence(
                SkillRoute(RouteDisposition.ROUTE, route_skill),
                artifacts,
                substituted_sequence,
            ).to_dict()
            assert payload["ok"] is False
            assert payload["failure_code"] == "invalid_evidence"


def test_completion_reducer_rejects_extraneous_fields_in_every_event_slot():
    from dataclasses import replace

    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        CompletionAction,
        EventKind,
        ProtocolEvent,
        Skill,
        Tool,
        verify_event_sequence,
    )

    valid = (
        ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
        ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
        ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
        ProtocolEvent(EventKind.REPORT),
        ProtocolEvent(EventKind.STOP),
    )
    hostile = (
        valid[:0] + (replace(valid[0], approval=Approval.REJECTED),) + valid[1:],
        valid[:1] + (replace(valid[1], tool=Tool.COMPLETION),) + valid[2:],
        valid[:1] + (replace(valid[1], confirm=True),) + valid[2:],
        valid[:1] + (replace(valid[1], action=CompletionAction.DETERMINISTIC),) + valid[2:],
        valid[:2] + (replace(valid[2], approval=Approval.EXPLICIT),) + valid[3:],
        valid[:3] + (replace(valid[3], tool=Tool.COMPLETION),) + valid[4:],
        valid[:3] + (replace(valid[3], confirm=True),) + valid[4:],
        valid[:3] + (replace(valid[3], action=CompletionAction.DETERMINISTIC),) + valid[4:],
        valid[:4] + (replace(valid[4], tool=Tool.COMPLETION),),
        valid[:4] + (replace(valid[4], confirm=True),),
        valid[:4] + (replace(valid[4], action=CompletionAction.DETERMINISTIC),),
    )
    for events in hostile:
        assert verify_event_sequence(Skill.COMPLETION, events).ok is False


def test_malformed_skill_identity_fails_closed_before_hash_or_frontmatter_access():
    from podcast_ingest_core.hermes_skill_protocol import (
        FailureCode,
        Skill,
        SkillArtifact,
        validate_skill_artifacts,
    )

    valid_remainder = tuple(SkillArtifact(skill, "") for skill in tuple(Skill)[1:])
    for malformed_skill in ("corpus-episode-completion", []):
        validation = validate_skill_artifacts(
            (SkillArtifact(malformed_skill, ""),) + valid_remainder
        )
        assert validation.ok is False
        assert validation.failure is FailureCode.MALFORMED_ARTIFACT
        assert validation.managed_allowlist_ok is True


def test_named_report_ready_requires_exact_reference_approval():
    from podcast_ingest_core.hermes_skill_protocol import (
        Approval,
        EventKind,
        PreviewOutcome,
        ProtocolEvent,
        Skill,
        Tool,
        verify_event_sequence,
    )

    def ready_events(approval: Approval) -> tuple[ProtocolEvent, ...]:
        return (
            ProtocolEvent(
                EventKind.CALL,
                Tool.NAMED_VERIFIED_REPORT,
                False,
                preview_outcome=PreviewOutcome.READY,
            ),
            ProtocolEvent(EventKind.APPROVAL, approval=approval),
            ProtocolEvent(EventKind.CALL, Tool.NAMED_VERIFIED_REPORT, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        )

    assert verify_event_sequence(
        Skill.NAMED_VERIFIED_REPORT, ready_events(Approval.EXACT_REFERENCE)
    ).ok is True
    assert verify_event_sequence(
        Skill.NAMED_VERIFIED_REPORT, ready_events(Approval.EXPLICIT)
    ).ok is False


def test_each_skill_requires_its_contract_specific_prohibition_clauses():
    from pathlib import Path

    from podcast_ingest_core.hermes_skill_protocol import (
        FailureCode,
        Skill,
        SkillArtifact,
        validate_skill_artifacts,
    )

    root = Path(__file__).resolve().parents[1]
    artifacts = {
        skill: SkillArtifact(
            skill,
            (root / ".agents" / "skills" / skill.value / "SKILL.md").read_text(encoding="utf-8"),
        )
        for skill in Skill
    }
    required_prohibitions = {
        Skill.COMPLETION: (
            "Do not start another preview or action",
            "Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, or autonomous loop as a fallback.",
        ),
        Skill.LATEST_DETERMINISTIC: (
            "Do not call with `confirm=false` before the confirmed call",
            "Do not call this tool more than once",
            "Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, batch, cache rebuild, or autonomous loop as a fallback.",
            "Do not invoke semantic summary or semantic review.",
            "Do not resolve a new latest episode during the same request.",
        ),
        Skill.LATEST_VERIFIED_REPORT: (
            "Do not use CLI or a terminal fallback.",
            "Do not retry",
            "scheduler, schedule, loop, force,",
            "select partial mode",
            "rebuild cache",
            "call another side-effect tool",
            "resolve a\nsecond latest episode",
            "call an external live provider",
            "Do not replace the\npreview/approval protocol with autonomous execution.",
        ),
        Skill.NAMED_VERIFIED_REPORT: (
            "Do not use CLI or a terminal fallback",
            "Do not retry, schedule, loop, force,",
            "partial mode",
            "rebuild cache",
            "call 015/016/017/018",
            "call LLM tools",
            "resolve\nRSS latest",
            "provide investment advice",
            "do not auto-chain remediation.",
        ),
    }

    for skill, prohibitions in required_prohibitions.items():
        for prohibition in prohibitions:
            mutated = tuple(
                SkillArtifact(
                    candidate,
                    artifact.text.replace(prohibition, "removed-prohibition", 1)
                    if candidate is skill
                    else artifact.text,
                )
                for candidate, artifact in artifacts.items()
            )
            validation = validate_skill_artifacts(mutated)
            assert validation.ok is False, (skill, prohibition)
            assert validation.failure is FailureCode.MISSING_REQUIRED_CLAUSE


def test_ast_tool_source_parser_collects_sync_async_and_parameterized_decorators(monkeypatch):
    import podcast_ingest_core.hermes_skill_protocol as protocol

    from podcast_ingest_core.hermes_skill_protocol import _tool_names_from_python_source

    source = """
@audit
@mcp.tool()
def sync_tool():
    pass

@mcp.tool(name="tool-22")
async def async_tool_22():
    pass

@before
@mcp.tool(description="parameterized")
@after
def parameterized_tool():
    pass
"""

    assert _tool_names_from_python_source(source) == frozenset(
        {"sync_tool", "tool-22", "parameterized_tool"}
    )
    assert _tool_names_from_python_source("def malformed(:\n") is None
    assert _tool_names_from_python_source("@mcp.tool\ndef ambiguous():\n    pass\n") is None
    assert _tool_names_from_python_source(
        "@mcp.tool(name=dynamic)\ndef dynamic_name():\n    pass\n"
    ) is None
    assert _tool_names_from_python_source(
        "@mcp.tool(name=1)\ndef non_string_name():\n    pass\n"
    ) is None
    assert _tool_names_from_python_source(
        "@mcp.tool(**options)\ndef expanded_options():\n    pass\n"
    ) is None
    assert _tool_names_from_python_source(
        "@mcp.tool(name=\"first\", name=\"second\")\ndef duplicate_keyword():\n    pass\n"
    ) is None

    def raise_oserror(*_args, **_kwargs):
        raise OSError("unavailable source")

    monkeypatch.setattr(protocol.Path, "read_text", raise_oserror)
    assert protocol._registry_tool_names_from_source() is None


def test_ast_tool_source_parser_rejects_non_top_level_references():
    from podcast_ingest_core.hermes_skill_protocol import _tool_names_from_python_source

    invalid_sources = (
        "if False:\n    @mcp.tool()\n    def conditional_tool():\n        pass\n",
        "def outer():\n    @mcp.tool()\n    def nested_tool():\n        pass\n",
        "class Tools:\n    @mcp.tool()\n    def method_tool():\n        pass\n",
        "tool = mcp.tool\n",
    )
    for source in invalid_sources:
        assert _tool_names_from_python_source(source) is None


def test_ast_tool_source_parser_resolves_static_names_and_rejects_duplicates(monkeypatch):
    import podcast_ingest_core.hermes_skill_protocol as protocol

    registry_names = [tool.value for tool in protocol.Tool] + ["tool_22"] + [
        f"aux_{index}" for index in range(16)
    ]
    source = "\n\n".join(
        f"@mcp.tool()\ndef {name}():\n    pass" for name in registry_names
    )
    renamed_source = source.replace(
        "@mcp.tool()\ndef aux_0",
        '@mcp.tool(name="tool_22")\ndef aux_0',
        1,
    )

    assert protocol._tool_names_from_python_source(source) == frozenset(registry_names)
    assert protocol._tool_names_from_python_source(renamed_source) is None

    monkeypatch.setattr(protocol, "_MCP_TOOL_SOURCE_FILES", ("synthetic.py",))
    monkeypatch.setattr(
        protocol.Path,
        "read_text",
        lambda *_args, **_kwargs: renamed_source,
    )
    assert protocol._registry_tool_names_from_source() is None


def test_registry_source_extraction_rejects_cross_file_duplicate_names(monkeypatch):
    import podcast_ingest_core.hermes_skill_protocol as protocol

    registry_names = [tool.value for tool in protocol.Tool] + [
        f"aux_{index}" for index in range(17)
    ]

    def source_for(names):
        return "\n\n".join(
            f"@mcp.tool()\ndef {name}():\n    pass" for name in names
        )

    source_by_name = {
        "first.py": source_for(registry_names[:11]),
        "second.py": source_for([registry_names[10], *registry_names[11:]]),
    }
    assert all(
        protocol._tool_names_from_python_source(source) is not None
        for source in source_by_name.values()
    )
    monkeypatch.setattr(protocol, "_MCP_TOOL_SOURCE_FILES", tuple(source_by_name))
    monkeypatch.setattr(
        protocol.Path,
        "read_text",
        lambda path, **_kwargs: source_by_name[path.name],
    )

    assert protocol._registry_tool_names_from_source() is None


def test_ast_tool_source_parser_rejects_indirect_tool_and_mcp_decorators():
    from podcast_ingest_core.hermes_skill_protocol import _tool_names_from_python_source

    invalid_sources = (
        "server = mcp\n@server.tool()\ndef aliased_tool():\n    pass\n",
        "server = mcp\nregister = server.tool\n@register()\ndef hidden_tool():\n    pass\n",
        "register = getattr(mcp, \"tool\")\n@register()\ndef getattr_alias_tool():\n    pass\n",
        "register = getattr(mcp_runtime.mcp, \"tool\")\n@register()\ndef module_alias_tool():\n    pass\n",
        "def imperative_tool():\n    pass\ngetattr(mcp_runtime.mcp, \"tool\")(name=\"imperative_tool\")(imperative_tool)\n",
        "from some_runtime import mcp as server\ndef imported_imperative_tool():\n    pass\ngetattr(server, \"tool\")(name=\"imported_imperative_tool\")(imported_imperative_tool)\n",
        "from package import mcp as server\n@server.tool()\ndef imported_alias_tool():\n    pass\n",
        "@unknown.tool()\ndef indirect_tool():\n    pass\n",
        "@getattr(mcp, \"tool\")()\ndef getattr_tool():\n    pass\n",
        "class Tools:\n    @server.tool()\n    def class_tool(self):\n        pass\n",
        "def outer():\n    @server.tool()\n    def nested_tool():\n        pass\n",
    )
    for source in invalid_sources:
        assert _tool_names_from_python_source(source) is None


def test_artifacts_require_an_exact_source_derived_registry_toolset():
    from pathlib import Path

    from podcast_ingest_core.hermes_skill_protocol import (
        FailureCode,
        Skill,
        SkillArtifact,
        Tool,
        _registry_tool_names_from_source,
        validate_skill_artifacts,
    )

    root = Path(__file__).resolve().parents[1]
    artifacts = tuple(
        SkillArtifact(
            skill,
            (root / ".agents" / "skills" / skill.value / "SKILL.md").read_text(encoding="utf-8"),
        )
        for skill in Skill
    )
    source_tool_names = _registry_tool_names_from_source()
    assert source_tool_names is not None
    assert len(source_tool_names) == 21
    assert frozenset(tool.value for tool in Tool) <= source_tool_names
    assert "download_audio" in source_tool_names

    wrong_tool_artifacts = (
        SkillArtifact(
            Skill.COMPLETION,
            artifacts[0].text + "\nCall `download_audio` after approval.\n",
        ),
        *artifacts[1:],
    )
    validation = validate_skill_artifacts(
        wrong_tool_artifacts,
        registry_tool_names=source_tool_names,
    )
    assert validation.ok is False
    assert validation.failure is FailureCode.WRONG_TOOL_MAPPING

    invalid_toolsets = (
        source_tool_names - {"download_audio"},
        source_tool_names | {"invented_registry_tool"},
        (source_tool_names - {"download_audio"}) | {"replacement_registry_tool"},
        frozenset({"invented_registry_tool"}),
        source_tool_names - {Tool.COMPLETION.value},
    )
    for toolset in invalid_toolsets:
        validation = validate_skill_artifacts(
            artifacts,
            registry_tool_names=toolset,
        )
        assert validation.ok is False
        assert validation.failure is FailureCode.INVALID_REGISTRY_TOOLSET

    numbered_only = (
        SkillArtifact(Skill.COMPLETION, artifacts[0].text + "\nTool 22 remains forbidden.\n"),
        *artifacts[1:],
    )
    assert validate_skill_artifacts(
        numbered_only,
        registry_tool_names=source_tool_names,
    ).ok is True
