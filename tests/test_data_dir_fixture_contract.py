"""Guard contracts for the shared data-dir fixture and injectable data root.

Protected invariants (specs/025-core-consolidation FR-008):

1. Reflection in ``tests/conftest.py`` covers every ``storage`` ``*_DIR``
   constant, so a future directory addition is patched automatically.
2. The evals reports-dir bypass bindings stay importable under their known
   module/attribute names; a rename must fail here, in one place.
3. ``CORPUS_INGEST_DATA_DIR`` overrides ``storage.DATA_DIR`` at import time;
   with the variable unset the value stays the historical ``Path("data")``.
   The pre-rename ``PODCAST_INGEST_DATA_DIR`` spelling still works, so a
   machine configured before 0.2.0 does not silently fall back to ``data/``.
4. The copy-pasted ``_use_tmp_data_dirs`` helper is frozen to the allowlist
   below: migrated files may drop it, new test files must use the shared
   fixture instead.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from corpus_ingest_core.local_env_names import (
    CONFIG_ENV,
    DATA_DIR_ENV,
    DEPRECATED_ALIASES,
)
from corpus_ingest_core.local_env_names import (
    names_for as _names,
)
from tests import conftest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"

KNOWN_STORAGE_DIR_CONSTANTS = {
    "DATA_DIR",
    "AUDIO_DIR",
    "TRANSCRIPTS_DIR",
    "SUMMARIES_DIR",
    "MENTIONS_DIR",
    "REPORTS_DIR",
    "MAPPINGS_DIR",
    "EXTERNAL_DIR",
    "STOCK_LENS_DIR",
    "CACHE_DIR",
    "CORPUS_DIR",
    "RESEARCH_REPORTS_DIR",
    "STUDY_GUIDES_DIR",
}

HELPER_COPY_ALLOWLIST = {
    "test_cache.py",
    "test_corpus_audio_download_runner.py",
    "test_corpus_episode_completion_workflow_runner.py",
    "test_corpus_episode_intake.py",
    "test_corpus_episode_workflow_runner.py",
    "test_corpus_local_transcription_runner.py",
    "test_corpus_remediation_plan.py",
    "test_corpus_remediation_runner.py",
    "test_corpus_semantic_remediation_runner.py",
    "test_entity_extractor.py",
    "test_episode_intelligence.py",
    "test_external_data_boundary.py",
    "test_external_data_verification.py",
    "test_industry_mapping.py",
    "test_research_workflow.py",
    "test_semantic_summarizer.py",
    "test_stock_lens_report.py",
    "test_stock_lens_synthesis.py",
}


def test_reflection_covers_known_storage_dir_constants():
    names = set(conftest.storage_dir_constant_names())
    missing = KNOWN_STORAGE_DIR_CONSTANTS - names
    assert not missing, f"reflection lost storage dir constants: {sorted(missing)}"


def test_evals_reports_dir_bindings_exist_as_paths():
    for module_name, attribute in conftest.EVALS_REPORTS_DIR_BINDINGS:
        module = importlib.import_module(module_name)
        value = getattr(module, attribute)
        assert isinstance(value, Path), f"{module_name}.{attribute} is not a Path"


def test_fixture_redirects_every_storage_dir(tmp_data_dirs):
    from corpus_ingest_core import storage

    root = tmp_data_dirs
    for name in conftest.storage_dir_constant_names():
        value = getattr(storage, name)
        assert value == root or root in value.parents, (
            f"storage.{name} escaped the tmp root: {value}"
        )
    for module_name, attribute in conftest.EVALS_REPORTS_DIR_BINDINGS:
        module = importlib.import_module(module_name)
        value = getattr(module, attribute)
        assert root in value.parents, (
            f"{module_name}.{attribute} escaped the tmp root: {value}"
        )


def _data_dir_in_subprocess(extra_env: dict[str, str]) -> str:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _names(DATA_DIR_ENV)
    }
    env.update(extra_env)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from corpus_ingest_core import storage; print(storage.DATA_DIR)",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
    return completed.stdout.strip()


def test_data_dir_default_is_unchanged_without_env_override():
    assert _data_dir_in_subprocess({}) == "data"


def test_data_dir_honors_environment_override():
    override = str(Path("alt-data-root"))
    assert _data_dir_in_subprocess({DATA_DIR_ENV: override}) == override


def test_data_dir_still_honors_the_pre_rename_variable():
    """0.2.0 renamed the variable; a machine set up before it must keep working.

    A data root that silently reverts to ``data/`` reads as corruption, not as
    configuration, so the old spelling stays supported until 0.3.0.
    """

    override = str(Path("legacy-data-root"))
    legacy = DEPRECATED_ALIASES[DATA_DIR_ENV]
    assert _data_dir_in_subprocess({legacy: override}) == override


def test_current_data_dir_variable_wins_over_the_deprecated_one():
    legacy = DEPRECATED_ALIASES[DATA_DIR_ENV]
    result = _data_dir_in_subprocess(
        {DATA_DIR_ENV: "current-root", legacy: "legacy-root"}
    )
    assert result == "current-root"




def _config_path_in_subprocess(extra_env: dict[str, str]) -> str:
    """Same subprocess shape as the data-dir pair: DEFAULT_CONFIG_PATH is read
    at import time, so an in-process monkeypatch would not exercise it.
    """

    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _names(CONFIG_ENV)
    }
    env.update(extra_env)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from corpus_ingest_core import config; print(config.DEFAULT_CONFIG_PATH)",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
    return completed.stdout.strip()


def test_config_path_default_is_unchanged_without_env_override():
    assert _config_path_in_subprocess({}) == str(Path("config/podcasts.yaml"))


def test_config_path_honors_environment_override():
    override = str(Path("local-profiles.yaml"))
    assert _config_path_in_subprocess({CONFIG_ENV: override}) == override


def test_config_path_still_honors_the_pre_rename_variable():
    override = str(Path("legacy-profiles.yaml"))
    legacy = DEPRECATED_ALIASES[CONFIG_ENV]
    assert _config_path_in_subprocess({legacy: override}) == override
def test_evals_reports_dir_literal_is_defined_only_in_storage():
    pattern = re.compile(r'Path\(\s*"evals"\s*\)')
    src_dir = REPO_ROOT / "src" / "corpus_ingest_core"
    offenders = [
        path.name
        for path in sorted(src_dir.glob("*.py"))
        if path.name != "storage.py"
        and pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, (
        "the evals reports root must be defined once in storage.py and "
        f"re-exported; found Path(\"evals\") in: {offenders}"
    )


def test_helper_copies_are_frozen_to_the_allowlist():
    helper_def = "def " + "_use_tmp_data_dirs"  # split so this file never matches
    offenders = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        if helper_def not in path.read_text(encoding="utf-8"):
            continue
        if path.name not in HELPER_COPY_ALLOWLIST:
            offenders.append(path.name)
    assert not offenders, (
        "new test files must use the shared tmp_data_dirs fixture from "
        f"tests/conftest.py instead of copying the helper: {offenders}"
    )


def test_every_renamed_variable_has_its_alias_wired():
    """One table, four variables, one resolution rule.

    The subprocess tests above cover CORPUS_INGEST_DATA_DIR and
    CORPUS_INGEST_CONFIG because those two are read at import time and need a
    child process to exercise. The other two -- the MCP port and the stock-lens
    debug path -- share the same `read_env` helper, so what needs guarding is
    the table, not four more subprocess round-trips: an alias that is never
    added is the failure mode, and it is invisible until an operator's setting
    silently stops taking effect.
    """

    from corpus_ingest_core import local_env_names

    current = {
        name: value
        for name, value in vars(local_env_names).items()
        if name.endswith("_ENV") and isinstance(value, str)
    }
    assert current, "no *_ENV constants found -- the module was restructured"

    missing = sorted(
        value for value in current.values() if value not in DEPRECATED_ALIASES
    )
    assert not missing, (
        f"these variables have no pre-rename alias: {missing}. Every renamed "
        "variable needs one until 0.3.0, or a machine configured before the "
        "rename loses the setting with no error."
    )
    for new_name, old_name in DEPRECATED_ALIASES.items():
        assert new_name.startswith("CORPUS_INGEST_"), new_name
        assert old_name.startswith("PODCAST_INGEST_"), old_name
        assert new_name.removeprefix("CORPUS_INGEST_") == old_name.removeprefix(
            "PODCAST_INGEST_"
        ), f"{new_name} and {old_name} are not the same variable renamed"


@pytest.mark.parametrize("name", sorted(DEPRECATED_ALIASES))
def test_current_variable_wins_over_its_alias(name, monkeypatch):
    from corpus_ingest_core.local_env_names import DEPRECATED_ALIASES, read_env

    monkeypatch.setenv(name, "current")
    monkeypatch.setenv(DEPRECATED_ALIASES[name], "deprecated")
    assert read_env(name) == "current"

    monkeypatch.delenv(name)
    assert read_env(name) == "deprecated"
