from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'specs/058-learning-mcp-acceptance'


def test_acceptance_package_separates_delivery_quality_and_live_host():
    contract = (PACKAGE / 'contracts/verification.md').read_text(encoding='utf-8')
    guide = (PACKAGE / 'quickstart.md').read_text(encoding='utf-8')
    checks = (PACKAGE / 'content-acceptance.md').read_text(encoding='utf-8')
    for term in ('--data-dir', '--mcp-url', 'scope', 'SPEC057 T017/T018', 'worker_host_incompatible', 'fresh'):
        assert term in guide
    assert 'metadata' in contract and 'query_source_content' in contract
    for term in ('Q1', 'Q2', 'Q3', 'TDD', '米其林', 'Pending replay', 'AI', 'Pending Hermes'):
        assert term in checks


def test_acceptance_is_discoverable_without_new_tool_claim():
    for path in ('specs/README.md', 'docs/install-and-porting.md', 'docs/verification-matrix.md', 'docs/roadmap.md'):
        text = (ROOT / path).read_text(encoding='utf-8')
        assert '058-learning-mcp-acceptance' in text
    assert 'SPEC058' in (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
