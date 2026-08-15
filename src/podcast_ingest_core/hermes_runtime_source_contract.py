"""Pinned, offline-only Hermes v0.19.0 source contract for Spec 029.

The contract validates only a repository-pinned manifest.  It never fetches
source, starts Hermes, or treats an unverified input/provider/overlay seam as
safe for live activation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Final


class ContractVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    BLOCKED_SOURCE_DRIFT = "BLOCKED_SOURCE_DRIFT"
    BLOCKED_RUNTIME_SEAM = "BLOCKED_RUNTIME_SEAM"


@dataclass(frozen=True)
class PinnedRuntimeManifest:
    target_commit_sha: str
    one_shot_input_seam: str
    terminal_verdict: str
    plugin_live_activation_authorized: bool = False


@dataclass(frozen=True)
class RuntimeContractEvaluation:
    verdict: ContractVerdict
    pinned_manifest_identity_verified: bool
    safe_one_shot_input_seam_verified: bool
    plugin_live_activation_authorized: bool


_MANIFEST: Final = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "029-hermes-blocked-tool-attempt-runtime-smoke"
    / "contracts"
    / "hermes-v0.19.0-runtime-source-manifest.json"
)
EXPECTED_SOURCE_BLOBS: Final = {
    "plugins_py_blob_sha": "6ca393fca53c1fd2b3479bed72180fedcc848c88",
    "model_tools_py_blob_sha": "32394a69eec64f3d676bedb1659a6f4e94887a74",
    "tool_executor_py_blob_sha": "d235de36c03dd668bfb10377ef51c7074368c6b9",
    "hooks_blob_sha": "d3f86bd00e80254b42ea9440cdcede4ab9a0c68b",
}
_EXPECTED: Final = {
    "schema_version": "hermes-v0.19.0-runtime-source-contract-v1",
    "repository": "NousResearch/hermes-agent",
    "release": "v0.19.0",
    "release_date": "2026.7.20",
    "target_commit_sha": "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6",
    **EXPECTED_SOURCE_BLOBS,
    "plugin_registration_contract": "source_pre_tool_call_post_tool_call_capability_register(ctx)_register_hook_plugin_pre_tool_call_only",
    "pre_dispatch_contract": "action_block_message_SPEC029_POLICY_BLOCK_block_before_execution",
    "hook_failure_contract": "callback_exception_fail_open",
    "one_shot_input_seam": "unverified",
    "provider_seam": "unverified",
    "disposable_overlay_seam": "unverified",
    "terminal_verdict": "BLOCKED_RUNTIME_SEAM",
}
SAFE_EVIDENCE_KEYS: Final = frozenset(
    {
        "schema_version",
        "spec_id",
        "verdict",
        "pinned_manifest_identity_verified",
        "safe_one_shot_input_seam_verified",
        "plugin_live_activation_authorized",
        "live_actions_authorized",
        "raw_persisted",
    }
)


def _read() -> object:
    try:
        return json.loads(_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _source_drift() -> RuntimeContractEvaluation:
    return RuntimeContractEvaluation(
        ContractVerdict.BLOCKED_SOURCE_DRIFT, False, False, False
    )


def load_pinned_runtime_manifest() -> PinnedRuntimeManifest:
    raw = _read()
    if not isinstance(raw, dict) or raw != _EXPECTED:
        return PinnedRuntimeManifest("", "", "")
    return PinnedRuntimeManifest(
        raw["target_commit_sha"],
        raw["one_shot_input_seam"],
        raw["terminal_verdict"],
        False,
    )


def evaluate_pinned_runtime_contract(
    observed_manifest: object = None,
) -> RuntimeContractEvaluation:
    """Fail closed on any missing, extra, or changed manifest fact."""
    raw = _read() if observed_manifest is None else observed_manifest
    if not isinstance(raw, dict) or raw != _EXPECTED:
        return _source_drift()
    # All three operational seams remain intentionally unverified in G0.
    return RuntimeContractEvaluation(
        ContractVerdict.BLOCKED_RUNTIME_SEAM, True, False, False
    )


def build_contract_evidence(evaluation: object) -> dict[str, str | bool]:
    """Project only the current terminal state; forged fields fail closed."""
    current = evaluate_pinned_runtime_contract()
    if not isinstance(evaluation, RuntimeContractEvaluation) or evaluation != current:
        evaluation = _source_drift()
    return {
        "schema_version": "hermes-runtime-source-contract-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "verdict": evaluation.verdict.value,
        "pinned_manifest_identity_verified": (
            evaluation.pinned_manifest_identity_verified is True
        ),
        "safe_one_shot_input_seam_verified": (
            evaluation.safe_one_shot_input_seam_verified is True
        ),
        "plugin_live_activation_authorized": (
            evaluation.plugin_live_activation_authorized is True
        ),
        "live_actions_authorized": False,
        "raw_persisted": False,
    }
