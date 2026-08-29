from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from .canonical_transcript import current_canonical_transcript_identity
from .config import load_podcast_profile
from .episode_claim import episode_writer_claimed
from .errors import ExternalDataBoundaryFailedError, ExternalDataBoundaryInputError
from .models import ExternalDataBoundaryAsset
from .storage import external_data_boundary_asset_paths, industry_chain_mapping_asset_paths

BOUNDARY_MODE = "external-data-boundary-v1"
SUPPORTED_MAPPING_MODE = "deterministic-industry-chain-v1"
DEFAULT_BOUNDARY_CONFIG_PATH = Path("config/external_data_boundary.yaml")


@episode_writer_claimed
def generate_external_data_boundary(
    podcast_id: str,
    episode_ref: str,
    *,
    force: bool = False,
    allow_partial: bool = False,
) -> ExternalDataBoundaryAsset:
    """從 Phase 6C industry mapping 產生 external data boundary scaffold。"""

    profile = load_podcast_profile(podcast_id)
    transcript_identity = current_canonical_transcript_identity(podcast_id, episode_ref)
    mapping_paths = (
        None
        if transcript_identity is None
        else industry_chain_mapping_asset_paths(
            podcast_id, episode_ref, transcript_identity.title
        )
    )
    if mapping_paths is None or not mapping_paths.json_path.exists():
        raise ExternalDataBoundaryInputError(
            f"找不到 industry chain mapping：{podcast_id}/{episode_ref}"
        )

    mapping_payload = _load_mapping_payload(mapping_paths.json_path)
    _validate_mapping_identity(mapping_payload, podcast_id, episode_ref)
    mapping_mode = _required_text(mapping_payload, "mapping_mode")
    if mapping_mode != SUPPORTED_MAPPING_MODE:
        raise ExternalDataBoundaryInputError(
            f"industry chain mapping mode 不支援：{mapping_mode}"
        )

    mapping_status = _required_text(mapping_payload, "mapping_status")
    if mapping_status == "partial-draft" and not allow_partial:
        raise ExternalDataBoundaryInputError(
            "industry chain mapping status is partial-draft；請使用 --allow-partial。"
        )
    if mapping_status not in {"final", "partial-draft"}:
        raise ExternalDataBoundaryInputError(
            f"industry chain mapping status 不支援：{mapping_status}"
        )

    title = _required_text(mapping_payload, "title")
    boundary_paths = external_data_boundary_asset_paths(podcast_id, episode_ref, title)
    boundary_config, warnings = _load_boundary_config(DEFAULT_BOUNDARY_CONFIG_PATH)
    if (
        boundary_paths.json_path.exists()
        and boundary_paths.markdown_path.exists()
        and not force
    ):
        existing = _load_existing_boundary_counts(boundary_paths.json_path)
        return ExternalDataBoundaryAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            boundary_json_path=boundary_paths.json_path,
            boundary_markdown_path=boundary_paths.markdown_path,
            boundary_status=existing.get("boundary_status", _boundary_status(mapping_status)),
            candidate_count=existing.get("candidate_count", 0),
            warning_count=existing.get("warning_count", len(warnings)),
            generated=False,
            already_exists=True,
        )

    checks = _external_checks(boundary_config)
    candidates = [
        _candidate_boundary(candidate, checks)
        for candidate in _stock_candidates(mapping_payload)
    ]
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "boundary_mode": BOUNDARY_MODE,
        "boundary_config": _config_file_identity(DEFAULT_BOUNDARY_CONFIG_PATH),
        "boundary_status": _boundary_status(mapping_status),
        "source_status": {
            "industry_mapping": "available",
            "boundary_config": "available" if boundary_config else "missing_or_empty",
        },
        "source_mapping_path": str(mapping_paths.json_path),
        "candidate_boundaries": candidates,
        "warnings": warnings,
        "not_investment_advice": True,
    }
    markdown = _render_markdown(display_name=profile.display_name, payload=payload)
    _write_boundary(
        boundary_paths.json_path,
        boundary_paths.markdown_path,
        payload,
        markdown,
    )

    return ExternalDataBoundaryAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        boundary_json_path=boundary_paths.json_path,
        boundary_markdown_path=boundary_paths.markdown_path,
        boundary_status=payload["boundary_status"],
        candidate_count=len(candidates),
        warning_count=len(warnings),
        generated=True,
        already_exists=False,
    )


def _load_mapping_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExternalDataBoundaryInputError(
            f"industry chain mapping JSON 格式錯誤：{json_path}"
        ) from exc
    except OSError as exc:
        raise ExternalDataBoundaryInputError(
            f"無法讀取 industry chain mapping：{exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ExternalDataBoundaryInputError("industry chain mapping JSON 必須是 object。")
    return payload


def _validate_mapping_identity(
    payload: dict[str, Any], podcast_id: str, episode_ref: str
) -> None:
    payload_podcast_id = _required_text(payload, "podcast_id")
    payload_episode_ref = _required_text(payload, "episode_ref")
    if payload_podcast_id != podcast_id or payload_episode_ref != episode_ref:
        raise ExternalDataBoundaryInputError(
            "industry chain mapping 的 podcast_id 或 episode_ref 不符合請求。"
        )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExternalDataBoundaryInputError(f"industry chain mapping 缺少有效欄位：{key}")
    return value


def _boundary_status(mapping_status: str) -> str:
    return "partial-draft" if mapping_status == "partial-draft" else "final"


def _load_boundary_config(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"external data boundary config missing: {path}"]
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return {}, [f"external data boundary config unreadable: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["external data boundary config must be a mapping"]
    checks = payload.get("external_data_checks")
    if not isinstance(checks, list):
        return {}, ["external data boundary config must include external_data_checks"]
    return payload, []


def _external_checks(boundary_config: dict[str, Any]) -> list[dict[str, Any]]:
    checks = boundary_config.get("external_data_checks")
    if not isinstance(checks, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in checks:
        if not isinstance(item, dict):
            continue
        data_type = str(item.get("data_type", "")).strip()
        if not data_type:
            continue
        normalized.append(
            {
                "data_type": data_type,
                "label": str(item.get("label", data_type)),
                "requires_source_status": True,
                "requires_data_date": True,
            }
        )
    return normalized


def _stock_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("stock_candidates")
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _candidate_boundary(
    candidate: dict[str, Any], checks: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "company_name": str(candidate.get("company_name", "")),
        "tickers": _string_list(candidate.get("tickers")),
        "relation": str(candidate.get("relation", "")),
        "relation_type": str(candidate.get("relation_type", "")),
        "evidence_status": str(candidate.get("evidence_status", "")),
        "verification_status": str(candidate.get("verification_status", "")),
        "external_verification_status": "not_requested",
        "source_status": "not_fetched",
        "data_date": None,
        "required_external_checks": checks,
    }


def _config_file_identity(path: Path) -> dict[str, str | None]:
    try:
        raw = path.read_bytes()
    except OSError:
        return {"path": path.resolve(strict=False).as_posix(), "sha256": None}
    return {
        "path": path.resolve(strict=False).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _load_existing_boundary_counts(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    candidates = payload.get("candidate_boundaries")
    warnings = payload.get("warnings")
    return {
        "boundary_status": payload.get("boundary_status"),
        "candidate_count": len(candidates) if isinstance(candidates, list) else 0,
        "warning_count": len(warnings) if isinstance(warnings, list) else 0,
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _render_markdown(*, display_name: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {display_name} - {payload['episode_ref']} External Data Boundary",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Episode: {payload['episode_ref']}",
        f"- Title: {payload['title']}",
        f"- Boundary mode: {payload['boundary_mode']}",
        f"- Boundary status: {payload['boundary_status']}",
        "",
        "## Warnings",
        "",
    ]
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- No warnings.")
    lines.extend(["", "## Candidate Boundaries", ""])
    if not payload["candidate_boundaries"]:
        lines.extend(["No stock candidates found in the source mapping.", ""])
    for candidate in payload["candidate_boundaries"]:
        tickers = ", ".join(candidate["tickers"]) if candidate["tickers"] else "unverified"
        checks = ", ".join(
            check["data_type"] for check in candidate["required_external_checks"]
        )
        if not checks:
            checks = "no configured external checks"
        lines.extend(
            [
                f"### {candidate['company_name']} [{tickers}]",
                "",
                f"- Relation type: {candidate['relation_type']}",
                f"- Evidence status: {candidate['evidence_status']}",
                f"- Mapping verification status: {candidate['verification_status']}",
                f"- External verification status: {candidate['external_verification_status']}",
                f"- Source status: {candidate['source_status']}",
                "- Data date: unavailable",
                f"- Required external checks: {checks}",
                "",
            ]
        )
    lines.extend(
        [
            "## 注意事項",
            "",
            "本檔案不構成投資建議。",
            "本階段未查詢外部市場資料，所有 external data 狀態皆為 not_requested / not_fetched。",
            "inferred_from_industry candidates 是未查證研究線索，不代表 podcast 明確提到。",
            "",
        ]
    )
    return "\n".join(lines)


def _write_boundary(
    json_path: Path,
    markdown_path: Path,
    payload: dict[str, Any],
    markdown: str,
) -> None:
    json_part_path = json_path.with_name(f"{json_path.name}.part")
    markdown_part_path = markdown_path.with_name(f"{markdown_path.name}.part")
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_part_path.unlink(missing_ok=True)
        markdown_part_path.unlink(missing_ok=True)
        json_part_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        markdown_part_path.write_text(markdown, encoding="utf-8")
        json_part_path.replace(json_path)
        markdown_part_path.replace(markdown_path)
    except OSError as exc:
        for part_path in (json_part_path, markdown_part_path):
            try:
                part_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise ExternalDataBoundaryFailedError(
            f"寫入 external data boundary 失敗：{exc}"
        ) from exc
