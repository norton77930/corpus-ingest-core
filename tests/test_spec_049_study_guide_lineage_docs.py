from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'specs/049-study-guide-lineage'
def test_artifacts_and_requirements_are_complete():
    for name in ('spec.md','plan.md','research.md','data-model.md','contracts/lineage.md','tasks.md','quickstart.md','checklists/requirements.md','checklists/safety.md','workflow-record.md'):
        assert (PACKAGE/name).is_file(),name
    spec=(PACKAGE/'spec.md').read_text(encoding='utf-8')
    tasks=(PACKAGE/'tasks.md').read_text(encoding='utf-8')
    assert set(re.findall(r'FR-\d{3}',spec))<=set(re.findall(r'FR-\d{3}',tasks))
    assert 'no backfill' in spec and 'Tool 27' in spec and 'semantic summary' in spec
    assert 'metadata_writes' in (PACKAGE/'contracts/lineage.md').read_text(encoding='utf-8')
def test_registry_entry():
    entry=next(line for line in (ROOT/'specs/README.md').read_text(encoding='utf-8').splitlines() if line.startswith('- `049-study-guide-lineage`'))
    assert ('Implementation in progress' in entry or 'Implemented' in entry) and '29' in entry
