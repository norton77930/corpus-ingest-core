from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'specs/050-learning-bundle-recovery'
def test_planning_and_scope_are_complete():
    for name in ('spec.md','plan.md','research.md','data-model.md','contracts/recovery.md','tasks.md','quickstart.md','checklists/requirements.md','checklists/safety.md','workflow-record.md'):
        assert (PACKAGE/name).is_file(),name
    spec=(PACKAGE/'spec.md').read_text(encoding='utf-8')
    tasks=(PACKAGE/'tasks.md').read_text(encoding='utf-8')
    assert set(re.findall(r'FR-\d{3}',spec))<=set(re.findall(r'FR-\d{3}',tasks))
    for phrase in ('publication_outcome_not_proven','no automatic repair','no cleanup commands','Tools1-29'):assert phrase.casefold() in spec.casefold()
    assert 'manual_review_required' in (PACKAGE/'contracts/recovery.md').read_text(encoding='utf-8')
def test_registry_tracks_phase050():
    entry=next(line for line in (ROOT/'specs/README.md').read_text(encoding='utf-8').splitlines() if line.startswith('- `050-learning-bundle-recovery`'))
    assert ('Implementation in progress' in entry or 'Implemented' in entry) and '30' in entry
