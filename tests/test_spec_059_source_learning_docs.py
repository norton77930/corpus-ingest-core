"""SPEC059 governance and discoverability; no real host acceptance claim."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / 'specs/059-source-learning-reliability'


def test_package_is_complete_and_requirements_have_tasks():
    for name in ('spec.md', 'plan.md', 'research.md', 'data-model.md', 'quickstart.md',
                 'tasks.md', 'contracts/learning.md', 'checklists/requirements.md',
                 'checklists/reliability.md'):
        text = (FEATURE / name).read_text(encoding='utf-8')
        assert not re.search(r'\[NEEDS CLARIFICATION|\bTBD\b|\bTODO\b', text), name
    spec = (FEATURE / 'spec.md').read_text(encoding='utf-8')
    tasks = (FEATURE / 'tasks.md').read_text(encoding='utf-8')
    assert set(re.findall(r'FR-\d{3}', spec)) <= set(re.findall(r'FR-\d{3}', tasks))
    ids = re.findall(r'^- \[[ xX]\] (T\d{3}) ', tasks, re.MULTILINE)
    assert ids and len(ids) == len(set(ids))


def test_current_guides_route_to_spec059_and_separate_host_acceptance():
    for path in ('specs/README.md', 'docs/mcp-usage.md', 'docs/install-and-porting.md',
                 'docs/verification-matrix.md'):
        assert '059-source-learning-reliability' in (ROOT / path).read_text(encoding='utf-8'), path
    assert 'SPEC059' in (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    assert 'SPEC058' in (ROOT / 'AGENTS.md').read_text(encoding='utf-8')  # historical discovery
    guide = (FEATURE / 'quickstart.md').read_text(encoding='utf-8')
    assert 'Actual Hermes acceptance (separate, pending)' in guide
    assert '120000' in guide and 'does not retry' in guide
