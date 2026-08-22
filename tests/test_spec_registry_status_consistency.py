"""Spec-package Status lines must agree with the registry in specs/README.md.

Every capability package states its lifecycle twice: once as the ``**Status**:``
line in ``specs/<nnn>-<name>/spec.md``, and once in the ``specs/README.md``
registry entry for the same package. Nothing kept the two in step, and both had
drifted in opposite directions -- 037 still called itself a Draft with no
implementation while the registry described it as implemented, reviewed, and
confirmed by a real run; 038 called itself Implemented while the registry still
had it in implementation. Neither is caught by
``tests/test_docs_registry_count_consistency.py``, whose governed-file list
covers ``specs/README.md`` but not the packages themselves.

The check is deliberately narrow. It compares only the *leading* lifecycle term
on each side, because both texts are prose that mentions other packages' states
in passing: spec 018's status says "post-review controls specified below", and
the 028 registry entry describes Hermes runtime as BLOCKED while the package
itself is complete. Comparing every term found would fail both. A package whose
registry entry states no lifecycle term at all -- the 008-016 entries open with
a description -- is unstated rather than contradictory, and is skipped. So is a package with no
``**Status**:`` line at all -- the 002-007 backfills and the 029-034 Hermes
chain. Twenty of the forty-two packages are compared; the rest state their
lifecycle on only one side, or on neither.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs"
REGISTRY = SPECS / "README.md"

PACKAGE_DIR = re.compile(r"^\d{3}-")
STATUS_LINE = re.compile(r"^\*\*Status\*\*:\s*(.+)$", re.M)

# Mutually exclusive lifecycle terms, matched case-insensitively.
LIFECYCLE_TERMS = {
    "implemented": re.compile(r"\bimplemented\b"),
    "blocked": re.compile(r"\bblocked\b"),
    "complete": re.compile(r"\bcomplete\b"),
    "draft": re.compile(r"\bdraft\b"),
    "specified": re.compile(r"\bspecified\b|\bin implementation\b"),
}

# A finished live confirm and a not-run live confirm cannot both be true. This
# is a separate rule because both sides say "Implemented" while contradicting
# each other on the evidence, so the lifecycle comparison above cannot see it.
LIVE_CONFIRMED = re.compile(r"live[- ]confirmed", re.I)
LIVE_CONFIRM_NOT_RUN = re.compile(r"confirm not run", re.I)


def _packages() -> list[Path]:
    return sorted(p for p in SPECS.iterdir() if p.is_dir() and PACKAGE_DIR.match(p.name))


def _spec_status(package: Path) -> str | None:
    spec = package / "spec.md"
    if not spec.exists():
        return None
    match = STATUS_LINE.search(spec.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def _registry_entry(registry_text: str, name: str) -> str | None:
    match = re.search(rf"^- `{re.escape(name)}`:\s*(.+)$", registry_text, re.M)
    return match.group(1).strip() if match else None


def _leading_term(text: str) -> str | None:
    """The lifecycle term that appears first, or None if the text states none."""
    lowered = text.casefold()
    hits = [
        (found.start(), term)
        for term, pattern in LIFECYCLE_TERMS.items()
        if (found := pattern.search(lowered))
    ]
    return min(hits)[1] if hits else None


def test_every_spec_package_status_agrees_with_the_registry():
    registry_text = REGISTRY.read_text(encoding="utf-8")
    problems = []
    for package in _packages():
        status = _spec_status(package)
        entry = _registry_entry(registry_text, package.name)
        if status is None or entry is None:
            continue
        spec_term = _leading_term(status)
        registry_term = _leading_term(entry)
        if spec_term is None or registry_term is None:
            continue
        if spec_term != registry_term:
            problems.append(
                f"{package.name}: spec.md says {spec_term!r} but "
                f"specs/README.md says {registry_term!r}"
            )
    assert not problems, (
        "a spec package and the registry disagree about its lifecycle -- fix "
        "whichever one is stale, do not relax this check: " + "; ".join(problems)
    )


def test_live_confirm_evidence_does_not_contradict_between_spec_and_registry():
    registry_text = REGISTRY.read_text(encoding="utf-8")
    problems = []
    for package in _packages():
        status = _spec_status(package)
        entry = _registry_entry(registry_text, package.name)
        if status is None or entry is None:
            continue
        if LIVE_CONFIRMED.search(status) and LIVE_CONFIRM_NOT_RUN.search(entry):
            problems.append(
                f"{package.name}: spec.md claims a completed live confirm while "
                f"specs/README.md still records it as not run"
            )
    assert not problems, (
        "a live confirm cannot be both done and not run -- update the registry "
        "entry when a spec records one: " + "; ".join(problems)
    )
