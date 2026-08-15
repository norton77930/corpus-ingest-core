"""Spec032 sealed offline approval and single-use lease authority."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import math
import threading
import time
import weakref

class Spec032Scope(str, Enum):
    OFFLINE_EXECUTOR_VALIDATION = "OFFLINE_EXECUTOR_VALIDATION"
    LIVE_H4_ONE_RUN = "LIVE_H4_ONE_RUN"
class Spec032GateStatus(str, Enum):
    BLOCKED_CREDENTIAL_SEAM = "BLOCKED_CREDENTIAL_SEAM"

@dataclass(frozen=True, init=False)
class Spec032GateDecision:
    status: Spec032GateStatus; lease_issue_count: int; ledger_claim_count: int; driver_call_count: int; runtime_status: str; _factory_token: object
    def __init__(self,*_a: object,**_k: object)->None: raise TypeError("use evaluate_spec032_production_gate()")
    def __repr__(self)->str: return "Spec032GateDecision()"
    __str__=__repr__
@dataclass(frozen=True, init=False)
class Spec032OfflineApproval:
    _factory_token: object
    def __init__(self,*_a: object,**_k: object)->None: raise TypeError("use issue_offline_executor_approval()")
    def __repr__(self)->str: return "Spec032OfflineApproval()"
    __str__=__repr__
@dataclass(frozen=True, init=False)
class Spec032AttemptLease:
    _factory_token: object
    def __init__(self,*_a: object,**_k: object)->None: raise TypeError("use issue_spec032_attempt_lease()")
    def __repr__(self)->str: return "Spec032AttemptLease()"
    __str__=__repr__

_LOCK=threading.RLock(); _LEASE_SECONDS=30.0; _trusted_monotonic=time.monotonic
_GATE_REGISTRY: dict[int, tuple[weakref.ReferenceType[object],object,tuple[object,...]]]={}
_APPROVAL_REGISTRY: dict[int, tuple[weakref.ReferenceType[object],object,tuple[object,...]]]={}
_LEASE_REGISTRY: dict[int, tuple[weakref.ReferenceType[object],object,tuple[object,...],object,Spec032Scope,float,float,bool]]={}

def _fields(cls:type)->tuple[str,...]: return tuple(cls.__annotations__)
def _state(value:object,fields:tuple[str,...])->dict[str,object]|None:
    try: state=vars(value)
    except (TypeError,BaseException): return None
    if type(state) is not dict or len(state)!=len(fields): return None
    keys=tuple(state)
    if any(type(key) is not str for key in keys): return None
    if any(not any(key==field for field in fields) for key in keys): return None
    return state
def _freeze(value:object)->object:
    if type(value) is bool: return ("bool",value)
    if type(value) is int: return ("int",value)
    if type(value) is str: return ("str",value)
    if type(value) in (Spec032GateStatus,): return ("identity",value)
    return ("identity",value)
def _matches(value:object,sealed:object)->bool:
    kind,expected=sealed
    if kind=="bool": return type(value) is bool and value is expected
    if kind=="int": return type(value) is int and value==expected
    if kind=="str": return type(value) is str and value==expected
    return value is expected
def _register(registry:dict,value:object,token:object,*facts:object)->None:
    key=id(value)
    def discard(ref:weakref.ReferenceType[object],*,value_key:int=key)->None:
        with _LOCK:
            current=registry.get(value_key)
            if current is not None and current[0] is ref: registry.pop(value_key,None)
    registry[key]=(weakref.ref(value,discard),token,tuple(facts))
def _make(cls:type,**values:object)->object:
    value=object.__new__(cls)
    for name,item in values.items(): object.__setattr__(value,name,item)
    token=object(); object.__setattr__(value,"_factory_token",token)
    state=_state(value,_fields(cls)); assert state is not None
    _register((_GATE_REGISTRY if cls is Spec032GateDecision else _APPROVAL_REGISTRY),value,token,*tuple(_freeze(state[name]) for name in _fields(cls)))
    return value
def _issued(value:object,cls:type,registry:dict)->bool:
    if type(value) is not cls: return False
    fields=_fields(cls); state=_state(value,fields)
    with _LOCK: entry=registry.get(id(value))
    if entry is None or state is None or entry[0]() is not value or state["_factory_token"] is not entry[1] or len(entry[2])!=len(fields): return False
    try: return all(_matches(state[name],seal) for name,seal in zip(fields,entry[2]))
    except BaseException: return False

def evaluate_spec032_production_gate()->Spec032GateDecision:
    return _make(Spec032GateDecision,status=Spec032GateStatus.BLOCKED_CREDENTIAL_SEAM,lease_issue_count=0,ledger_claim_count=0,driver_call_count=0,runtime_status="not_run")
def is_factory_issued_spec032_gate(value:object)->bool: return _issued(value,Spec032GateDecision,_GATE_REGISTRY)
def issue_offline_executor_approval()->Spec032OfflineApproval: return _make(Spec032OfflineApproval)
def is_factory_issued_offline_approval(value:object)->bool: return _issued(value,Spec032OfflineApproval,_APPROVAL_REGISTRY)
def _clock_now()->float|None:
    try: now=_trusted_monotonic()
    except BaseException: return None
    return float(now) if type(now) in (int,float) and math.isfinite(float(now)) and now>=0 else None
def issue_spec032_attempt_lease(approval:object,scope:object)->Spec032AttemptLease|None:
    if scope is not Spec032Scope.OFFLINE_EXECUTOR_VALIDATION: return None
    with _LOCK:
        if not is_factory_issued_offline_approval(approval): return None
        now=_clock_now()
        if now is None: return None
        value=object.__new__(Spec032AttemptLease); token=object(); object.__setattr__(value,"_factory_token",token)
        _register(_LEASE_REGISTRY,value,token,_freeze(token),approval,scope,now+_LEASE_SECONDS,now,False)
        ref,tok,seals=_LEASE_REGISTRY[id(value)]
        _LEASE_REGISTRY[id(value)]=(ref,tok,seals,approval,scope,now+_LEASE_SECONDS,now,False)
        return value
def is_factory_issued_spec032_attempt_lease(value:object)->bool:
    if type(value) is not Spec032AttemptLease: return False
    state=_state(value,_fields(Spec032AttemptLease))
    with _LOCK: entry=_LEASE_REGISTRY.get(id(value))
    return bool(state is not None and entry is not None and entry[0]() is value and state["_factory_token"] is entry[1] and _matches(state["_factory_token"],entry[2][0]))
def _revoke_entry(lease:object,entry:tuple)->None: _LEASE_REGISTRY[id(lease)]=(*entry[:-1],True)
def revoke_spec032_attempt_lease(lease:object,approval:object,scope:object)->bool:
    with _LOCK:
        if scope is not Spec032Scope.OFFLINE_EXECUTOR_VALIDATION or not is_factory_issued_spec032_attempt_lease(lease): return False
        entry=_LEASE_REGISTRY.get(id(lease))
        if entry is None or entry[3] is not approval or entry[4] is not scope: return False
        _revoke_entry(lease,entry); return True
def consume_spec032_attempt_lease(lease:object,approval:object,scope:object)->bool:
    if scope is not Spec032Scope.OFFLINE_EXECUTOR_VALIDATION: return False
    with _LOCK:
        if not is_factory_issued_spec032_attempt_lease(lease): return False
        entry=_LEASE_REGISTRY.get(id(lease))
        if entry is None or entry[7] or entry[3] is not approval or entry[4] is not scope or not is_factory_issued_offline_approval(approval): return False
        now=_clock_now()
        if now is None or now<entry[6] or now>=entry[5]: _revoke_entry(lease,entry); return False
        _revoke_entry(lease,entry); return True
