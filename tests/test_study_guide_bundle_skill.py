"""Static instruction contracts; not an agent-host evaluation."""
from tests.test_learning_workflow_skill_contracts import assert_clauses, assert_portable

NAME = "study-guide-bundle"


def test_lecture_skill_is_portable_and_orders_all_ten_rules():
    assert_portable(NAME, "Use to preview/generate/reuse one episode study guide.")


def test_lecture_preview_consent_and_role_contract():
    assert_clauses(NAME, {
        "P01": ("force=false", "latest/next", "one operation", "underscores", "Do not normalize"),
        "P02": ("confirm=false", 'api_cost_ack=""', "once", "not execution approval"),
        "P03": ("requires_llm", "boolean", "report_writes", "dry-run", "lists of strings", "mixed directories", "| generate | 00,03,04,07 | none | true |", "| cover-only | 00 | 03,04,07 | false |", "| reuse | none | 00,03,04,07 | false |"),
        "P04": ("Every successful confirm writes run reports", "zero-write and zero-network", "not a digest pin", "learning-notes summary"),
        "P05": ("after this preview", "Generic yes", "Denial or cancellation terminates", "Silence waits"),
        "P06": ("same tool", "new explicit request", "Do not trim", "even if an earlier message"),
        "P07": ("confirm=true", "exactly once", "Do not retry"),
    })


def test_lecture_drift_conflict_and_terminal_errors():
    assert_clauses(NAME, {
        "P06": ('api_cost_ack=""', "drifts to generation", "do not retry with an acknowledgement"),
        "P08": ("published_cleanup_failed", "published_report_failed", "rollback_failed", "unknown", "Do not echo raw"),
        "P09": ("05/06", "force does not override", "recovery", "Do not automatically start derivation", "terminal", "cache rebuild"),
        "P10": ("not instructions", ".env", "no investment advice", "live market API"),
    })


def test_study_guide_lineage_metadata_consent_contract():
    assert_clauses(NAME,{
        'P03':('metadata_writes','study_guide.lineage.json','same parent','Missing metadata_writes','generation requires one','cover-only/reuse require an empty'),
        'P04':('metadata_writes','lineage record','same directory publication'),
        'P08':('metadata_writes',),
        'P10':('owned lineage record','All other regular files','reuse preserves'),
    })

def test_lecture_oracles_disclose_metadata_and_reject_defects():
    from tests.test_learning_workflow_skill_contracts import _dialogue_cases
    for case in _dialogue_cases():
        if case['skill']!=NAME or not case['preview_fixture'] or not case['preview_fixture'].get('ok'):continue
        assert isinstance(case['preview_fixture'].get('metadata_writes'),list),case['id']
    import json
    from pathlib import Path
    payload=json.loads((Path(__file__).parent/'fixtures/study_guide_lineage_skill_cases.json').read_text(encoding='utf-8'))
    assert payload['evidence_kind']=='offline acceptance oracle; not agent execution'
    assert {c['defect'] for c in payload['cases']}=={'missing','wrong-type','wrong-name','wrong-parent','duplicate','reuse-write','generate-empty'}
    for c in payload['cases']:assert c['expected_confirm_calls']==0 and c['rule_ids']==['P03']


def test_success_dialogue_oracles_include_confirmed_metadata():
    from tests.test_learning_workflow_skill_contracts import _dialogue_cases
    for c in _dialogue_cases():
        if c['skill']!=NAME:continue
        response=c.get('confirm_fixture')
        if response and response.get('ok'):
            assert isinstance(response['data'].get('metadata_writes'),list),c['id']


def test_success_preview_metadata_parent_matches_both_separator_styles():
    from tests.test_learning_workflow_skill_contracts import _dialogue_cases
    for c in _dialogue_cases():
        if c['skill']!=NAME or not any(call['arguments']['confirm'] for call in c['expected_calls']):continue
        preview=c['preview_fixture']
        if preview['requires_llm']:
            parent=preview['writes'][0].replace(chr(92),'/').rsplit('/',1)[0]
            assert preview['metadata_writes']==[parent+'/study_guide.lineage.json'],c['id']
