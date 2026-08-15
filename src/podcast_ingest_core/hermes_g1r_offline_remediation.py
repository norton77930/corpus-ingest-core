"""Factory-sealed static G1R evidence; no runtime observation or execution."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Final
import weakref
from podcast_ingest_core.hermes_runtime_controller_plan import CredentialPassthroughStatus, RollbackPlanStatus, StaticPlanStatus, assess_g1r_rollback_plan, assess_opaque_credential_passthrough, assess_static_controller_plan, is_factory_issued_credential_assessment, is_factory_issued_rollback_assessment, is_factory_issued_static_plan_assessment
class G1RStatus(str,Enum):
    BLOCKED_INVALID_PROVENANCE="BLOCKED_INVALID_PROVENANCE"; BLOCKED_SOURCE_CONTRACT="BLOCKED_SOURCE_CONTRACT"; BLOCKED_PREFLIGHT_CONTRACT="BLOCKED_PREFLIGHT_CONTRACT"; BLOCKED_STATIC_CONTROLS="BLOCKED_STATIC_CONTROLS"; BLOCKED_CREDENTIAL_PASSTHROUGH="BLOCKED_CREDENTIAL_PASSTHROUGH"; BLOCKED_ROLLBACK_QUARANTINED="BLOCKED_ROLLBACK_QUARANTINED"; PASS_OFFLINE_REMEDIATION="PASS_OFFLINE_REMEDIATION"; STATIC_PLAN_ACCEPTED="PASS_OFFLINE_REMEDIATION"
SAFE_G1R_EVIDENCE_KEYS: Final=frozenset({"schema_version","spec_id","status","predecessor_spec_id","gate","evidence_basis","source_identity_reused","historical_g1_status","offline_baseline_preflight_status","owner_ledger_present","command_plan_factory_issued","input_seam_assessment","no_durable_persistence_static_contract_satisfied","ephemeral_storage_plan_complete","log_sink_absent_static_contract_satisfied","fresh_session_static_contract_satisfied","opaque_credential_passthrough_assessment","credential_value_read","credential_value_copied","credential_value_projected","credential_value_logged","binding_reference_only","rollback_plan_complete","runtime_observation_status","docker_runtime_observed","credential_runtime_observed","raw_persisted","raw_persisted_scope","g2_authorized","g3a_authorized","live_actions_authorized"})
_REG={}
@dataclass(frozen=True,init=False)
class G1ROfflineRemediationEvaluation:
    status:G1RStatus; _factory_token:object
    def __init__(self,*a,**k): raise TypeError("use evaluate_g1r_offline_remediation()")
    def __repr__(self): return "G1ROfflineRemediationEvaluation()"
    __str__=__repr__
_FIELDS=tuple(G1ROfflineRemediationEvaluation.__annotations__)
def _evaluation_state(item):
    try: state=vars(item)
    except TypeError: return None
    if type(state) is not dict or len(state)!=len(_FIELDS): return None
    keys=tuple(state)
    if any(type(key) is not str for key in keys) or any(not any(key==field for field in _FIELDS) for key in keys): return None
    return state
def _fallback(status): return {"schema_version":"hermes-g1r-offline-remediation-evidence-v2","spec_id":"030-hermes-g1r-offline-remediation","status":status.value,"predecessor_spec_id":"029-hermes-blocked-tool-attempt-runtime-smoke","gate":"G1R_OFFLINE_REMEDIATION","evidence_basis":"static_command_plan_contract","source_identity_reused":False,"historical_g1_status":"not_available","offline_baseline_preflight_status":"not_available","owner_ledger_present":False,"command_plan_factory_issued":False,"input_seam_assessment":False,"no_durable_persistence_static_contract_satisfied":False,"ephemeral_storage_plan_complete":False,"log_sink_absent_static_contract_satisfied":False,"fresh_session_static_contract_satisfied":False,"opaque_credential_passthrough_assessment":False,"credential_value_read":False,"credential_value_copied":False,"credential_value_projected":False,"credential_value_logged":False,"binding_reference_only":False,"rollback_plan_complete":False,"runtime_observation_status":"not_run","docker_runtime_observed":False,"credential_runtime_observed":False,"raw_persisted":False,"raw_persisted_scope":"safe_evidence_projection_only","g2_authorized":False,"g3a_authorized":False,"live_actions_authorized":False}
def _payload(status,static=None,credential=None,rollback=None):
    result=_fallback(status)
    if not (is_factory_issued_static_plan_assessment(static) and (credential is None or is_factory_issued_credential_assessment(credential)) and (rollback is None or is_factory_issued_rollback_assessment(rollback))): return result
    result.update(source_identity_reused=static.source_identity_reused,historical_g1_status="BLOCKED_CONTROL_PLANE",offline_baseline_preflight_status=static.offline_baseline_preflight_status,owner_ledger_present=static.owner_ledger_present,command_plan_factory_issued=static.command_plan_factory_issued,input_seam_assessment=static.status is StaticPlanStatus.PASS_OFFLINE_REMEDIATION,no_durable_persistence_static_contract_satisfied=static.no_durable_persistence_static_contract_satisfied,ephemeral_storage_plan_complete=static.ephemeral_storage_plan_complete,log_sink_absent_static_contract_satisfied=static.log_sink_absent_static_contract_satisfied,fresh_session_static_contract_satisfied=static.fresh_session_static_contract_satisfied)
    if credential: result.update(opaque_credential_passthrough_assessment=credential.status is CredentialPassthroughStatus.READ_ONLY_REFERENCE_ONLY,binding_reference_only=credential.binding_reference_only)
    if rollback: result["rollback_plan_complete"]=rollback.rollback_plan_complete
    return result
def _make(status,static=None,credential=None,rollback=None):
    item=object.__new__(G1ROfflineRemediationEvaluation); token=object(); object.__setattr__(item,"status",status); object.__setattr__(item,"_factory_token",token); key=id(item)
    def drop(ref,*,k=key):
        if (old:=_REG.get(k)) and old[0] is ref:_REG.pop(k,None)
    _REG[key]=(weakref.ref(item,drop),token,status,_payload(status,static,credential,rollback),type(item)); return item
def _issued(item):
    if type(item) is not G1ROfflineRemediationEvaluation: return False
    old=_REG.get(id(item)); state=_evaluation_state(item)
    return bool(old and state is not None and old[0]() is item and state["_factory_token"] is old[1] and type(state["status"]) is G1RStatus and state["status"] is old[2] and old[4] is G1ROfflineRemediationEvaluation)
def evaluate_g1r_offline_remediation(plan):
    static=assess_static_controller_plan(plan)
    if not is_factory_issued_static_plan_assessment(static) or static.status is StaticPlanStatus.INVALID_PROVENANCE:return _make(G1RStatus.BLOCKED_INVALID_PROVENANCE)
    if static.status is StaticPlanStatus.BLOCKED_SOURCE_CONTRACT:return _make(G1RStatus.BLOCKED_SOURCE_CONTRACT,static)
    if static.status is StaticPlanStatus.BLOCKED_PREFLIGHT_CONTRACT:return _make(G1RStatus.BLOCKED_PREFLIGHT_CONTRACT,static)
    if static.status is not StaticPlanStatus.PASS_OFFLINE_REMEDIATION:return _make(G1RStatus.BLOCKED_STATIC_CONTROLS,static)
    credential=assess_opaque_credential_passthrough(plan.credential_reference,plan.deployment_ledger)
    if not is_factory_issued_credential_assessment(credential) or credential.status is not CredentialPassthroughStatus.READ_ONLY_REFERENCE_ONLY:return _make(G1RStatus.BLOCKED_CREDENTIAL_PASSTHROUGH,static,credential)
    rollback=assess_g1r_rollback_plan_from_plan(plan)
    if rollback.status is not RollbackPlanStatus.COMPLETE:return _make(G1RStatus.BLOCKED_ROLLBACK_QUARANTINED,static,credential,rollback)
    return _make(G1RStatus.PASS_OFFLINE_REMEDIATION,static,credential,rollback)
def assess_g1r_rollback_plan_from_plan(plan):
    # plan seal was already verified by static assessment; recreate only closed scalar intent facts.
    from podcast_ingest_core.hermes_runtime_controller_plan import G1RBaselineRollbackIntentFacts,G1RRollbackPlanFacts
    values=plan.rollback_intent_snapshot; return assess_g1r_rollback_plan(G1RRollbackPlanFacts(G1RBaselineRollbackIntentFacts(*values[:5]),*values[5:]))
def build_g1r_offline_remediation_evidence(evaluation): return dict(_REG[id(evaluation)][3]) if _issued(evaluation) else _fallback(G1RStatus.BLOCKED_INVALID_PROVENANCE)
