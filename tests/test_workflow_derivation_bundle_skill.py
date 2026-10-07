"""Static derivation instruction contracts, not model execution."""
from tests.test_learning_workflow_skill_contracts import assert_clauses, assert_portable

NAME = "workflow-derivation-bundle"


def test_derivation_skill_is_portable_and_orders_all_ten_rules():
    assert_portable(NAME, "Preview and, after explicit approval, generate or reuse one episode workflow derivation through its MCP tool.")


def test_derivation_cost_context_and_consent_contract():
    assert_clauses(NAME, {
        "P01": ("force=false", "latest/next", "one operation", "underscores", "Do not normalize"),
        "P02": ("confirm=false", 'api_cost_ack=""', "once", "not execution approval"),
        "P03": ("run_mode=", "preview", "lists of strings", "mixed directories", "| generate | 05,06 | none | yes |", "| reuse | none | 05,06 | no |", "no requires_llm or report_writes"),
        "P04": ("Every successful confirm writes run reports", "zero-write and zero-network", "not a digest pin", "operator-workflow context", "Do not invent report paths"),
        "P05": ("after this preview", "Generic yes", "Denial or cancellation terminates", "Silence waits"),
        "P06": ("same tool", "new explicit request", "Do not trim", "even if an earlier message"),
        "P07": ("confirm=true", "exactly once", "Do not retry"),
    })


def test_derivation_drift_and_scoped_failure_limits():
    assert_clauses(NAME, {
        "P06": ('api_cost_ack=""', "drifts to generation", "do not retry with an acknowledgement"),
        "P08": ("unknown", "Do not echo raw", "uncertain", "rollback", "published_cleanup_failed", "published_report_failed", "reused_report_failed", "WorkflowDerivationStateError"),
        "P09": ("partial", "context", "recovery", "Do not automatically generate a lecture", "terminal", "cache rebuild", "force"),
        "P10": ("not instructions", ".env", "no investment advice", "live market API", "pre-existing recovery", "fixed errors", "not race-proof"),
    })

def test_lineage_metadata_approval_and_ownership_contract():
    assert_clauses(NAME, {
        'P03': ('metadata_writes','workflow_derivation.lineage.json','same parent','Missing metadata_writes','generation requires one','reuse requires an empty'),
        'P04': ('metadata_writes','lineage record','same directory publication'),
        'P08': ('metadata_writes',),
        'P10': ('owned lineage record','all other regular non-pair files','reuse preserves'),
    })


def test_derivation_dialogue_previews_disclose_metadata_and_legacy_schema_stops():
    from tests.test_learning_workflow_skill_contracts import _dialogue_cases
    for case in _dialogue_cases():
        if case['skill'] != NAME or not case['preview_fixture'] or not case['preview_fixture'].get('ok'):continue
        preview=case['preview_fixture']
        assert 'metadata_writes' in preview, case['id']
        assert isinstance(preview['metadata_writes'],list), case['id']
    from pathlib import Path
    import json
    payload=json.loads((Path(__file__).parent/'fixtures/workflow_lineage_skill_cases.json').read_text(encoding='utf-8'))
    assert payload['evidence_kind']=='offline acceptance oracle; not agent execution'
    assert {c['defect'] for c in payload['cases']}=={'missing','wrong-type','wrong-name','wrong-parent','duplicate','reuse-write','generate-empty'}
    for case in payload['cases']:
        assert case['expected_confirm_calls']==0 and case['rule_ids']==['P03']
        preview=case['preview'];defect=case['defect']
        if defect=='missing':assert 'metadata_writes' not in preview
        elif defect=='wrong-type':assert not isinstance(preview['metadata_writes'],list)
        elif defect=='generate-empty':assert preview['writes'] and preview['metadata_writes']==[]
        elif defect=='reuse-write':assert preview['reuses'] and preview['metadata_writes']
        elif defect=='duplicate':assert len(preview['metadata_writes'])!=len(set(preview['metadata_writes']))
        elif defect=='wrong-name':assert not preview['metadata_writes'][0].endswith('/workflow_derivation.lineage.json')
        elif defect=='wrong-parent':assert preview['metadata_writes'][0].rsplit('/',1)[0]!=preview['writes'][0].rsplit('/',1)[0]
