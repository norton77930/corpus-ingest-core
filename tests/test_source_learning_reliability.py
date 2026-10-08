"""Synthetic MCP seams and written host contract; never actual Hermes execution."""
from copy import deepcopy
import asyncio
import inspect
import json
from pathlib import Path, PurePosixPath

import pytest

from tests.test_source_content_query import prepared

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / '.agents/skills/source-content-qa'
ENTRY = ROOT / '.agents/skills/source-learning-entry'


def tool():
    from corpus_ingest_core.mcp_server import query_source_content
    return query_source_content


@pytest.mark.parametrize('extra', [{'limit': 1}, {'max_chars': 100}, {'cursor': 'bad'},
                                  {'expected_source_version': 'a' * 64}, {'query': 'word'}])
def test_inspect_diagnoses_only_accepted_identity_parameters(prepared, extra):
    prepared[1]()
    reply = tool()('show', 'EP1', **extra)
    assert reply['reason'] == 'invalid_request'
    assert 'inspect 只接受 podcast_id、episode_ref' in reply['message']
    assert 'segments' not in reply and 'Verification first.' not in json.dumps(reply)


def test_version_format_and_source_mismatch_are_distinct(prepared):
    prepared[1]()
    malformed = tool()('show', 'EP1', action='read', expected_source_version='a' * 63)
    assert malformed['reason'] == 'invalid_request'
    assert '64 lowercase hexadecimal' in malformed['message']
    mismatch = tool()('show', 'EP1', action='read', expected_source_version='a' * 64)
    assert mismatch['reason'] == 'source_changed'
    assert 'does not match the pinned version' in mismatch['message']
    assert 'stop' in mismatch['message'].lower()
    assert 'a' * 64 not in json.dumps(mismatch)


def test_cursor_format_and_binding_diagnoses_remain_bound(prepared):
    prepared[1]()
    version = tool()('show', 'EP1')['data']['source_version']
    base = dict(action='read', expected_source_version=version, limit=1)
    first = tool()('show', 'EP1', **base)['data']
    malformed = tool()('show', 'EP1', **base, cursor='%%%')
    assert malformed['reason'] == 'invalid_cursor'
    assert 'cursor format' in malformed['message'].lower()
    other_scope = tool()('show', 'EP1', **base, cursor=first['next_cursor'], start_seconds=1)
    assert other_scope['reason'] == 'invalid_cursor'
    assert 'query scope' in other_scope['message'].lower()
    assert first['next_cursor'] not in json.dumps(other_scope)


def test_diagnosis_never_echoes_arbitrary_or_incompatible_categories(prepared, monkeypatch):
    from corpus_ingest_core import source_content_query as core
    assert 'diagnosis' in inspect.signature(core.SourceContentError).parameters
    for reason, diagnosis in [('invalid_request', 'PRIVATE-DIAGNOSIS'),
                              ('source_missing', 'inspect_arguments')]:
        def fail(*args, **kwargs):
            raise core.SourceContentError(reason, diagnosis=diagnosis)
        monkeypatch.setattr(core, 'query_source_content', fail)
        reply = tool()('show', 'EP1')
        assert reply['reason'] == reason
        assert 'PRIVATE-DIAGNOSIS' not in json.dumps(reply)
        assert 'inspect 只接受' not in reply['message']


def recovery_contract(text):
    """Fail closed when a required written decision is removed or reversed."""
    for sentence in (
        'At most one recovery per explicit QA task, not per page.',
        'Only query_source_content with invalid_request or invalid_cursor caused by host parameters is eligible.',
        'A successfully pinned source_version is required; initial inspect failures stop.',
        'Reinspect with only podcast_id and episode_ref; no action, limit or max_chars.',
        'Require the same identity and the original pinned source_version.',
        'Retry only the unread request using the last successful next_cursor verbatim',
        'A second eligible error stops without another inspect and labels notes partial.',
        'Recovery inspection failure, source_changed, unsafe/missing source, malformed reply or transport failure stops without retry.',
        'Count the failed call, recovery inspect and retry against the remaining cumulative budget; never reset it.',
        'Preparation, download, transcription and study-guide tools never use this exception.',
        'Successfully recovered parameter errors do not by themselves make notes partial; complete coverage still requires all consecutive same-version chunks.',
    ):
        assert sentence in text, sentence


def test_recovery_contract_is_explicit_and_entry_exception_is_narrow():
    contract = (QA / 'references/response-contract.md').read_text(encoding='utf-8')
    recovery_contract(contract)
    skill = (QA / 'SKILL.md').read_text(encoding='utf-8')
    assert 'one page at a time' in skill and 'never parallel' in skill
    assert 'verbatim' in skill and 'source_version' in skill
    entry = (ENTRY / 'SKILL.md').read_text(encoding='utf-8')
    protocol = (ENTRY / 'references/entry-protocol.md').read_text(encoding='utf-8')
    assert 'sole retry exception' in entry and 'query_source_content' in entry
    assert 'source_changed stops' in contract and 'source_changed stops' in protocol
    assert 'restart inspection/retrieval' not in skill


def test_contract_guard_rejects_removal_of_stop_and_budget_rules():
    contract = (QA / 'references/response-contract.md').read_text(encoding='utf-8')
    recovery_contract(contract)
    for sentence in ('At most one recovery per explicit QA task, not per page.',
                     'Require the same identity and the original pinned source_version.',
                     'A second eligible error stops without another inspect and labels notes partial.',
                     'Preparation, download, transcription and study-guide tools never use this exception.'):
        with pytest.raises(AssertionError):
            recovery_contract(contract.replace(sentence, ''))


def scripted_host(faults, *, max_calls=30, before_reinspect=None):
    """Test-only interpretation oracle exercising real MCP, not shipped host code."""
    recovery_contract((QA / 'references/response-contract.md').read_text(encoding='utf-8'))
    from corpus_ingest_core.learning_mcp_acceptance import _metadata
    calls, evidence = [], []
    def call(arguments):
        calls.append(deepcopy(arguments))
        return tool()(**arguments)
    ids = dict(podcast_id='show', episode_ref='EP1')
    baseline = _metadata(call(ids)['data'], ids)
    pinned = baseline['source_version']
    request = dict(**ids, action='read', expected_source_version=pinned, limit=1, max_chars=10)
    used = False
    last_successful_response = None
    attempt = 0
    while len(calls) < max_calls:
        sent = deepcopy(request)
        fault = faults.get(attempt)
        attempt += 1
        if fault == 'cursor':
            sent['cursor'] = '%%%'
        elif fault == 'version':
            sent['expected_source_version'] = pinned[:-1]
        elif fault == 'changed':
            sent['expected_source_version'] = ('0' if pinned[0] != '0' else '1') + pinned[1:]
        reply = call(sent)
        if not reply['ok']:
            if reply['reason'] not in {'invalid_request', 'invalid_cursor'} or used or max_calls - len(calls) < 2:
                break
            used = True
            if before_reinspect is not None:
                before_reinspect()
            fresh = call(ids)
            if not fresh['ok']:
                break
            try:
                _metadata(fresh['data'], ids, pinned=baseline)
            except (ValueError, KeyError, TypeError):
                break
            # Freshly copy from the successful reply, never from the failed outgoing arguments.
            request['cursor'] = last_successful_response['next_cursor'] if last_successful_response else ''
            request['expected_source_version'] = (last_successful_response['source_version']
                                                  if last_successful_response else pinned)
            continue
        page = reply['data']
        _metadata(page, ids, page=True, pinned=baseline)
        last_successful_response = deepcopy(page)
        evidence.extend(page['segments'])
        if page['next_cursor'] is None:
            return dict(status='complete', calls=calls, evidence=evidence, recoveries=int(used))
        request['cursor'] = page['next_cursor']
        request['expected_source_version'] = page['source_version']
    return dict(status='partial', calls=calls, evidence=evidence, recoveries=int(used))


@pytest.mark.parametrize('fault', ['cursor', 'version'])
@pytest.mark.parametrize('at', [0, 2])
def test_one_parameter_recovery_reconstructs_exact_chunks_without_repeating(prepared, fault, at):
    _, payload = prepared[1]()
    result = scripted_host({at: fault})
    assert result['status'] == 'complete' and result['recoveries'] == 1
    for ordinal, segment in enumerate(payload['segments']):
        chunks = [s for s in result['evidence'] if s['ordinal'] == ordinal]
        assert ''.join(s['text'] for s in chunks) == segment['text']
        assert [s['text_offset'] for s in chunks] == list(range(0, len(segment['text']), 10))
    assert result['calls'][at + 2] == dict(podcast_id='show', episode_ref='EP1')
    if at and fault == 'cursor':
        assert result['calls'][at + 1]['cursor'] != result['calls'][at + 3]['cursor']
    assert sum('action' not in c for c in result['calls']) == 2


def test_second_error_stops_partial_without_second_inspect(prepared):
    prepared[1]()
    result = scripted_host({2: 'cursor', 3: 'version'})
    assert result['status'] == 'partial' and result['recoveries'] == 1
    assert len(result['calls']) == 6
    assert sum('action' not in c for c in result['calls']) == 2
    assert result['evidence'] and all(s['ordinal'] == 0 for s in result['evidence'])


def test_successful_recovery_does_not_reset_allowance_for_later_page(prepared):
    prepared[1]()
    result = scripted_host({1: 'cursor', 5: 'version'})
    assert result['status'] == 'partial' and result['recoveries'] == 1
    assert len(result['calls']) == 8
    assert sum('action' not in c for c in result['calls']) == 2
    assert any(s['ordinal'] == 1 for s in result['evidence'])


@pytest.mark.parametrize('fault', ['changed', 'missing', 'malformed', 'identity'])
def test_reinspection_drift_or_failure_stops_without_retry_read(prepared, monkeypatch, fault):
    paths, payload = prepared[1]()
    if fault in {'changed', 'missing'}:
        def before():
            if fault == 'missing':
                paths.json_path.unlink()  # owned synthetic fixture only
            else:
                payload['segments'][0]['text'] = 'changed synthetic fixture'
                paths.json_path.write_text(json.dumps(payload), encoding='utf-8')
    else:
        from corpus_ingest_core import mcp_server
        original = mcp_server.query_source_content
        def before():
            def altered(*args, **kwargs):
                reply = original(*args, **kwargs)
                if fault == 'identity':
                    reply['data']['episode_ref'] = 'other'
                else:
                    reply['data']['unexpected'] = 'not protocol authority'
                return reply
            monkeypatch.setattr(mcp_server, 'query_source_content', altered)
    result = scripted_host({2: 'cursor'}, before_reinspect=before)
    assert result['status'] == 'partial' and result['recoveries'] == 1
    assert len(result['calls']) == 5  # initial, two reads, error, recovery inspect
    assert 'action' not in result['calls'][-1]
    assert result['evidence']


def test_source_changed_and_budget_exhaustion_do_not_authorize_recovery(prepared):
    prepared[1]()
    changed = scripted_host({2: 'changed'})
    assert changed['status'] == 'partial' and changed['recoveries'] == 0
    assert len(changed['calls']) == 4
    bounded = scripted_host({2: 'cursor'}, max_calls=5)
    assert bounded['status'] == 'partial' and len(bounded['calls']) == 4
    assert bounded['recoveries'] == 0


def test_preparation_no_retry_written_contract_remains(prepared):
    protocol = (ENTRY / 'references/entry-protocol.md').read_text(encoding='utf-8')
    assert 'transport loss or outcome_unconfirmed stop without retry' in protocol
    assert 'confirm=true and expected_plan_id=preview.plan_id once.' in protocol
    assert 'No later tool call in this submission turn.' in protocol
    standalone = (ROOT / '.agents/skills/source-preparation/SKILL.md').read_text(encoding='utf-8')
    assert 'retry' in standalone and 'stop' in standalone


def test_entry_discovery_covers_learning_intents_and_local_first_choice():
    skill = (ENTRY / 'SKILL.md').read_text(encoding='utf-8')
    import yaml
    description = yaml.safe_load(skill.split('---', 2)[1])['description']
    assert len(description) <= 60
    for intent in ('YouTube', 'X', '學習', '本機', 'MCP'):
        assert intent in description, intent
    for intent in ('understanding', 'summary', 'questions', 'learning notes'):
        assert intent in skill, intent
    assert 'local MCP before' in skill and 'third-party transcripts' in skill
    assert 'ask the user to decide' in skill


def test_notes_quality_contract_preserves_examples_neutrality_and_requested_scope():
    template = (QA / 'references/learning-notes-template.md').read_text(encoding='utf-8')
    contract = (QA / 'references/response-contract.md').read_text(encoding='utf-8')
    for term in ('性別', '代名詞', '具體情境', '抽象結論', '未要求的段落', '獨立段落'):
        assert term in template, term
    for term in ('gender', 'concrete', 'unsolicited', 'separate labeled'):
        assert term in contract, term


def test_verifier_default_admits_long_synthetic_delivery_and_cli_matches():
    from corpus_ingest_core.learning_mcp_acceptance import verify_learning_session
    from tests.test_learning_mcp_acceptance import Session, metadata, page, segment
    version = metadata()['source_version']
    replies = [metadata()]
    for offset in range(0, 62000, 12000):
        length = min(12000, 62000 - offset)
        final = offset + length == 62000
        replies.append(page([segment(text='x' * length, offset=offset, complete=final)],
                            cursor=None if final else f'cursor-{offset}', complete=False))
    replies.append(metadata())
    session = Session(replies)
    result = asyncio.run(verify_learning_session(session, podcast_id='x-test', episode_ref='123',
                                                 start_seconds=29, end_seconds=40))
    assert result['ok'] and result['delivered_chars'] == 62000
    assert inspect.signature(verify_learning_session).parameters['max_total_chars'].default == 120000
    from corpus_ingest_core import learning_mcp_acceptance as core
    assert core.DEFAULT_MAX_TOTAL_CHARS == 120000
    from scripts.verify_learning_mcp import parse_args
    args = ['verify', '--data-dir', 'synthetic', '--podcast', 'x-test', '--episode', '123',
            '--start', '29', '--end', '40']
    assert parse_args(args).max_total_chars == core.DEFAULT_MAX_TOTAL_CHARS
    assert parse_args(args + ['--max-total-chars', '60000']).max_total_chars == 60000
    assert version == result['source_version']


def test_preview_fixture_is_portable_under_posix_semantics(monkeypatch):
    # Characterize Linux Path semantics on Windows; not a native Linux execution claim.
    from corpus_ingest_core import study_guide_bundle
    from tests.test_mcp_study_guide_bundle import test_preview_delegates_once_and_hides_ack
    monkeypatch.setattr(study_guide_bundle, 'Path', PurePosixPath)
    # A Windows path literal in this test must disappear, independently of host platform.
    test_preview_delegates_once_and_hides_ack(monkeypatch, PurePosixPath('/synthetic/lectures'))
