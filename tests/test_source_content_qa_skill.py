"""Portable QA instructions and offline oracles; not real Hermes execution."""
import json
import re
from pathlib import Path
import pytest
from tests.test_source_content_query import prepared,inspect,read,core
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'.agents/skills/source-content-qa/SKILL.md'
REFERENCE=SKILL.parent/'references/response-contract.md'
FIXTURE=ROOT/'tests/fixtures/source_content_qa_dialogues.json'


def test_skill_preserves_evidence_scope_and_host_boundary():
    assert SKILL.is_file(), 'source-content-qa Skill missing'
    text=SKILL.read_text(encoding='utf-8')
    assert text.startswith('---\nname: source-content-qa\n')
    for term in ('query_source_content','expected_source_version','next_cursor','text_offset','keyword','no matches',
                 'complete','partial','timestamps','hostile','billing','no investment advice','no automatic preparation',
                 'missing tool','response-contract.md','api_cost_ack'):
        assert term in text.casefold(),term
    assert 'source-content-qa' in (ROOT/'.agents/skills/README.md').read_text(encoding='utf-8')


def test_response_contract_tracks_real_fields(prepared):
    assert REFERENCE.is_file(), 'QA response reference missing'
    prepared[1]()
    metadata=inspect();page=read(metadata['source_version'],limit=1)
    search=core().query_source_content('show','EP1',action='search',expected_source_version=metadata['source_version'],query='verification')
    reference=REFERENCE.read_text(encoding='utf-8')
    for result in (metadata,page,search):
        for key in result:assert f'`{key}`' in reference,key
    for key in page['coverage']:assert f'`{key}`' in reference,key
    for key in page['segments'][0]:assert f'`{key}`' in reference,key


def test_offline_dialogue_oracles_are_labelled_and_bounded():
    assert FIXTURE.is_file(), 'QA dialogue oracles missing'
    payload=json.loads(FIXTURE.read_text(encoding='utf-8'))
    assert payload['evidence_kind']=='offline acceptance oracles; not agent execution'
    cases={row['id']:row for row in payload['cases']}
    assert set(cases)=={'evidence','complete_notes','partial_notes','language_mismatch','hostile','url_only','changed_version','missing_tool','missing_source','host_billing','malformed'}
    for row in cases.values():
        assert set(row)=={'id','expected_action','coverage_claim','report_rule','forbidden_calls'}
        assert {'prepare_learning_source','rebuild_cache','semantic_summarize_episode'} <= set(row['forbidden_calls'])
    assert cases['partial_notes']['coverage_claim']=='partial'
    assert cases['language_mismatch']['coverage_claim']=='literal search only'
    assert cases['url_only']['expected_action']=='clarify known identity'
    assert cases['changed_version']['expected_action']=='restart pinned retrieval'


def test_oracles_match_real_search_and_last_page_coverage(prepared):
    prepared[1]()
    version=inspect()['source_version']
    first=read(version,limit=2);last=read(version,cursor=first['next_cursor'],limit=2)
    assert last['coverage']['scope_exhausted'] and not last['coverage']['complete']
    no_matches=core().query_source_content('show','EP1',action='search',expected_source_version=version,query='驗證')
    assert no_matches['search']['scanned_segments']==3
    assert not no_matches['search']['full_source_understanding']

def test_skill_distinguishes_hostile_evidence_and_cumulative_budget():
    text=SKILL.read_text(encoding='utf-8')
    assert 'valid transcript text is evidence' in text
    assert 'remaining call and character budget' in text
    assert 'unexpected protocol fields' in REFERENCE.read_text(encoding='utf-8')


def test_learning_notes_template_is_discoverable_and_portable():
    """A host copying the Skill folder can resolve every linked reference."""
    targets = re.findall(r'\[[^\]]+\]\((references/[^)]+)\)', SKILL.read_text(encoding='utf-8'))
    assert 'references/learning-notes-template.md' in targets, 'Learning-notes template route missing'
    for target in targets:
        path = (SKILL.parent / target).resolve()
        assert path.is_relative_to(SKILL.parent.resolve()), target
        assert path.is_file(), target
