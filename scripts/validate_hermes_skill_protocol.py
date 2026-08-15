"""Emit bounded, offline assurance evidence for the Hermes Skill contracts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Sequence

from podcast_ingest_core import hermes_integration
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
    SkillArtifact,
    SkillRoute,
    SkillToolBinding,
    Tool,
    build_contract_evidence,
    canonical_skill_bindings,
    validate_skill_artifacts,
    verify_event_sequence,
)


_SCHEMA_VERSION = "hermes-skill-protocol-cli-v1"
_ROOT = Path(__file__).resolve().parents[1]


def _contract_artifacts() -> ArtifactValidation:
    managed_skills = hermes_integration.MANAGED_SKILLS
    try:
        skills = tuple(Skill(name) for name in managed_skills)
    except (TypeError, ValueError):
        return validate_skill_artifacts((), managed_skills=managed_skills)
    artifacts = tuple(
        SkillArtifact(
            skill,
            (_ROOT / ".agents" / "skills" / skill.value / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        for skill in skills
    )
    return validate_skill_artifacts(artifacts, managed_skills=managed_skills)


def _synthetic_artifacts() -> ArtifactValidation:
    return ArtifactValidation(
        True,
        FailureCode.NONE,
        canonical_skill_bindings(),
        True,
    )


def _events_for(skill: Skill) -> tuple[ProtocolEvent, ...]:
    if skill is Skill.COMPLETION:
        return (
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, False, Approval.NONE, CompletionAction.NEXT),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.COMPLETION, True, Approval.NONE, CompletionAction.DETERMINISTIC),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        )
    if skill is Skill.LATEST_DETERMINISTIC:
        return (
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXPLICIT),
            ProtocolEvent(EventKind.CALL, Tool.LATEST_DETERMINISTIC, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        )
    if skill is Skill.LATEST_VERIFIED_REPORT:
        return (
            ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, False),
            ProtocolEvent(EventKind.APPROVAL, approval=Approval.EXACT_REFERENCE_AND_ACK),
            ProtocolEvent(EventKind.CALL, Tool.LATEST_VERIFIED_REPORT, True),
            ProtocolEvent(EventKind.REPORT),
            ProtocolEvent(EventKind.STOP),
        )
    return (
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
    )


def _synthetic_protocol_status() -> dict[str, bool]:
    protocols_pass = all(
        verify_event_sequence(skill, _events_for(skill)).ok for skill in Skill
    )
    unknown_event_fail_closed = not verify_event_sequence(
        Skill.COMPLETION, (ProtocolEvent(object()),)
    ).ok
    non_boolean_fail_closed = not verify_event_sequence(
        Skill.COMPLETION,
        (ProtocolEvent(EventKind.CALL, Tool.COMPLETION, 1),),
    ).ok
    return {
        "synthetic_protocols_pass": protocols_pass,
        "unknown_event_fail_closed": unknown_event_fail_closed,
        "non_boolean_fail_closed": non_boolean_fail_closed,
    }


def _payload(mode: str, artifacts: ArtifactValidation) -> dict[str, object]:
    evidence = [
        build_contract_evidence(
            SkillRoute(RouteDisposition.ROUTE, skill),
            artifacts,
            verify_event_sequence(skill, _events_for(skill)),
        ).to_dict()
        for skill in Skill
    ]
    ok = all(item["ok"] is True for item in evidence)
    payload: dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "ok": ok,
        "mode": mode,
        "failure_code": "none" if ok else next(
            item["failure_code"] for item in evidence if item["ok"] is False
        ),
        "managed_allowlist_ok": (
            artifacts.managed_allowlist_ok
            if isinstance(artifacts, ArtifactValidation)
            and type(artifacts.managed_allowlist_ok) is bool
            else False
        ),
        "hermes_runtime_observation": "not_evaluated",
        "evidence": evidence,
    }
    if mode == "synthetic":
        synthetic = _synthetic_protocol_status()
        payload.update(synthetic)
        payload["ok"] = ok and all(synthetic.values())
        if payload["ok"] is False and payload["failure_code"] == "none":
            payload["failure_code"] = "invalid_evidence"
    return payload


def _failure_payload(code: str) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "ok": False,
        "mode": "rejected",
        "failure_code": code,
        "managed_allowlist_ok": False,
        "hermes_runtime_observation": "not_evaluated",
        "evidence": [],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Accept only the fixed ``contracts`` and ``synthetic`` offline modes."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1 or arguments[0] not in {"contracts", "synthetic"}:
        print(json.dumps(_failure_payload("invalid_mode"), sort_keys=True))
        return 2
    try:
        artifacts = _contract_artifacts() if arguments[0] == "contracts" else _synthetic_artifacts()
        payload = _payload(arguments[0], artifacts)
        print(json.dumps(payload, sort_keys=True))
        if payload["ok"] is False:
            return 1
    except Exception:
        print(json.dumps(_failure_payload("internal_failure"), sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
