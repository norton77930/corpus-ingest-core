"""Closed, static-only Spec030 controller-plan contracts; no runtime control."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Final
import weakref
from podcast_ingest_core.hermes_runtime_deployment import PreflightEvaluation, build_preflight_evidence
from podcast_ingest_core.hermes_runtime_source_contract import RuntimeContractEvaluation, build_contract_evidence

class ControllerStaticAdapter(str, Enum): HERMES_PROVIDER_BINDING="hermes_provider_binding"
class ControllerOperation(str, Enum):
    CREATE_DISPOSABLE="create_disposable"; ATTACH_ONE_SHOT_INPUT="attach_one_shot_input"; WAIT_FOR_SAFE_PROJECTION="wait_for_safe_projection"; DESTROY_DISPOSABLE="destroy_disposable"
class TmpfsRole(str, Enum):
    RAW_INPUT="raw_input"; RAW_OUTPUT="raw_output"; SESSION_STATE="session_state"; PROFILE_STATE="profile_state"; DATABASE_STATE="database_state"; TEMPORARY_WORK="temporary_work"
class InputMode(str, Enum): ONE_SHOT_STDIN="one_shot_stdin"
class LogSink(str, Enum): NONE="none"
class CredentialBindingKind(str, Enum): READ_ONLY_REFERENCE="read_only_reference"
class StaticPlanStatus(str, Enum):
    INVALID_PROVENANCE="BLOCKED_INVALID_PROVENANCE"; BLOCKED_SOURCE_CONTRACT="BLOCKED_SOURCE_CONTRACT"; BLOCKED_PREFLIGHT_CONTRACT="BLOCKED_PREFLIGHT_CONTRACT"; BLOCKED_STATIC_CONTROLS="BLOCKED_STATIC_CONTROLS"; PASS_OFFLINE_REMEDIATION="PASS_OFFLINE_REMEDIATION"; ACCEPTED="PASS_OFFLINE_REMEDIATION"
class CredentialPassthroughStatus(str, Enum): INVALID_REFERENCE="BLOCKED_CREDENTIAL_PASSTHROUGH"; READ_ONLY_REFERENCE_ONLY="PASS_READ_ONLY_REFERENCE"; OPAQUE_PASSTHROUGH_ONLY="PASS_READ_ONLY_REFERENCE"
class RollbackPlanStatus(str, Enum): INVALID_PROVENANCE="BLOCKED_INVALID_PROVENANCE"; QUARANTINED="BLOCKED_ROLLBACK_QUARANTINED"; COMPLETE="PASS_ROLLBACK_PLAN"
REQUIRED_TMPFS_ROLES: Final=frozenset(TmpfsRole); REQUIRED_OPERATION_ORDER: Final=tuple(ControllerOperation)
_REG: dict[int, tuple[weakref.ReferenceType, object, tuple[object, ...], type]]={}
_UNSUPPORTED=object()

def _fields(cls): return tuple(cls.__annotations__)
def _state(value, fields):
    try: state=vars(value)
    except TypeError: return None
    if type(state) is not dict or len(state)!=len(fields): return None
    keys=tuple(state)
    if any(type(key) is not str for key in keys) or any(not any(key==field for field in fields) for key in keys): return None
    return state
def _freeze(value, field=None):
    if field=="_factory_token": return ("identity",value)
    value_type=type(value)
    if value_type is bool: return ("bool",value)
    if value_type is int: return ("int",value)
    if value_type is str: return ("str",value)
    if value_type in (ControllerStaticAdapter,ControllerOperation,TmpfsRole,InputMode,LogSink,CredentialBindingKind,StaticPlanStatus,CredentialPassthroughStatus,RollbackPlanStatus,G1ROwnerLedger,OpaqueCredentialReference,ControllerCommandPlan,StaticPlanAssessment,CredentialPassthroughAssessment,G1RRollbackPlanAssessment): return ("identity",value)
    if value_type is tuple:
        values=tuple(_freeze(item) for item in value)
        return _UNSUPPORTED if _UNSUPPORTED in values else ("tuple",values)
    if value_type is frozenset:
        values=tuple(_freeze(item) for item in value)
        return _UNSUPPORTED if _UNSUPPORTED in values else ("frozenset",values)
    return _UNSUPPORTED
def _matches(value, frozen):
    kind=frozen[0]
    if kind=="identity": return value is frozen[1]
    if kind=="bool": return type(value) is bool and value is frozen[1]
    if kind=="int": return type(value) is int and value==frozen[1]
    if kind=="str": return type(value) is str and value==frozen[1]
    if kind=="tuple": return type(value) is tuple and len(value)==len(frozen[1]) and all(_matches(item,expected) for item,expected in zip(value,frozen[1]))
    if kind=="frozenset":
        if type(value) is not frozenset or len(value)!=len(frozen[1]): return False
        matched=[False]*len(frozen[1])
        for item in value:
            for index,expected in enumerate(frozen[1]):
                if not matched[index] and _matches(item,expected): matched[index]=True; break
            else: return False
        return True
    return False
def _seal(value, fields):
    state=_state(value,fields)
    if state is None: return None
    values=tuple(_freeze(state[field],field) for field in fields)
    return None if _UNSUPPORTED in values else values
def _seal_matches(state, fields, seal): return len(seal)==len(fields) and all(_matches(state[field],expected) for field,expected in zip(fields,seal))
def _issue(value, fields):
    token=object(); object.__setattr__(value,"_factory_token",token); seal=_seal(value,fields); assert seal is not None; key=id(value)
    def drop(ref, *, k=key):
        if (item:=_REG.get(k)) and item[0] is ref: _REG.pop(k,None)
    _REG[key]=(weakref.ref(value,drop),token,seal,type(value)); return value
def _issued(value, fields, expected):
    if type(value) is not expected: return False
    item=_REG.get(id(value)); state=_state(value,fields)
    return bool(item and state is not None and item[0]() is value and state["_factory_token"] is item[1] and _seal_matches(state,fields,item[2]) and item[3] is expected)

@dataclass(frozen=True,init=False)
class G1ROwnerLedger:
    _factory_token: object
    def __init__(self,*a,**k): raise TypeError("use issue_g1r_owner_ledger()")
    def __repr__(self): return "G1ROwnerLedger()"
    __str__=__repr__
_OWNER_FIELDS=_fields(G1ROwnerLedger)
def issue_g1r_owner_ledger(owner):
    if type(owner) is not str or not owner: raise ValueError("non-empty owner required")
    return _issue(object.__new__(G1ROwnerLedger),_OWNER_FIELDS)
def _ledger_issued(ledger): return type(ledger) is G1ROwnerLedger and _issued(ledger,_OWNER_FIELDS,G1ROwnerLedger)

@dataclass(frozen=True)
class AdapterCapability:
    reference_only: bool; materializes_value: bool
_CAPABILITIES: Final={ControllerStaticAdapter.HERMES_PROVIDER_BINDING: AdapterCapability(True,False)}
def adapter_capability(adapter):
    if type(adapter) is not ControllerStaticAdapter: return AdapterCapability(False,True)
    return _CAPABILITIES[adapter]

@dataclass(frozen=True,init=False)
class OpaqueCredentialReference:
    adapter: ControllerStaticAdapter; binding_kind: CredentialBindingKind; ledger: G1ROwnerLedger; _factory_token: object
    def __init__(self,*a,**k): raise TypeError("use issue_opaque_credential_reference()")
    def __repr__(self): return "OpaqueCredentialReference()"
    __str__=__repr__
_OPAQUE=_fields(OpaqueCredentialReference)
def issue_opaque_credential_reference(ledger,adapter):
    if type(adapter) is not ControllerStaticAdapter: raise ValueError("sealed reference-only adapter and ledger required")
    cap=adapter_capability(adapter)
    if not cap.reference_only or cap.materializes_value or not _ledger_issued(ledger): raise ValueError("sealed reference-only adapter and ledger required")
    item=object.__new__(OpaqueCredentialReference); object.__setattr__(item,"adapter",adapter); object.__setattr__(item,"binding_kind",CredentialBindingKind.READ_ONLY_REFERENCE); object.__setattr__(item,"ledger",ledger); return _issue(item,_OPAQUE)
def _opaque_issued(ref):
    if not isinstance(ref,OpaqueCredentialReference) or not _issued(ref,_OPAQUE,OpaqueCredentialReference): return False
    capability=adapter_capability(ref.adapter)
    return _ledger_issued(ref.ledger) and capability.reference_only is True and capability.materializes_value is False

@dataclass(frozen=True)
class G1RBaselineRollbackIntentFacts:
    overlay_deactivate_intent: bool; overlay_remove_intent: bool; baseline_preserve_intent: bool; controls_restore_intent: bool; offline_lease_revoke_intent: bool
@dataclass(frozen=True)
class G1RRollbackPlanFacts:
    baseline_intents: G1RBaselineRollbackIntentFacts; disposable_container_destroy_intent: bool; all_tmpfs_destroy_intent: bool; fresh_session_destroy_intent: bool; raw_ephemeral_surfaces_destroy_intent: bool; credential_binding_revoke_intent: bool; controller_plan_revoke_intent: bool
def _intent_snapshot(value):
    if type(value) is not G1RRollbackPlanFacts: return None
    outer_fields=_fields(G1RRollbackPlanFacts); outer_state=_state(value,outer_fields)
    if outer_state is None or type(outer_state["baseline_intents"]) is not G1RBaselineRollbackIntentFacts: return None
    baseline_fields=_fields(G1RBaselineRollbackIntentFacts); baseline_state=_state(outer_state["baseline_intents"],baseline_fields)
    if baseline_state is None: return None
    values=tuple(baseline_state[field] for field in baseline_fields)+tuple(outer_state[field] for field in outer_fields if field!="baseline_intents")
    return values if len(values)==11 and all(type(item) is bool for item in values) else None

@dataclass(frozen=True)
class ControllerPlanFacts:
    source_evaluation: RuntimeContractEvaluation; preflight_evaluation: PreflightEvaluation; deployment_ledger: G1ROwnerLedger; credential_reference: OpaqueCredentialReference; operation_order: tuple[ControllerOperation,...]; tmpfs_roles: frozenset[TmpfsRole]; input_mode: InputMode; log_sink: LogSink; credential_binding_kind: CredentialBindingKind; read_only_rootfs: bool; auto_remove: bool; destroy_disposable_intent: bool; raw_argv_absent: bool; writable_durable_mount_count: int; persistent_volume_count: int; host_port_count: int; tty_absent: bool; shell_absent: bool; fresh_session_only: bool; rollback_plan_facts: G1RRollbackPlanFacts
@dataclass(frozen=True,init=False)
class ControllerCommandPlan:
    deployment_ledger: G1ROwnerLedger; credential_reference: OpaqueCredentialReference; source_contract_status: str; source_identity_reused: bool; preflight_status: str; preflight_controls_verified: bool; operation_order: tuple[ControllerOperation,...]; tmpfs_roles: frozenset[TmpfsRole]; input_mode: InputMode; log_sink: LogSink; credential_binding_kind: CredentialBindingKind; read_only_rootfs: bool; auto_remove: bool; destroy_disposable_intent: bool; raw_argv_absent: bool; writable_durable_mount_count: int; persistent_volume_count: int; host_port_count: int; tty_absent: bool; shell_absent: bool; fresh_session_only: bool; rollback_intent_snapshot: tuple[bool,...]; live_actions_authorized: bool; _factory_token: object
    def __init__(self,*a,**k): raise TypeError("use build_controller_command_plan()")
    def __repr__(self): return "ControllerCommandPlan()"
    __str__=__repr__
_PLAN=_fields(ControllerCommandPlan)
def _plan_issued(plan): return isinstance(plan,ControllerCommandPlan) and _issued(plan,_PLAN,ControllerCommandPlan) and _ledger_issued(plan.deployment_ledger) and _opaque_issued(plan.credential_reference) and plan.credential_reference.ledger is plan.deployment_ledger

def _valid_facts(facts):
    if type(facts) is not ControllerPlanFacts: return False
    state=_state(facts,_fields(ControllerPlanFacts))
    if state is None: return False
    ints=("writable_durable_mount_count","persistent_volume_count","host_port_count"); bools=("read_only_rootfs","auto_remove","destroy_disposable_intent","raw_argv_absent","tty_absent","shell_absent","fresh_session_only")
    return (type(state["source_evaluation"]) is RuntimeContractEvaluation and type(state["preflight_evaluation"]) is PreflightEvaluation and _opaque_issued(state["credential_reference"]) and state["credential_reference"].ledger is state["deployment_ledger"] and _ledger_issued(state["deployment_ledger"]) and isinstance(state["operation_order"],tuple) and all(type(x) is ControllerOperation for x in state["operation_order"]) and isinstance(state["tmpfs_roles"],frozenset) and all(type(x) is TmpfsRole for x in state["tmpfs_roles"]) and type(state["input_mode"]) is InputMode and type(state["log_sink"]) is LogSink and type(state["credential_binding_kind"]) is CredentialBindingKind and all(type(state[x]) is bool for x in bools) and all(type(state[x]) is int for x in ints) and _intent_snapshot(state["rollback_plan_facts"]) is not None)
def build_controller_command_plan(facts):
    if not _valid_facts(facts): raise ValueError("closed controller plan facts required")
    source=build_contract_evidence(facts.source_evaluation); preflight=build_preflight_evidence(facts.preflight_evaluation); controls=all(preflight[x] is True for x in ("baseline_image_pinned","disposable_overlay_prepared","overlay_isolated_from_production","controls_resolved","interposer_boundary_verified","terminal_shell_absent","rollback_recipe_complete"))
    values={key:getattr(facts,key) for key in _fields(ControllerPlanFacts) if key not in ("source_evaluation","preflight_evaluation","rollback_plan_facts")}; values.update(source_contract_status=source["verdict"],source_identity_reused=source["pinned_manifest_identity_verified"] is True,preflight_status=preflight["status"],preflight_controls_verified=controls,rollback_intent_snapshot=_intent_snapshot(facts.rollback_plan_facts),live_actions_authorized=False)
    return _issue(object.__new__(ControllerCommandPlan),_PLAN) if False else _make_plan(values)
def _make_plan(values):
    item=object.__new__(ControllerCommandPlan)
    for key,value in values.items(): object.__setattr__(item,key,value)
    return _issue(item,_PLAN)

@dataclass(frozen=True,init=False)
class StaticPlanAssessment:
    status: StaticPlanStatus; owner_ledger_present: bool; source_identity_reused: bool; offline_baseline_preflight_status: str; no_durable_persistence_static_contract_satisfied: bool; ephemeral_storage_plan_complete: bool; log_sink_absent_static_contract_satisfied: bool; fresh_session_static_contract_satisfied: bool; command_plan_factory_issued: bool; _factory_token: object
    def __init__(self,*a,**k): raise TypeError("use assess_static_controller_plan()")
@dataclass(frozen=True,init=False)
class CredentialPassthroughAssessment:
    status: CredentialPassthroughStatus; binding_reference_only: bool; credential_value_read: bool; credential_value_copied: bool; credential_value_projected: bool; credential_value_logged: bool; _factory_token: object
    def __init__(self,*a,**k): raise TypeError("use assess_opaque_credential_passthrough()")
@dataclass(frozen=True,init=False)
class G1RRollbackPlanAssessment:
    status: RollbackPlanStatus; rollback_plan_complete: bool; quarantine_required: bool; _factory_token: object
    def __init__(self,*a,**k): raise TypeError("use assess_g1r_rollback_plan()")
def _make(cls,**values):
    item=object.__new__(cls)
    for key,value in values.items(): object.__setattr__(item,key,value)
    return _issue(item,_fields(cls))
def is_factory_issued_static_plan_assessment(x): return isinstance(x,StaticPlanAssessment) and _issued(x,_fields(StaticPlanAssessment),StaticPlanAssessment)
def is_factory_issued_credential_assessment(x): return isinstance(x,CredentialPassthroughAssessment) and _issued(x,_fields(CredentialPassthroughAssessment),CredentialPassthroughAssessment)
def is_factory_issued_rollback_assessment(x): return isinstance(x,G1RRollbackPlanAssessment) and _issued(x,_fields(G1RRollbackPlanAssessment),G1RRollbackPlanAssessment)
def assess_static_controller_plan(plan):
    if not _plan_issued(plan): return _make(StaticPlanAssessment,status=StaticPlanStatus.INVALID_PROVENANCE,owner_ledger_present=False,source_identity_reused=False,offline_baseline_preflight_status="not_available",no_durable_persistence_static_contract_satisfied=False,ephemeral_storage_plan_complete=False,log_sink_absent_static_contract_satisfied=False,fresh_session_static_contract_satisfied=False,command_plan_factory_issued=False)
    source_ok=plan.source_contract_status=="BLOCKED_RUNTIME_SEAM" and plan.source_identity_reused is True; preflight_ok=plan.preflight_status=="BLOCKED_RUNTIME_SEAM" and plan.preflight_controls_verified is True; durable=plan.read_only_rootfs is True and plan.writable_durable_mount_count==0 and plan.persistent_volume_count==0; ephemeral=plan.tmpfs_roles==REQUIRED_TMPFS_ROLES and plan.auto_remove is True and plan.destroy_disposable_intent is True; static=all((plan.operation_order==REQUIRED_OPERATION_ORDER,plan.input_mode is InputMode.ONE_SHOT_STDIN,plan.log_sink is LogSink.NONE,plan.credential_binding_kind is CredentialBindingKind.READ_ONLY_REFERENCE,plan.raw_argv_absent is True,plan.host_port_count==0,plan.tty_absent is True,plan.shell_absent is True,plan.fresh_session_only is True,plan.live_actions_authorized is False,durable,ephemeral))
    status=StaticPlanStatus.PASS_OFFLINE_REMEDIATION if source_ok and preflight_ok and static else StaticPlanStatus.BLOCKED_SOURCE_CONTRACT if not source_ok else StaticPlanStatus.BLOCKED_PREFLIGHT_CONTRACT if not preflight_ok else StaticPlanStatus.BLOCKED_STATIC_CONTROLS
    return _make(StaticPlanAssessment,status=status,owner_ledger_present=True,source_identity_reused=source_ok,offline_baseline_preflight_status=plan.preflight_status,no_durable_persistence_static_contract_satisfied=durable,ephemeral_storage_plan_complete=ephemeral,log_sink_absent_static_contract_satisfied=plan.log_sink is LogSink.NONE,fresh_session_static_contract_satisfied=plan.fresh_session_only is True,command_plan_factory_issued=True)
def assess_opaque_credential_passthrough(ref,ledger):
    ok=_opaque_issued(ref) and _ledger_issued(ledger) and ref.ledger is ledger and ref.binding_kind is CredentialBindingKind.READ_ONLY_REFERENCE
    return _make(CredentialPassthroughAssessment,status=CredentialPassthroughStatus.READ_ONLY_REFERENCE_ONLY if ok else CredentialPassthroughStatus.INVALID_REFERENCE,binding_reference_only=ok,credential_value_read=False,credential_value_copied=False,credential_value_projected=False,credential_value_logged=False)
def assess_g1r_rollback_plan(facts):
    snapshot=_intent_snapshot(facts); complete=bool(snapshot and all(item is True for item in snapshot))
    return _make(G1RRollbackPlanAssessment,status=RollbackPlanStatus.COMPLETE if complete else RollbackPlanStatus.QUARANTINED,rollback_plan_complete=complete,quarantine_required=not complete)
