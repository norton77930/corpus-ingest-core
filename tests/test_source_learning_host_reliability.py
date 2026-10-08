"""SPEC060 real reader checks and written host contracts; not Hermes execution."""
import base64
import json
from pathlib import Path
import re
import struct

import pytest
import yaml

from tests.test_source_content_query import prepared, core, inspect, read, reason

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'
QA = SKILLS / 'source-content-qa'
ENTRY = SKILLS / 'source-learning-entry'


def legacy_cursor(metadata, index, offset=0, *, action='read', query='', start=None, end=None):
    binding = core()._binding(metadata, action, query, start, end)
    payload = json.dumps([binding, index, offset], separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip('=')


def test_compact_cursor_preserves_full_version_and_exact_split_delivery(prepared):
    text = 'concrete source example ' * 4
    prepared[1](segments=[dict(id=9, start=0, end=12, text=text),
                          dict(id=9, start=12, end=20, text='tail')])
    meta = inspect()
    assert re.fullmatch(r'[a-f0-9]{64}', meta['source_version'])
    cursor, chunks = '', []
    for _ in range(20):
        page = read(meta['source_version'], cursor=cursor, limit=1, max_chars=17)
        chunks.extend(page['segments'])
        assert page['source_version'] == meta['source_version']
        cursor = page['next_cursor']
        if cursor is None:
            break
        assert cursor.startswith('c1.') and len(cursor) == 57
    else:
        pytest.fail('continuation did not exhaust')
    assert ''.join(s['text'] for s in chunks if s['ordinal'] == 0) == text
    assert [s['text_offset'] for s in chunks if s['ordinal'] == 0] == list(range(0, len(text), 17))
    assert page['coverage']['scope_exhausted'] and not page['coverage']['complete']


def test_legacy_cursor_accepted_and_next_emission_upgraded(prepared):
    prepared[1]()
    meta = inspect()
    page = read(meta['source_version'], cursor=legacy_cursor(meta, 1), limit=1)
    assert [s['ordinal'] for s in page['segments']] == [1]
    assert page['next_cursor'].startswith('c1.') and len(page['next_cursor']) == 57
    final = read(meta['source_version'], cursor=page['next_cursor'])
    assert [s['ordinal'] for s in final['segments']] == [2]


@pytest.mark.parametrize('field', ['index', 'offset'])
def test_in_range_position_copy_error_rejected(prepared, field):
    prepared[1]()
    version = inspect()['source_version']
    cursor = read(version, max_chars=6)['next_cursor']
    assert cursor.startswith('c1.')
    payload = bytearray(base64.urlsafe_b64decode(cursor[3:] + '=='))
    payload[32:] = struct.pack('>II', 1, 6) if field == 'index' else struct.pack('>II', 0, 7)
    bad = 'c1.' + base64.urlsafe_b64encode(payload).decode().rstrip('=')
    reason('invalid_cursor', lambda: read(version, cursor=bad))


def test_each_single_character_copy_mutation_is_rejected(prepared):
    prepared[1]()
    meta = inspect()
    cursor = read(meta['source_version'], limit=1)['next_cursor']
    assert cursor.startswith('c1.')
    selected = [dict(text='long synthetic text') for _ in range(3)]
    binding = core()._binding(meta, 'read', '', None, None)
    for index, char in enumerate(cursor):
        changed = cursor[:index] + ('B' if char == 'A' else 'A') + cursor[index + 1:]
        reason('invalid_cursor', lambda: core()._decode(changed, binding, selected))
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    # Change only unused Base64 bits: decoded bytes stay identical, spelling must still be canonical.
    noncanonical = cursor[:-1] + alphabet[alphabet.index(cursor[-1]) | 1]
    assert noncanonical != cursor
    reason('invalid_cursor', lambda: core()._decode(noncanonical, binding, selected))


@pytest.mark.parametrize('options', [dict(action='search', query='Verification'),
                                   dict(start_seconds=1), dict(end_seconds=29)])
def test_short_cursor_stays_action_query_window_bound(prepared, options):
    prepared[1]()
    version = inspect()['source_version']
    cursor = read(version, limit=1)['next_cursor']
    reason('invalid_cursor', lambda: core().query_source_content(
        'show', 'EP1', expected_source_version=version, cursor=cursor, **dict(action='read') | options))


def test_short_search_cursor_positions_are_selection_indexes(prepared):
    prepared[1](segments=[dict(id=0, start=i, end=i + 1, text=t) for i, t in enumerate(
        ['skip', 'match first example', 'skip again', 'match second example'])])
    version = inspect()['source_version']
    first = core().query_source_content('show', 'EP1', action='search', query='match',
                                      expected_source_version=version, limit=1)
    assert first['next_cursor'].startswith('c1.')
    second = core().query_source_content('show', 'EP1', action='search', query='match',
                                       expected_source_version=version, cursor=first['next_cursor'])
    assert [s['ordinal'] for s in first['segments'] + second['segments']] == [1, 3]
    assert second['next_cursor'] is None
    assert not second['search']['full_source_understanding']


@pytest.mark.parametrize('cursor', ['c1.', 'c2.AAAA', 'c1.' + 'A' * 53,
                                   'c1.' + 'A' * 55, 'c1.' + '%' * 54, 'c1.' + 'A' * 54 + '='])
def test_unknown_or_malformed_short_tokens_have_safe_errors(prepared, cursor):
    prepared[1]()
    from corpus_ingest_core.mcp_server import query_source_content
    version = inspect()['source_version']
    reply = query_source_content('show', 'EP1', action='read', expected_source_version=version, cursor=cursor)
    assert reply['reason'] == 'invalid_cursor'
    assert 'segments' not in reply and cursor not in reply['message']


def test_short_cursor_identity_and_full_version_are_still_pinned(prepared):
    prepared[1]()
    prepared[1](episode='EP2')
    version = inspect()['source_version']
    cursor = read(version, limit=1)['next_cursor']
    other_version = core().query_source_content('show', 'EP2')['source_version']
    reason('invalid_cursor', lambda: core().query_source_content(
        'show', 'EP2', action='read', expected_source_version=other_version, cursor=cursor))
    reason('source_changed', lambda: read('a' * 64, cursor=cursor))


def test_short_cursor_cannot_continue_empty_selection(prepared):
    prepared[1]()
    meta = inspect()
    cursor = core()._encode(core()._binding(meta, 'search', 'absent', None, None), 0, 0)
    reason('invalid_cursor', lambda: core().query_source_content(
        'show', 'EP1', action='search', query='absent', expected_source_version=meta['source_version'], cursor=cursor))


def test_response_based_recovery_is_visible_and_rejects_bad_request_reuse():
    main = (QA / 'SKILL.md').read_text(encoding='utf-8')
    contract = (QA / 'references/response-contract.md').read_text(encoding='utf-8')
    for text in (main, contract):
        assert 'last successful tool response' in text
        assert 'failed request' in text
    assert 'freshly copy' in contract and 'once per explicit QA task' in contract


@pytest.mark.parametrize('fault', ['cursor', 'version'])
def test_recovery_retry_matches_successful_reply_not_failed_arguments(prepared, fault):
    from tests.test_source_learning_reliability import scripted_host
    prepared[1]()
    result = scripted_host({2: fault})
    assert result['status'] == 'complete' and result['recoveries'] == 1
    failed, retry = result['calls'][3], result['calls'][5]
    assert result['calls'][4] == dict(podcast_id='show', episode_ref='EP1')
    from corpus_ingest_core.mcp_server import query_source_content
    previous = query_source_content(**result['calls'][2])['data']
    assert retry['cursor'] == previous['next_cursor']
    assert retry['expected_source_version'] == previous['source_version']
    assert failed['cursor' if fault == 'cursor' else 'expected_source_version'] != retry[
        'cursor' if fault == 'cursor' else 'expected_source_version']


def visible_description(path):
    text = path.read_text(encoding='utf-8-sig')
    frontmatter = yaml.safe_load(text.split('---', 2)[1])
    description = str(frontmatter['description']).strip().strip("'\"")
    return description, description[:57] + '...' if len(description) > 60 else description


def test_all_skill_descriptions_fit_host_budget_and_entry_route_is_visible():
    purposes = {
        'corpus-episode-completion': ('episode', 'completion'),
        'corpus-latest-episode-processing': ('latest', 'episode'),
        'episode-verified-research-report': ('named', 'verified', 'report'),
        'historical-episode-verified-report-path': ('historical', 'verified', 'report'),
        'latest-episode-verified-research-report': ('latest', 'verified', 'report'),
        'learning-workflow-advance': ('learning', 'advance'),
        'source-content-qa': ('原文', '問答', '筆記'),
        'source-learning-entry': ('YouTube', 'X', '學習', '本機', 'MCP'),
        'source-preparation': ('YouTube', 'X', '轉錄', '預覽'),
        'study-guide-bundle': ('study guide', 'preview'),
        'workflow-derivation-bundle': ('workflow derivation', 'preview'),
        'x-video-ingest': ('X', 'ingest', 'preview'),
        'youtube-video-ingest': ('YouTube', 'ingest', 'preview'),
    }
    purposes.update({f'speckit-{name}': ('Spec Kit', term) for name, term in {
        'analyze': 'consistency', 'checklist': 'checklist', 'clarify': 'clarify',
        'constitution': 'principles', 'converge': 'unbuilt', 'implement': 'execute',
        'plan': 'technical', 'specify': 'requirements', 'tasks': 'tasks',
        'taskstoissues': 'GitHub issues',
    }.items()})
    too_long = []
    for path in sorted(SKILLS.glob('*/SKILL.md')):
        description, rendered = visible_description(path)
        if not 1 <= len(description) <= 60:
            too_long.append(path.parent.name)
        assert description.strip() and rendered.strip()
        for purpose in purposes[path.parent.name]:
            assert purpose in rendered, (path.parent.name, purpose)
    assert not too_long, too_long
    _, rendered = visible_description(ENTRY / 'SKILL.md')
    for key in ('YouTube', 'X', '學習', '本機', 'MCP'):
        assert key in rendered, key


def test_description_guard_detects_overlong_hidden_routing(tmp_path):
    path = tmp_path / 'SKILL.md'
    path.write_text('---\nname: example\ndescription: ' + 'x' * 60 + ' local MCP\n---\n', encoding='utf-8')
    description, rendered = visible_description(path)
    assert len(description) > 60 and len(rendered) == 60
    assert rendered == 'x' * 57 + '...' and 'MCP' not in rendered


@pytest.mark.parametrize('name,predicate', [
    ('corpus-episode-completion', '_has_completion_skill_metadata'),
    ('corpus-latest-episode-processing', '_has_latest_deterministic_skill_metadata'),
    ('latest-episode-verified-research-report', '_has_verified_research_report_skill_metadata'),
    ('episode-verified-research-report', '_has_episode_verified_research_report_skill_metadata'),
])
def test_setup_validator_recognizes_actual_compact_metadata(name, predicate):
    from scripts import validate_mcp_setup
    text = (SKILLS / name / 'SKILL.md').read_text(encoding='utf-8')
    check = getattr(validate_mcp_setup, predicate)
    assert check(text)
    assert not check(text.replace('description:', 'other-field:', 1))


def test_entry_first_source_call_and_blocked_user_choice_are_explicit():
    for name in ('SKILL.md', 'references/entry-protocol.md'):
        text = (ENTRY / name).read_text(encoding='utf-8')
        for term in ('first source-processing MCP call', 'confirm=false', 'x_search', 'web_search', 'web_extract'):
            assert term in text, (name, term)
        assert 'user choice' in text or 'ask the user to decide' in text


@pytest.mark.parametrize('name', ['source-learning-entry', 'source-content-qa', 'source-preparation'])
def test_foreground_and_progress_rules_do_not_ban_media_jobs(name):
    text = (SKILLS / name / 'SKILL.md').read_text(encoding='utf-8')
    for term in ('main conversation', 'delegate_task', 'background AI', '整理中', '已提交'):
        assert term in text, (name, term)
    assert 'server-managed' in text


def test_concept_questions_neutral_examples_and_preanswer_source_checks():
    text = (QA / 'SKILL.md').read_text(encoding='utf-8')
    for term in ('concept', 'retrieve', 'unrelated', '他', '她', '正例', '反例', 'Before answering',
                 'concrete', 'AI 補充', 'unsolicited'):
        assert term in text, term
    contract = (QA / 'references/response-contract.md').read_text(encoding='utf-8')
    assert 'Before answering' in contract and 'AI 補充' in contract
    template = (QA / 'references/learning-notes-template.md').read_text(encoding='utf-8')
    assert '回答前' in template and '概念' in template and 'AI 補充' in template


def test_default_cli_sdk_delivers_whole_long_synthetic_source(prepared, capsys):
    """Actual owned stdio SDK/CLI, not mocked Session or operator/Hermes acceptance."""
    root, write = prepared
    segments = [dict(id=17, start=i, end=i + 1,
                     text=f'Synthetic segment {i:04}: a concrete example about teamwork.')
                for i in range(1448)]
    segments[0]['text'] = 'Synthetic oversized source segment. ' * 420
    segments[-1]['end'] = segments[-1]['start']  # Include the final instant, not just [0,end).
    write(segments=segments)
    meta = inspect()
    expected_chars = sum(len(s['text']) for s in segments)
    assert 60000 < expected_chars < 120000
    from scripts.verify_learning_mcp import main
    argv = ['verify', '--data-dir', str(root.parent), '--podcast', 'show', '--episode', 'EP1',
            '--start', '0', '--end', str(meta['end_seconds'] + 1)]
    assert main(argv) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['ok'] and result['scope_complete']
    assert result['selected_segments'] == result['delivered_segments'] == meta['segment_count'] == 1448
    assert result['delivered_chars'] == expected_chars and result['source_version'] == meta['source_version']
    assert len(result['trace']) <= 20 and result['pages'] > 1
    assert result['host_acceptance'] == result['content_quality'] == 'not_evaluated'
    assert 'Synthetic oversized' not in json.dumps(result)
    assert not list(root.parent.rglob('*.sqlite3'))
