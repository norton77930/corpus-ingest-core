from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import GooayeLensConfigError
from .models import GooayeLensDimension, GooayeLensModel

DEFAULT_GOOAYE_LENS_CONFIG_PATH = Path("config/gooaye_lens.yaml")


def load_gooaye_lens_model(
    path: str | Path = DEFAULT_GOOAYE_LENS_CONFIG_PATH,
) -> GooayeLensModel:
    """載入並驗證本機 Gooaye Lens model config。"""

    config_path = Path(path)
    if not config_path.exists():
        raise GooayeLensConfigError(f"gooaye lens config missing: {config_path}")
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise GooayeLensConfigError(f"gooaye lens config unreadable: {exc}") from exc
    if not isinstance(payload, dict):
        raise GooayeLensConfigError("gooaye lens config must be a mapping")

    version = _required_int(payload, "version")
    name = _required_text(payload, "name")
    description = _required_text(payload, "description")
    dimensions = _parse_dimensions(payload.get("dimensions"))
    safety_rules = _required_text_list(payload, "safety_rules")
    _validate_safety_rules(safety_rules)
    return GooayeLensModel(
        version=version,
        name=name,
        description=description,
        dimensions=dimensions,
        safety_rules=safety_rules,
    )


def _parse_dimensions(raw_dimensions: Any) -> list[GooayeLensDimension]:
    if not isinstance(raw_dimensions, list) or not raw_dimensions:
        raise GooayeLensConfigError("gooaye lens config dimensions must be a non-empty list")
    dimensions: list[GooayeLensDimension] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw_dimensions, start=1):
        if not isinstance(item, dict):
            raise GooayeLensConfigError(f"dimension {index} must be a mapping")
        dimension_id = _required_text(item, "id")
        if dimension_id in seen_ids:
            raise GooayeLensConfigError(f"dimension id duplicated: {dimension_id}")
        seen_ids.add(dimension_id)
        dimensions.append(
            GooayeLensDimension(
                id=dimension_id,
                label=_required_text(item, "label"),
                description=_required_text(item, "description"),
                analysis_questions=_required_text_list(item, "analysis_questions"),
                expected_evidence_sources=_required_text_list(item, "expected_evidence_sources"),
                output_guidance=_required_text(item, "output_guidance"),
            )
        )
    return dimensions


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GooayeLensConfigError(f"gooaye lens config missing valid field: {key}")
    return value.strip()


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise GooayeLensConfigError(f"gooaye lens config missing valid field: {key}")
    return value


def _required_text_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise GooayeLensConfigError(f"gooaye lens config missing valid field: {key}")
    values = [str(item).strip() for item in value if str(item).strip()]
    if not values:
        raise GooayeLensConfigError(f"gooaye lens config missing valid field: {key}")
    return values


def _validate_safety_rules(safety_rules: list[str]) -> None:
    safety_text = "\n".join(safety_rules).lower()
    required_fragments = [
        "buy/sell/hold",
        "target price",
        "guaranteed returns",
        "podcast evidence, inference, and external-data status",
        "do not fabricate podcast evidence",
    ]
    for fragment in required_fragments:
        if fragment not in safety_text:
            raise GooayeLensConfigError(f"gooaye lens config safety_rules missing required boundary: {fragment}")
