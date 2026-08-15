"""Emit only sealed static Spec030 evidence; no runtime mode exists."""
from __future__ import annotations
import json,sys
from podcast_ingest_core.hermes_g1r_offline_remediation import build_g1r_offline_remediation_evidence,evaluate_g1r_offline_remediation
from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_OPERATION_ORDER,REQUIRED_TMPFS_ROLES,ControllerPlanFacts,ControllerStaticAdapter,CredentialBindingKind,G1RBaselineRollbackIntentFacts,G1RRollbackPlanFacts,InputMode,LogSink,build_controller_command_plan,issue_g1r_owner_ledger,issue_opaque_credential_reference
from podcast_ingest_core.hermes_runtime_deployment import BaselineOverlayFacts,evaluate_offline_overlay_preflight
from podcast_ingest_core.hermes_runtime_source_contract import evaluate_pinned_runtime_contract
_MODE=("offline-remediation-plan",); _REJECTED={"status":"rejected","runtime_observation_status":"not_run","g2_authorized":False,"g3a_authorized":False,"live_actions_authorized":False,"raw_persisted":False,"raw_persisted_scope":"safe_evidence_projection_only"}
def _plan():
 s=evaluate_pinned_runtime_contract(); p=evaluate_offline_overlay_preflight(BaselineOverlayFacts("sha256:"+"a"*64,True,True,True,True,True,True,True),s); l=issue_g1r_owner_ledger("spec030-controller"); r=issue_opaque_credential_reference(l,ControllerStaticAdapter.HERMES_PROVIDER_BINDING); b=G1RBaselineRollbackIntentFacts(True,True,True,True,True); return build_controller_command_plan(ControllerPlanFacts(s,p,l,r,REQUIRED_OPERATION_ORDER,REQUIRED_TMPFS_ROLES,InputMode.ONE_SHOT_STDIN,LogSink.NONE,CredentialBindingKind.READ_ONLY_REFERENCE,True,True,True,True,0,0,0,True,True,True,G1RRollbackPlanFacts(b,True,True,True,True,True,True)))
def main(argv=None):
 if tuple(sys.argv[1:] if argv is None else argv)!=_MODE: print(json.dumps(_REJECTED,sort_keys=True)); return 2
 print(json.dumps(build_g1r_offline_remediation_evidence(evaluate_g1r_offline_remediation(_plan())),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
