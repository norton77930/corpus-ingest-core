"""Discoverable planning and operator handoff for the source learning entry."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / 'specs/057-source-learning-entry-skill'


def test_feature_artifacts_are_complete_and_task_ids_are_unique():
    for name in ('spec.md', 'plan.md', 'research.md', 'data-model.md',
                 'quickstart.md', 'tasks.md', 'contracts/skill.md',
                 'checklists/requirements.md', 'checklists/interaction.md'):
        path = FEATURE / name
        assert path.is_file(), name
        assert not re.search(r'\[NEEDS CLARIFICATION|\bTBD\b|\bTODO\b', path.read_text(encoding='utf-8')), name
    tasks = (FEATURE / 'tasks.md').read_text(encoding='utf-8')
    ids = re.findall(r'^- \[[ xX]\] (T\d{3}) ', tasks, re.MULTILINE)
    assert ids and len(ids) == len(set(ids))


def test_all_requirements_have_traceable_tasks():
    spec = (FEATURE / 'spec.md').read_text(encoding='utf-8')
    tasks = (FEATURE / 'tasks.md').read_text(encoding='utf-8')
    requirements = set(re.findall(r'\*\*(FR-\d{3})\*\*:', spec))
    assert requirements
    assert requirements <= set(re.findall(r'FR-\d{3}', tasks))


def test_entry_is_discoverable_without_claiming_live_hermes_acceptance():
    assert '057-source-learning-entry-skill' in (ROOT / 'specs/README.md').read_text(encoding='utf-8')
    for name in ('docs/mcp-usage.md', 'docs/install-and-porting.md', '.agents/skills/README.md'):
        assert 'source-learning-entry' in (ROOT / name).read_text(encoding='utf-8'), name
    quickstart = (FEATURE / 'quickstart.md').read_text(encoding='utf-8')
    assert 'Actual Hermes acceptance' in quickstart
    assert 'pending' in quickstart
    assert 'worker_host_incompatible' in quickstart
