"""Characterization truth table for the four `_is_safe_local_path` variants.

specs/025-core-consolidation FR-003: this table was captured empirically from
the pre-consolidation implementations on 2026-08-08 and MUST NOT change when
the shared structural skeleton (`corpus_ingest_core.path_safety`) replaces the
copy-pasted bodies. Each column is a per-module spec'd contract:

- A `corpus_episode_completion_workflow_runner` — absolute allowed, separator
  required, `_safe_output_text` round-trip.
- B `corpus_episode_workflow_runner` — as A with `_safe_message` round-trip.
- C `corpus_semantic_remediation_runner` — as A/B but WITHOUT the final
  round-trip conjunct. Known deliberate divergence: sensitive-looking path
  fragments (`secret`, `api_key`, `traceback`) pass the structural check here.
  Tightening this is a spec-015 behavior change and is out of 025 scope.
- D `corpus_latest_episode_deterministic_workflow_runner` — rejects any
  absolute path and any `:`; scans `_FORBIDDEN_PATH_FRAGMENTS`; `_safe_text`
  round-trip; and (unlike A/B/C) does NOT require a path separator.

C is called only with `str` by its module (callers pre-filter); non-string
behavior is pinned for A/B/D only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from corpus_ingest_core.corpus_episode_completion_workflow_runner import (
    _is_safe_local_path as predicate_a,
)
from corpus_ingest_core.corpus_episode_workflow_runner import (
    _is_safe_local_path as predicate_b,
)
from corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner import (
    _is_safe_local_path as predicate_d,
)
from corpus_ingest_core.corpus_semantic_remediation_runner import (
    _is_safe_local_path as predicate_c,
)

TRUTH_TABLE = [
    ("data/corpus/gooaye/corpus-index.json", True, True, True, True),
    ("data\\corpus\\gooaye\\corpus-index.json", True, True, True, True),
    ("corpus-index.json", False, False, False, True),
    ("/var/data/x.json", True, True, True, False),
    ("C:\\data\\x.json", True, True, True, False),
    ("C:/data/x.json", True, True, True, False),
    ("D:/x.json", True, True, True, False),
    ("d:x.json", False, False, False, False),
    ("\\\\host\\share\\x.json", False, False, False, False),
    ("//host/share/x.json", False, False, False, False),
    ("https://example.com/x.json", False, False, False, False),
    ("file://x/y.json", False, False, False, False),
    ("data/x.json?token=1", False, False, False, False),
    ("data/x#frag.json", False, False, False, False),
    ("data/x|y.json", False, False, False, False),
    ("data/sub dir/x.json", False, False, False, False),
    (" data/x.json", False, False, False, False),
    ("data/x.json ", False, False, False, False),
    ("", False, False, False, False),
    ("data/../x.json", False, False, False, False),
    ("data/./x.json", False, False, False, False),
    ("data//x.json", False, False, False, False),
    ("data/x", False, False, False, False),
    ("data/x.", False, False, False, False),
    ("data/x.toolongextension1234567", False, False, False, False),
    ("data/股癌/EP672__股癌.json", True, True, True, True),
    ("data/x:y/z.json", False, False, False, False),
    ("data/x~y.json", False, False, False, False),
    ("data/😀/x.json", False, False, False, False),
    ("data/.hidden/x.json", True, True, True, True),
    ("data/-x/y.json", True, True, True, True),
    ("data/CON.json", True, True, True, True),
    ("data/x.JSON", True, True, True, True),
    ("data/tab\tx.json", False, False, False, False),
    ("data/secret/x.json", False, False, True, False),
    ("data/api_key.json", False, False, True, False),
    ("data/token=abc/x.json", False, False, False, False),
    ("data/traceback/x.json", False, False, True, False),
    ("data/.env/x.json", True, True, True, False),
    (
        "evals/research-llm-smoke/reports/EP672.semantic-review.json",
        True,
        True,
        True,
        True,
    ),
    ("data/x-1.2.3.json", True, True, True, True),
    ("a/" + "b" * 1030 + ".json", False, False, False, False),
]

NON_STRING_VALUES = [None, 123, 4.5, Path("data/x.json"), b"data/x.json", ["x.json"]]


@pytest.mark.parametrize(
    ("value", "expected_a", "expected_b", "expected_c", "expected_d"),
    TRUTH_TABLE,
    ids=[repr(row[0])[:60] for row in TRUTH_TABLE],
)
def test_truth_table_is_frozen(value, expected_a, expected_b, expected_c, expected_d):
    assert predicate_a(value) is expected_a, "variant A drifted"
    assert predicate_b(value) is expected_b, "variant B drifted"
    assert predicate_c(value) is expected_c, "variant C drifted"
    assert predicate_d(value) is expected_d, "variant D drifted"


@pytest.mark.parametrize("value", NON_STRING_VALUES, ids=repr)
def test_non_string_values_are_rejected_by_a_b_d(value):
    assert predicate_a(value) is False
    assert predicate_b(value) is False
    assert predicate_d(value) is False


def test_known_divergences_stay_documented():
    """The four columns are intentionally NOT identical; lock the deltas."""
    diverging_rows = [row for row in TRUTH_TABLE if len(set(row[1:])) > 1]
    assert diverging_rows, "divergence disappeared — update spec 025 known-debt"
    only_c_accepts = {row[0] for row in TRUTH_TABLE if row[3] and not (row[1] or row[2] or row[4])}
    assert only_c_accepts == {
        "data/secret/x.json",
        "data/api_key.json",
        "data/traceback/x.json",
    }
    only_d_accepts = {row[0] for row in TRUTH_TABLE if row[4] and not (row[1] or row[2] or row[3])}
    assert only_d_accepts == {"corpus-index.json"}
