"""Skill/resource contracts and real backend seams; no live Hermes claim."""
import json
import re
from pathlib import Path

from tests.test_source_preparation import configured_source, transcript, URL

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/source-learning-entry/SKILL.md'
CASES = ROOT / 'tests/fixtures/source_learning_entry_cases.json'


def test_entry_resources_are_portable_and_dependencies_available():
    assert SKILL.is_file(), 'Unified source learning entry missing'
    text = SKILL.read_text(encoding='utf-8')
    assert text.startswith('---\nname: source-learning-entry\n')
    links = re.findall(r'\[[^\]]+\]\((references/[^)]+)\)', text)
    assert links, 'Entry protocol route missing'
    for relative in links:
        target = (SKILL.parent / relative).resolve()
        assert target.is_relative_to(SKILL.parent.resolve()) and target.is_file()
    for name, resources in (
        ('source-preparation', ('references/response-contract.md',)),
        ('source-content-qa', ('SKILL.md', 'references/response-contract.md',
                               'references/learning-notes-template.md')),
    ):
        assert name in text
        for resource in resources:
            assert (SKILL.parent.parent / name / resource).is_file()


def test_entry_contract_names_real_routes_and_distinct_stopping_conditions():
    text = SKILL.read_text(encoding='utf-8')
    reference = (SKILL.parent / 'references/entry-protocol.md').read_text(encoding='utf-8')
    combined = (text + reference).casefold()
    for requirement in ('prepare_learning_source', 'inspect_source_preparation_job',
                        'query_source_content', 'status-only', 'explicit continuation',
                        'busy', 'original', 'same conversation', 'outcome_unconfirmed'):
        assert requirement in combined, requirement


def assert_preparation_consent_and_stopping_contract(reference):
    """Guard critical written instructions, not a claim of host compliance."""
    approval, later = reference.split('## Later requests in the same conversation', 1)
    assert 'Wait for explicit fresh approval for this displayed plan.' in approval
    assert 'Denial stops, silence waits, conditional/ambiguous approval clarifies' in approval
    assert 'historical approval is not consent' in approval
    assert ('On that approval call prepare_learning_source with exact preview canonical_url, '
            'confirm=true and expected_plan_id=preview.plan_id once.') in approval
    assert 'transport loss or outcome_unconfirmed stop without retry' in approval
    assert 'No later tool call in this submission turn.' in approval
    status, continuation = later.split('is explicit continuation:', 1)
    assert 'is status-only: inspect one known job once' in status
    assert 'then stop even if ready' in status
    assert 'returned job_id, podcast_id and episode_ref must match the retained reference' in continuation
    assert 'never associate that job with this source' in approval


def test_entry_preserves_fresh_consent_exact_binding_and_stop_contract():
    reference = (SKILL.parent / 'references/entry-protocol.md').read_text(encoding='utf-8')
    assert_preparation_consent_and_stopping_contract(reference)


def test_consent_guard_rejects_removed_approval_and_confirmation_instructions():
    import pytest
    reference = (SKILL.parent / 'references/entry-protocol.md').read_text(encoding='utf-8')
    for instruction in (
        'Wait for explicit fresh approval for this displayed plan.',
        'On that approval call prepare_learning_source with exact preview canonical_url, '
        'confirm=true and expected_plan_id=preview.plan_id once.',
        'No later tool call in this submission turn.',
        'then stop even if ready',
    ):
        with pytest.raises(AssertionError):
            assert_preparation_consent_and_stopping_contract(reference.replace(instruction, ''))


def test_oracles_are_labelled_and_consent_status_paths_are_distinct():
    payload = json.loads(CASES.read_text(encoding='utf-8'))
    assert payload['evidence_kind'] == 'offline acceptance oracles; not agent execution'
    rows = payload['cases']
    assert len({row['id'] for row in rows}) == len(rows)
    cases = {row['id']: row for row in rows}
    assert cases['progress_ready']['expected_calls'] == ['status']
    assert cases['continue_ready']['expected_calls'] == ['status', 'inspect', 'read']
    assert cases['busy_other_source']['expected_calls'] == ['preview']
    for row in rows:
        assert set(row['expected_calls']) <= {'preview', 'confirm', 'status', 'inspect', 'read'}
        assert row['expected_calls'].count('confirm') <= 1
        if 'confirm' in row['expected_calls']:
            assert row['expected_calls'] == ['confirm'] and row['outcome'] == 'stop'
        if row['intent'] == 'status':
            assert row['expected_calls'] == ['status'] and row['outcome'] == 'stop'


def test_ready_handoff_keeps_legal_context_digest_and_input_bytes(configured_source):
    from corpus_ingest_core import mcp_server, source_preparation
    transcript()
    before = {p.relative_to(configured_source).as_posix(): p.read_bytes()
              for p in configured_source.rglob('*') if p.is_file()}
    preview = source_preparation.prepare_learning_source(URL)
    assert preview['status'] == 'transcript_ready'
    assert preview['plan_id'] is None and not preview['requires_confirmation']
    assert re.fullmatch('[a-f0-9]{64}', preview['context_digest'])
    assert 'learning_profile_incompatible' in preview['warnings']
    inspected = mcp_server.query_source_content(preview['podcast_id'], preview['episode_ref'])
    assert inspected['ok'] and inspected['data']['read_only']
    read = mcp_server.query_source_content(preview['podcast_id'], preview['episode_ref'],
        action='read', expected_source_version=inspected['data']['source_version'])
    assert read['ok'] and read['data']['segments'][0]['text'] == 'owned fixture'
    assert read['data']['coverage']['complete']
    after = {p.relative_to(configured_source).as_posix(): p.read_bytes()
             for p in configured_source.rglob('*') if p.is_file()}
    assert after == before


def test_preparation_ready_does_not_prove_source_readability(configured_source):
    from corpus_ingest_core import mcp_server, source_preparation
    paths = transcript()
    payload = json.loads(paths.json_path.read_text(encoding='utf-8'))
    payload.update(segments=[], segment_count=0)
    paths.json_path.write_text(json.dumps(payload), encoding='utf-8')
    before = paths.json_path.read_bytes()
    preview = source_preparation.prepare_learning_source(URL)
    assert preview['status'] == 'transcript_ready'
    result = mcp_server.query_source_content(preview['podcast_id'], preview['episode_ref'])
    assert not result['ok'] and result['reason'] == 'source_empty'
    assert paths.json_path.read_bytes() == before
    assert not (configured_source / 'preparation-jobs').exists()


def test_busy_job_is_not_owned_by_requested_preview(configured_source, monkeypatch):
    from corpus_ingest_core import source_preparation
    launches = []
    monkeypatch.setattr(source_preparation, 'launch_worker', lambda job: launches.append(job['job_id']))
    plan = source_preparation.prepare_learning_source(URL)
    accepted = source_preparation.prepare_learning_source(URL, confirm=True, expected_plan_id=plan['plan_id'])
    assert launches == [accepted['job_id']]
    other = source_preparation.prepare_learning_source('https://x.com/demo/status/987654321')
    assert other['status'] == 'busy' and other['job_id'] == accepted['job_id']
    assert other['episode_ref'] == '987654321'
    status = source_preparation.inspect_source_preparation_job(other['job_id'])
    assert status['episode_ref'] == '123456789' and status['episode_ref'] != other['episode_ref']
    assert 'canonical_url' not in status and 'source_type' not in status
    assert status['read_only'] and not status['network_access']
    assert launches == [accepted['job_id']]


def test_query_rechecks_version_after_ready_observation(configured_source):
    from corpus_ingest_core import mcp_server, source_preparation
    paths = transcript()
    assert source_preparation.prepare_learning_source(URL)['status'] == 'transcript_ready'
    inspected = mcp_server.query_source_content('x-demo', '123456789')['data']
    payload = json.loads(paths.json_path.read_text(encoding='utf-8'))
    payload['segments'][0]['text'] = 'changed fixture'
    paths.json_path.write_text(json.dumps(payload), encoding='utf-8')
    result = mcp_server.query_source_content('x-demo', '123456789', action='read',
        expected_source_version=inspected['source_version'])
    assert not result['ok'] and result['reason'] == 'source_changed'
    assert 'segments' not in result
