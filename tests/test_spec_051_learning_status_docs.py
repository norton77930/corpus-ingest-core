from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'specs/051-learning-workflow-status'

def test_spec_package_and_requirement_mapping():
    for name in ('spec.md','plan.md','research.md','data-model.md','contracts/status.md','tasks.md','quickstart.md','checklists/requirements.md','checklists/safety.md','workflow-record.md'):
        assert (PACKAGE/name).is_file(),name
    spec=(PACKAGE/'spec.md').read_text(encoding='utf-8');tasks=(PACKAGE/'tasks.md').read_text(encoding='utf-8')
    assert set(re.findall(r'FR-\d{3}',spec))<=set(re.findall(r'FR-\d{3}',tasks))
    for phrase in ['non_atomic_observation','summary_transcript_freshness_not_evaluated','no execution authorization','Tools1-30']:
        assert phrase in spec

def test_registry_tracks_spec051():
    entries=[l for l in (ROOT/'specs/README.md').read_text(encoding='utf-8').splitlines() if l.startswith('- `051-learning-workflow-status`')]
    assert len(entries)==1 and '31' in entries[0]
    assert 'Implementation in progress' in entries[0] or 'Implemented' in entries[0]
