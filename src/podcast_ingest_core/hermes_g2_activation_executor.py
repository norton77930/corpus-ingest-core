"""Pure Spec032 offline executor; no runtime adapter or Docker capability."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import threading
import weakref
from podcast_ingest_core import hermes_g2_activation_authority as authority
from podcast_ingest_core import hermes_g2_attempt_ledger as ledger
from podcast_ingest_core import hermes_g2_docker_commands as commands

class Spec032ExecutorStatus(str,Enum):
 BLOCKED_CREDENTIAL_SEAM="BLOCKED_CREDENTIAL_SEAM"; BLOCKED_INVALID_AUTHORITY="BLOCKED_INVALID_AUTHORITY"; BLOCKED_INVALID_DRIVER="BLOCKED_INVALID_DRIVER"; BLOCKED_LEASE="BLOCKED_LEASE"; BLOCKED_REPLAY="BLOCKED_REPLAY"; QUARANTINED_INDETERMINATE_ATTEMPT="QUARANTINED_INDETERMINATE_ATTEMPT"; QUARANTINED_MALFORMED_LEDGER="QUARANTINED_MALFORMED_LEDGER"; QUARANTINED_INACCESSIBLE_LEDGER="QUARANTINED_INACCESSIBLE_LEDGER"; BLOCKED_PRODUCTION_LEDGER_NOT_AUTHORIZED="BLOCKED_PRODUCTION_LEDGER_NOT_AUTHORIZED"; FAILED_ACTIVATION_QUARANTINED="FAILED_ACTIVATION_QUARANTINED"; FAILED_ROLLBACK_QUARANTINED="FAILED_ROLLBACK_QUARANTINED"; FAILED_LEDGER_TERMINALIZATION_QUARANTINED="FAILED_LEDGER_TERMINALIZATION_QUARANTINED"; PASS_OFFLINE_EXECUTOR_CONTRACT="PASS_OFFLINE_EXECUTOR_CONTRACT"
class Spec032DriverOperation(str,Enum): INSPECT="INSPECT"; ACTIVATE="ACTIVATE"; ROLLBACK="ROLLBACK"
class Spec032RollbackStatus(str,Enum): NOT_ATTEMPTED="NOT_ATTEMPTED"; PASS="PASS"; QUARANTINED="QUARANTINED"
@dataclass(frozen=True,init=False)
class Spec032DriverCommand:
 operation:Spec032DriverOperation; _factory_token:object
 def __init__(self,*_a:object,**_k:object)->None: raise TypeError("driver commands are factory-issued")
@dataclass(frozen=True,init=False)
class Spec032DriverObservation:
 operation:Spec032DriverOperation; ok:bool; metadata_status:commands.Spec032MetadataStatus|None; _factory_token:object
 def __init__(self,*_a:object,**_k:object)->None: raise TypeError("observations are factory-issued")
@dataclass(frozen=True,init=False)
class OfflineSyntheticDriver:
 _factory_token:object
 def __init__(self,*_a:object,**_k:object)->None: raise TypeError("use issue_offline_synthetic_driver()")
 def inspect_metadata(self,command:object)->Spec032DriverObservation: return _synthetic_call(self,command)
 def activate_once(self,command:object)->Spec032DriverObservation: return _synthetic_call(self,command)
 def rollback(self,command:object)->Spec032DriverObservation: return _synthetic_call(self,command)
@dataclass(frozen=True,init=False)
class Spec032ActualResult:
 status:Spec032ExecutorStatus; attempt_count:int; retry_count:int; driver_call_count:int; runtime_status:str; ledger_terminalized:bool; rollback_status:Spec032RollbackStatus; _factory_token:object
 def __init__(self,*_a:object,**_k:object)->None: raise TypeError("execute_spec032_offline_attempt() returns this result")
_LOCK=threading.RLock(); _REG:dict[str,dict[int,tuple]]={name:{} for name in("command","observation","driver","result")}
def _fields(cls:type)->tuple[str,...]: return tuple(cls.__annotations__)
def _state(value:object,fields:tuple[str,...])->dict[str,object]|None:
 try: state=vars(value)
 except BaseException: return None
 if type(state)is not dict or len(state)!=len(fields) or any(type(k)is not str for k in state): return None
 return state if all(any(k==f for f in fields) for k in state) else None
def _freeze(value:object)->object:
 if type(value)is bool:return("bool",value)
 if type(value)is int:return("int",value)
 if type(value)is str:return("str",value)
 return("identity",value)
def _match(value:object,seal:object)->bool:
 kind,expected=seal
 return (type(value)is bool and value is expected) if kind=="bool" else (type(value)is int and value==expected) if kind=="int" else (type(value)is str and value==expected) if kind=="str" else value is expected
def _register(kind:str,value:object,*facts:object)->None:
 token=vars(value)["_factory_token"]; key=id(value)
 def discard(ref:weakref.ReferenceType[object],*,key:int=key)->None:
  with _LOCK:
   entry=_REG[kind].get(key)
   if entry is not None and entry[0] is ref:_REG[kind].pop(key,None)
 _REG[kind][key]=(weakref.ref(value,discard),token,tuple(_freeze(vars(value)[f]) for f in _fields(type(value))),*facts)
def _make(kind:str,cls:type,**values:object)->object:
 value=object.__new__(cls)
 for name,item in values.items():object.__setattr__(value,name,item)
 object.__setattr__(value,"_factory_token",object()); _register(kind,value); return value
def _issued(kind:str,value:object,cls:type)->bool:
 if type(value)is not cls:return False
 state=_state(value,_fields(cls))
 with _LOCK:entry=_REG[kind].get(id(value))
 if state is None or entry is None or entry[0]() is not value or state.get("_factory_token") is not entry[1] or len(entry[2])!=len(_fields(cls)):return False
 try:return all(_match(state[n],s) for n,s in zip(_fields(cls),entry[2]))
 except BaseException:return False
def _command(operation:Spec032DriverOperation)->Spec032DriverCommand:return _make("command",Spec032DriverCommand,operation=operation)
def is_factory_issued_driver_command(value:object)->bool:return _issued("command",value,Spec032DriverCommand)
def _observation(operation:Spec032DriverOperation,ok:bool,metadata_status:commands.Spec032MetadataStatus|None)->Spec032DriverObservation:return _make("observation",Spec032DriverObservation,operation=operation,ok=ok,metadata_status=metadata_status)
def _valid_observation(value:object,operation:Spec032DriverOperation)->bool:return _issued("observation",value,Spec032DriverObservation) and value.operation is operation
def issue_offline_synthetic_driver(metadata_candidate:object,activate_ok:object,rollback_ok:object)->OfflineSyntheticDriver|None:
 if type(activate_ok)is not bool or type(rollback_ok)is not bool:return None
 parsed=commands.parse_bounded_metadata(metadata_candidate)
 if not commands.is_factory_issued_metadata_observation(parsed):return None
 value=_make("driver",OfflineSyntheticDriver)
 with _LOCK:
  entry=_REG["driver"][id(value)];_REG["driver"][id(value)]=(*entry,metadata_candidate,parsed,activate_ok,rollback_ok)
 return value
def is_factory_issued_offline_synthetic_driver(value:object)->bool:return _issued("driver",value,OfflineSyntheticDriver)
def _synthetic_call(driver:object,command:object)->Spec032DriverObservation:
 if not is_factory_issued_offline_synthetic_driver(driver) or not is_factory_issued_driver_command(command):return _observation(Spec032DriverOperation.INSPECT,False,None)
 with _LOCK: entry=_REG["driver"].get(id(driver))
 if entry is None:return _observation(Spec032DriverOperation.INSPECT,False,None)
 if command.operation is Spec032DriverOperation.INSPECT:return _observation(command.operation,entry[4].status is commands.Spec032MetadataStatus.PASS,entry[4].status)
 return _observation(command.operation,entry[5] if command.operation is Spec032DriverOperation.ACTIVATE else entry[6],None)
def _result(status:Spec032ExecutorStatus,attempts:int,calls:int,runtime:str,terminalized:bool=False,rollback:Spec032RollbackStatus=Spec032RollbackStatus.NOT_ATTEMPTED)->Spec032ActualResult:return _make("result",Spec032ActualResult,status=status,attempt_count=attempts,retry_count=0,driver_call_count=calls,runtime_status=runtime,ledger_terminalized=terminalized,rollback_status=rollback)
def is_factory_issued_spec032_actual_result(value:object)->bool:return _issued("result",value,Spec032ActualResult)
def _ledger_status(status:Spec032ExecutorStatus)->ledger.AttemptLedgerStatus:return ledger.AttemptLedgerStatus[status.name]
def project_blocked_production_gate(gate:object)->Spec032ActualResult:return _result(Spec032ExecutorStatus.BLOCKED_CREDENTIAL_SEAM if authority.is_factory_issued_spec032_gate(gate) and gate.status is authority.Spec032GateStatus.BLOCKED_CREDENTIAL_SEAM else Spec032ExecutorStatus.BLOCKED_INVALID_AUTHORITY,0,0,"not_run")
def execute_spec032_offline_attempt(approval:object,attempt_lease:object,attempt_ledger:object,driver:object)->Spec032ActualResult:
 if not authority.is_factory_issued_offline_approval(approval):return _result(Spec032ExecutorStatus.BLOCKED_INVALID_AUTHORITY,0,0,"not_run")
 if not is_factory_issued_offline_synthetic_driver(driver):
  authority.revoke_spec032_attempt_lease(attempt_lease,approval,authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION)
  return _result(Spec032ExecutorStatus.BLOCKED_INVALID_DRIVER,0,0,"not_run")
 if not authority.consume_spec032_attempt_lease(attempt_lease,approval,authority.Spec032Scope.OFFLINE_EXECUTOR_VALIDATION):return _result(Spec032ExecutorStatus.BLOCKED_LEASE,0,0,"not_run")
 claim=ledger.claim_attempt(attempt_ledger)
 if claim.status is not ledger.AttemptLedgerStatus.CLAIMED:return _result(Spec032ExecutorStatus[claim.status.name],0,0,"not_run")
 calls=0; terminal=Spec032ExecutorStatus.FAILED_ACTIVATION_QUARANTINED; rollback_status=Spec032RollbackStatus.NOT_ATTEMPTED; terminalized=False
 try:
  calls+=1; inspected=driver.inspect_metadata(_command(Spec032DriverOperation.INSPECT))
  if _valid_observation(inspected,Spec032DriverOperation.INSPECT) and inspected.metadata_status is commands.Spec032MetadataStatus.PASS:
   calls+=1; activated=driver.activate_once(_command(Spec032DriverOperation.ACTIVATE))
   if _valid_observation(activated,Spec032DriverOperation.ACTIVATE) and activated.ok is True:terminal=Spec032ExecutorStatus.PASS_OFFLINE_EXECUTOR_CONTRACT
 except BaseException:terminal=Spec032ExecutorStatus.FAILED_ACTIVATION_QUARANTED if False else Spec032ExecutorStatus.FAILED_ACTIVATION_QUARANTINED
 finally:
  try:
   calls+=1; rolled=driver.rollback(_command(Spec032DriverOperation.ROLLBACK)); rollback_status=Spec032RollbackStatus.PASS if _valid_observation(rolled,Spec032DriverOperation.ROLLBACK) and rolled.ok is True else Spec032RollbackStatus.QUARANTINED
  except BaseException:rollback_status=Spec032RollbackStatus.QUARANTINED
  if rollback_status is Spec032RollbackStatus.QUARANTINED:terminal=Spec032ExecutorStatus.FAILED_ROLLBACK_QUARANTINED
  try:
   finalized=ledger.terminalize_attempt(attempt_ledger,_ledger_status(terminal)); terminalized=finalized.status is _ledger_status(terminal)
  except BaseException:terminalized=False
  if not terminalized and terminal is not Spec032ExecutorStatus.FAILED_ROLLBACK_QUARANTINED:terminal=Spec032ExecutorStatus.FAILED_LEDGER_TERMINALIZATION_QUARANTINED
 return _result(terminal,1,calls,"offline_synthetic_driver",terminalized,rollback_status)
SAFE_SPEC032_RECEIPT_KEYS=frozenset({"schema_version","spec_id","status","terminal_status","attempt_count","retry_count","driver_call_count","runtime_status","ledger_terminalized","rollback_status","live_actions_authorized"})
def build_spec032_safe_receipt(result:object)->dict[str,str|int|bool]:
 if not is_factory_issued_spec032_actual_result(result):result=_result(Spec032ExecutorStatus.BLOCKED_INVALID_AUTHORITY,0,0,"not_run")
 return {"schema_version":"hermes-g2-spec032-receipt-v1","spec_id":"032-hermes-g2-offline-attempt-executor","status":result.status.value,"terminal_status":result.status.value,"attempt_count":result.attempt_count,"retry_count":result.retry_count,"driver_call_count":result.driver_call_count,"runtime_status":result.runtime_status,"ledger_terminalized":result.ledger_terminalized,"rollback_status":result.rollback_status.value,"live_actions_authorized":False}
