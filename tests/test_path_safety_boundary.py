"""Boundary guard: path-safety structure is single-sourced in path_safety.py.

Static-scan guard in the style of tests/test_llm_provider_factory_boundary.py
(specs/025-core-consolidation FR-003 / FR-010):

1. The structural regex constants (URI scheme / safe filename / safe path
   component) may be defined via ``re.compile`` assignment only in
   ``src/podcast_ingest_core/path_safety.py``.
2. Every ``_is_safe_local_path`` definition in ``src`` must be a thin wrapper:
   it references ``is_safe_local_path_structure`` and contains no ``re.split``
   reimplementation of the skeleton.
3. Exactly four wrapper modules exist today; a fifth copy must be a conscious,
   reviewed decision (update this count deliberately).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "podcast_ingest_core"

STRUCTURAL_PATTERN_DEFINITION = re.compile(
    r"_?(?:URI_SCHEME|SAFE_FILENAME|SAFE_PATH_COMPONENT)_PATTERN\s*=\s*re\.compile"
)

EXPECTED_WRAPPER_MODULES = {
    "corpus_episode_completion_workflow_runner.py",
    "corpus_episode_workflow_runner.py",
    "corpus_latest_episode_deterministic_workflow_runner.py",
    "corpus_semantic_remediation_runner.py",
}


def test_structural_patterns_are_defined_only_in_path_safety():
    offenders = []
    for path in sorted(SRC_DIR.glob("*.py")):
        if path.name == "path_safety.py":
            continue
        if STRUCTURAL_PATTERN_DEFINITION.search(path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    assert not offenders, (
        "structural path-safety patterns must live only in path_safety.py; "
        f"found re.compile definitions in: {offenders}"
    )


def test_is_safe_local_path_definitions_are_thin_wrappers():
    wrapper_modules = set()
    for path in sorted(SRC_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "def _is_safe_local_path" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == "_is_safe_local_path"
            ):
                segment = ast.get_source_segment(text, node) or ""
                assert "is_safe_local_path_structure(" in segment, (
                    f"{path.name}: _is_safe_local_path must delegate to "
                    "path_safety.is_safe_local_path_structure"
                )
                assert "re.split(" not in segment, (
                    f"{path.name}: _is_safe_local_path must not reimplement "
                    "the structural skeleton"
                )
                wrapper_modules.add(path.name)
    assert wrapper_modules == EXPECTED_WRAPPER_MODULES, (
        "wrapper module set changed — update deliberately: "
        f"{sorted(wrapper_modules)}"
    )
