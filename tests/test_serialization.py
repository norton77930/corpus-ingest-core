"""`to_jsonable` must survive a dataclass class, not just an instance.

`dataclasses.is_dataclass` answers True for a dataclass *class* as well as for
an instance of one, while `asdict` accepts only an instance. The original guard
tested just `is_dataclass(value)`, so handing the class straight to the
converter raised `TypeError: asdict() should be called on dataclass instances`.

Nothing in the repository did that, which is why no test caught it -- mypy did,
and only on a version newer than the one the authoring machine had installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from corpus_ingest_core.serialization import to_jsonable


@dataclass(frozen=True)
class _Leaf:
    name: str
    where: Path


@dataclass(frozen=True)
class _Branch:
    leaf: _Leaf
    tags: tuple[str, ...]


def test_dataclass_instance_becomes_a_dict():
    where = Path("data/x.json")
    result = to_jsonable(_Leaf(name="a", where=where))

    # str(Path), not a literal: this converter emits the platform's own
    # separator, so a hardcoded "data/x.json" passes on Linux and fails on
    # Windows. (The separator choice itself is worth revisiting -- paths that
    # enter content digests elsewhere go through .as_posix() -- but changing it
    # would move every artifact's bytes and is not this commit's business.)
    assert result == {"name": "a", "where": str(where)}


def test_dataclass_class_is_returned_untouched():
    """The regression. Previously TypeError; a class is not a value to encode."""

    assert to_jsonable(_Leaf) is _Leaf


def test_dataclass_class_nested_in_a_container_does_not_raise():
    result = to_jsonable({"model": _Leaf, "items": [_Branch, 1]})

    assert result == {"model": _Leaf, "items": [_Branch, 1]}


def test_nested_dataclasses_paths_and_sequences_are_converted():
    where = Path("data/y.json")
    branch = _Branch(leaf=_Leaf(name="b", where=where), tags=("x", "y"))

    assert to_jsonable([branch]) == [{"leaf": {"name": "b", "where": str(where)}, "tags": ["x", "y"]}]


def test_non_dataclass_values_pass_through():
    assert to_jsonable({"n": 1, "s": "t", "b": True, "none": None}) == {
        "n": 1,
        "s": "t",
        "b": True,
        "none": None,
    }
