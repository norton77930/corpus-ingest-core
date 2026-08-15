"""Pure closed Spec032 operation and bounded metadata definitions.

No image, argv, environment, path, mount, or executable adapter is present.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import threading
import weakref
from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES
class Spec032DockerOperation(str,Enum): INSPECT_METADATA="INSPECT_METADATA"; ACTIVATE_ONCE="ACTIVATE_ONCE"; ROLLBACK="ROLLBACK"
class Spec032MetadataStatus(str,Enum): PASS="PASS"; QUARANTINED="QUARANTINED"
@dataclass(frozen=True,init=False)
class Spec032DockerCommand:
 operation:Spec032DockerOperation;_factory_token:object
 def __init__(self,*_a:object,**_k:object)->None:raise TypeError("use build_closed_docker_command()")
@dataclass(frozen=True,init=False)
class Spec032BoundedMetadataCandidate:
 _factory_token:object
 def __init__(self,*_a:object,**_k:object)->None:raise TypeError("use issue_bounded_metadata_candidate()")
@dataclass(frozen=True,init=False)
class Spec032MetadataObservation:
 status:Spec032MetadataStatus;_factory_token:object
 def __init__(self,*_a:object,**_k:object)->None:raise TypeError("metadata observations are factory-issued")
_LOCK=threading.RLock();_REG:dict[str,dict[int,tuple]]={kind:{} for kind in("command","candidate","observation")}
def _new(cls:type,**fields:object)->object:
 item=object.__new__(cls)
 for n,v in fields.items():object.__setattr__(item,n,v)
 object.__setattr__(item,"_factory_token",object());return item
def _register(kind:str,item:object,*facts:object)->None:
 key=id(item);token=vars(item)["_factory_token"]
 def discard(ref:weakref.ReferenceType[object],*,key:int=key)->None:
  with _LOCK:
   current=_REG[kind].get(key)
   if current is not None and current[0]is ref:_REG[kind].pop(key,None)
 _REG[kind][key]=(weakref.ref(item,discard),token,*facts)
def _issued(kind:str,item:object,cls:type)->bool:
 if type(item)is not cls:return False
 try:state=vars(item)
 except BaseException:return False
 fields=tuple(cls.__annotations__)
 if type(state)is not dict or len(state)!=len(fields):return False
 token=None
 for index,(key,value) in enumerate(state.items()):
  if type(key)is not str or key!=fields[index]:return False
  if key=="_factory_token":token=value
 if token is None:return False
 with _LOCK:entry=_REG[kind].get(id(item))
 return bool(entry is not None and entry[0]()is item and token is entry[1])
def build_closed_docker_command(operation:object)->Spec032DockerCommand|None:
 if type(operation)is not Spec032DockerOperation:return None
 with _LOCK:
  item=_new(Spec032DockerCommand,operation=operation);_register("command",item,operation);return item
def is_factory_issued_closed_docker_command(value: object) -> bool:
 if not _issued("command", value, Spec032DockerCommand): return False
 with _LOCK: entry = _REG["command"].get(id(value))
 try: return bool(entry is not None and value.operation is entry[2])
 except BaseException: return False

def issue_bounded_metadata_candidate(*facts:object)->Spec032BoundedMetadataCandidate|None:
 if len(facts)!=14 or type(facts[1])is not frozenset:return None
 if any(type(facts[i])is not bool for i in (0,5,6,7,8,9,10)) or any(type(facts[i])is not int for i in (2,3,4,11,12,13)):return None
 if any(type(item) is not type(next(iter(REQUIRED_TMPFS_ROLES))) for item in facts[1]):return None
 with _LOCK:
  item=_new(Spec032BoundedMetadataCandidate);_register("candidate",item,tuple(facts));return item
def _observation(status:Spec032MetadataStatus)->Spec032MetadataObservation:
 with _LOCK:
  item=_new(Spec032MetadataObservation,status=status);_register("observation",item,status);return item
def is_factory_issued_metadata_observation(value:object)->bool:
 if not _issued("observation",value,Spec032MetadataObservation):return False
 with _LOCK:entry=_REG["observation"].get(id(value))
 return bool(entry is not None and value.status is entry[2])
def parse_bounded_metadata(candidate:object)->Spec032MetadataObservation:
 if not _issued("candidate",candidate,Spec032BoundedMetadataCandidate):return _observation(Spec032MetadataStatus.QUARANTINED)
 with _LOCK:entry=_REG["candidate"].get(id(candidate));facts=entry[2] if entry else None
 if type(facts)is not tuple:return _observation(Spec032MetadataStatus.QUARANTINED)
 try:complete=facts[0]is True and facts[1]==REQUIRED_TMPFS_ROLES and all(facts[i]==0 for i in (2,3,4,11,12,13)) and all(facts[i]is True for i in (5,6,7,8,9,10))
 except BaseException:complete=False
 return _observation(Spec032MetadataStatus.PASS if complete else Spec032MetadataStatus.QUARANTINED)
