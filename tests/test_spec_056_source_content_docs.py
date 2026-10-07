"""SPEC056 planning contracts, not runtime or live Hermes acceptance."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "specs/056-source-content-query"


def test_planning_package_has_artifacts_and_traceable_requirements():
    for name in ("spec.md", "plan.md", "research.md", "data-model.md", "quickstart.md", "tasks.md",
                 "workflow-record.md", "contracts/mcp.md", "contracts/skill.md",
                 "checklists/requirements.md", "checklists/safety.md"):
        assert (PACKAGE / name).is_file(), name
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    tasks = (PACKAGE / "tasks.md").read_text(encoding="utf-8")
    requirements = set(re.findall(r"FR-\d{3}|SC-\d{3}", spec))
    assert len(requirements) >= 17
    assert requirements <= set(re.findall(r"FR-\d{3}|SC-\d{3}", tasks))
    ids = re.findall(r"^- \[[ x]\] (T\d{3})", tasks, re.M)
    assert ids and len(ids) == len(set(ids))
    for name in ("spec.md", "plan.md", "tasks.md"):
        text = (PACKAGE / name).read_text(encoding="utf-8")
        for marker in ("NEEDS CLARIFICATION", "[FEATURE NAME]", "TBD"):
            assert marker not in text


def test_content_contract_has_versions_coverage_and_closed_boundaries():
    contract = (PACKAGE / "contracts/mcp.md").read_text(encoding="utf-8")
    for term in ("inspect", "read", "search", "podcast_id", "episode_ref", "expected_source_version",
                 "coverage", "35", "no automatic rebuild", "no provider"):
        assert term in contract, term
    skill = (PACKAGE / "contracts/skill.md").read_text(encoding="utf-8")
    for term in ("Hermes", "keyword", "no matches", "complete", "timestamps", "hostile", "billing"):
        assert term in skill, term
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    for term in ("RSS", "YouTube", "X", "single source", "not all video platforms", "planned", "2106893534980685927"):
        assert term in spec, term
    assert PACKAGE.name in (ROOT / "specs/README.md").read_text(encoding="utf-8")
