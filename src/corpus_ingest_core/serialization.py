from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def to_jsonable(value: Any) -> Any:
    """將 core dataclass / Path 結果轉成 JSON-compatible value。"""

    # `is_dataclass` is True for a dataclass *class* as well as an instance,
    # but `asdict` only accepts an instance -- passing the class raised
    # TypeError: asdict() should be called on dataclass instances. A class is
    # not a value to serialise, so it falls through to be returned as-is.
    if is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list | tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value
