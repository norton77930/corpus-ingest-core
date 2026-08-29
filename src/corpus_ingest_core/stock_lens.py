from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import storage
from .config import load_podcast_profile
from .errors import StockLensReportFailedError, StockLensReportInputError
from .gooaye_lens import load_gooaye_lens_model
from .models import StockLensReportAsset

REPORT_MODE = "deterministic-stock-lens-v1"
SUPPORTED_MAPPING_MODE = "deterministic-industry-chain-v1"
SUPPORTED_BOUNDARY_MODE = "external-data-boundary-v1"
NO_EXTERNAL_BOUNDARY = {
    "external_verification_status": "not_requested",
    "source_status": "not_fetched",
    "data_date": None,
    "required_external_checks": [],
}


def generate_stock_lens_report(
    podcast_id: str,
    stock_query: str,
    *,
    force: bool = False,
    allow_partial: bool = False,
    max_evidence_items: int = 10,
) -> StockLensReportAsset:
    """從既有 local research artifacts 產生 deterministic stock lens report。"""

    if not stock_query.strip():
        raise ValueError("stock_query 必須是非空字串。")
    if max_evidence_items < 1:
        raise ValueError("max_evidence_items 必須大於 0。")

    profile = load_podcast_profile(podcast_id)
    report_paths = storage.stock_lens_report_asset_paths(podcast_id, stock_query)
    if (
        report_paths.json_path.exists()
        and report_paths.markdown_path.exists()
        and not force
    ):
        existing = _load_existing_report_counts(report_paths.json_path)
        return StockLensReportAsset(
            podcast_id=podcast_id,
            stock_query=stock_query,
            report_json_path=report_paths.json_path,
            report_markdown_path=report_paths.markdown_path,
            report_status=existing.get("report_status", "unknown"),
            match_count=existing.get("match_count", 0),
            warning_count=existing.get("warning_count", 0),
            generated=False,
            already_exists=True,
        )

    lens_model = load_gooaye_lens_model()
    warnings: list[str] = []
    direct_evidence: list[dict[str, Any]] = []
    inferred_leads: list[dict[str, Any]] = []
    used_input_set: list[dict[str, str]] = []
    has_partial = False

    mapping_paths = _mapping_paths(podcast_id)
    if not mapping_paths:
        warnings.append(f"industry mapping artifacts missing: {podcast_id}")

    for mapping_path in mapping_paths:
        mapping_payload = _load_mapping_payload(mapping_path)
        if _required_text(mapping_payload, "mapping_mode") != SUPPORTED_MAPPING_MODE:
            raise StockLensReportInputError(
                f"industry mapping mode 不支援：{mapping_path}"
            )
        if mapping_payload.get("podcast_id") != podcast_id:
            raise StockLensReportInputError("industry mapping identity does not match podcast")
        episode_ref = _required_text(mapping_payload, "episode_ref")
        title = _required_text(mapping_payload, "title")
        boundary_payload = _load_boundary_payload(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
        )
        used_input_set.extend(
            (
                _input_identity("industry_mapping", mapping_path),
                _input_identity(
                    "external_boundary",
                    storage.external_data_boundary_asset_paths(
                        podcast_id, episode_ref, title
                    ).json_path,
                ),
            )
        )
        matched_candidates = [
            candidate
            for candidate in _stock_candidates(mapping_payload)
            if _candidate_matches(candidate, stock_query)
        ]
        if not matched_candidates:
            continue

        mapping_status = _required_text(mapping_payload, "mapping_status")
        if mapping_status == "partial-draft":
            if not allow_partial:
                raise StockLensReportInputError(
                    "matched industry mapping status is partial-draft；請使用 --allow-partial。"
                )
            has_partial = True
        elif mapping_status != "final":
            raise StockLensReportInputError(
                f"industry mapping status 不支援：{mapping_status}"
            )

        boundary_status = _required_text(boundary_payload, "boundary_status")
        if boundary_status == "partial-draft":
            if not allow_partial:
                raise StockLensReportInputError(
                    "matched external boundary status is partial-draft；請使用 --allow-partial。"
                )
            has_partial = True
        elif boundary_status != "final":
            raise StockLensReportInputError(
                f"external boundary status 不支援：{boundary_status}"
            )

        boundary_candidates = _boundary_candidates(boundary_payload)
        for candidate in matched_candidates:
            match = _candidate_match_payload(
                episode_ref=episode_ref,
                title=title,
                mapping_path=mapping_path,
                candidate=candidate,
                external_boundary=_matching_external_boundary(
                    candidate,
                    boundary_candidates,
                ),
                max_evidence_items=max_evidence_items,
            )
            if match["evidence_status"] == "podcast_explicit":
                direct_evidence.append(match)
            else:
                inferred_leads.append(match)

    report_status = _report_status(
        direct_count=len(direct_evidence),
        has_partial=has_partial,
    )
    payload = {
        "podcast_id": podcast_id,
        "stock_query": stock_query,
        "report_mode": REPORT_MODE,
        "generation_options": {"max_evidence_items": max_evidence_items},
        "input_set_lineage": sorted(
            used_input_set, key=lambda item: (item["role"], item["path"])
        ),
        "lens_config": _config_file_identity(Path("config/gooaye_lens.yaml")),
        "report_status": report_status,
        "source_status": {
            "industry_mappings": "available" if mapping_paths else "missing",
            "external_boundaries": "available" if _has_boundary(direct_evidence, inferred_leads) else "missing_or_not_matched",
            "gooaye_lens": "available",
        },
        "query_match_summary": {
            "stock_query": stock_query,
            "matched_candidate_count": len(direct_evidence) + len(inferred_leads),
            "direct_podcast_evidence_count": len(direct_evidence),
            "inferred_research_lead_count": len(inferred_leads),
            "no_direct_podcast_evidence": len(direct_evidence) == 0,
        },
        "direct_podcast_evidence": direct_evidence,
        "inferred_research_leads": inferred_leads,
        "gooaye_lens": {
            "name": lens_model.name,
            "version": lens_model.version,
            "dimension_count": len(lens_model.dimensions),
            "dimensions": [asdict(dimension) for dimension in lens_model.dimensions],
            "safety_rules": lens_model.safety_rules,
        },
        "external_verification_needs": _external_verification_needs(
            direct_evidence + inferred_leads
        ),
        "warnings": warnings,
        "not_investment_advice": True,
    }
    markdown = _render_markdown(display_name=profile.display_name, payload=payload)
    _write_report(report_paths.json_path, report_paths.markdown_path, payload, markdown)

    return StockLensReportAsset(
        podcast_id=podcast_id,
        stock_query=stock_query,
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        report_status=report_status,
        match_count=len(direct_evidence) + len(inferred_leads),
        warning_count=len(warnings),
        generated=True,
        already_exists=False,
    )


def _mapping_paths(podcast_id: str) -> list[Path]:
    mapping_dir = storage.MAPPINGS_DIR / podcast_id
    return sorted(mapping_dir.glob("*.industry-map.json"))


def _load_mapping_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StockLensReportInputError(f"industry mapping JSON 格式錯誤：{json_path}") from exc
    except OSError as exc:
        raise StockLensReportInputError(f"無法讀取 industry mapping：{exc}") from exc
    if not isinstance(payload, dict):
        raise StockLensReportInputError("industry mapping JSON 必須是 object。")
    return payload


def _load_boundary_payload(
    *, podcast_id: str, episode_ref: str, title: str
) -> dict[str, Any]:
    """Load only the boundary at the mapping's immutable identity-derived path."""

    paths = storage.external_data_boundary_asset_paths(podcast_id, episode_ref, title)
    if not paths.json_path.is_file():
        raise StockLensReportInputError(
            f"external boundary missing for mapping identity: {podcast_id}/{episode_ref}/{title}"
        )
    try:
        payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StockLensReportInputError(
            f"external boundary JSON 格式錯誤：{paths.json_path}"
        ) from exc
    except OSError as exc:
        raise StockLensReportInputError(f"無法讀取 external boundary：{exc}") from exc
    if not isinstance(payload, dict):
        raise StockLensReportInputError("external boundary JSON 必須是 object。")
    if (
        payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or payload.get("title") != title
    ):
        raise StockLensReportInputError("external boundary identity does not match mapping")
    if _required_text(payload, "boundary_mode") != SUPPORTED_BOUNDARY_MODE:
        raise StockLensReportInputError(
            f"external boundary mode 不支援：{paths.json_path}"
        )
    return payload


def _input_identity(role: str, path: Path) -> dict[str, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise StockLensReportInputError(f"stock lens input is unreadable: {path}") from exc
    return {
        "role": role,
        "path": path.resolve(strict=False).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StockLensReportInputError(f"stock lens input 缺少有效欄位：{key}")
    return value


def _stock_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("stock_candidates")
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _boundary_candidates(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if payload is None:
        return []
    candidates = payload.get("candidate_boundaries")
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _candidate_matches(candidate: dict[str, Any], stock_query: str) -> bool:
    query = _normalize_key(stock_query)
    company_name = _normalize_key(str(candidate.get("company_name", "")))
    tickers = {_normalize_key(ticker) for ticker in _string_list(candidate.get("tickers"))}
    return query == company_name or query in tickers


def _matching_external_boundary(
    candidate: dict[str, Any],
    boundary_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    for boundary_candidate in boundary_candidates:
        if _candidate_matches(boundary_candidate, str(candidate.get("company_name", ""))):
            return _external_boundary_payload(boundary_candidate)
        for ticker in _string_list(candidate.get("tickers")):
            if _candidate_matches(boundary_candidate, ticker):
                return _external_boundary_payload(boundary_candidate)
    return dict(NO_EXTERNAL_BOUNDARY)


def _external_boundary_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    checks = candidate.get("required_external_checks")
    return {
        "external_verification_status": str(
            candidate.get("external_verification_status", "not_requested")
        ),
        "source_status": str(candidate.get("source_status", "not_fetched")),
        "data_date": candidate.get("data_date"),
        "required_external_checks": checks if isinstance(checks, list) else [],
    }


def _candidate_match_payload(
    *,
    episode_ref: str,
    title: str,
    mapping_path: Path,
    candidate: dict[str, Any],
    external_boundary: dict[str, Any],
    max_evidence_items: int,
) -> dict[str, Any]:
    return {
        "episode_ref": episode_ref,
        "title": title,
        "source_mapping_path": str(mapping_path),
        "company_name": str(candidate.get("company_name", "")),
        "tickers": _string_list(candidate.get("tickers")),
        "relation": str(candidate.get("relation", "")),
        "relation_type": str(candidate.get("relation_type", "")),
        "evidence_status": str(candidate.get("evidence_status", "")),
        "verification_status": str(candidate.get("verification_status", "")),
        "evidence": _evidence(candidate, max_evidence_items),
        "external_boundary": external_boundary,
    }


def _evidence(candidate: dict[str, Any], max_evidence_items: int) -> list[dict[str, Any]]:
    evidence = candidate.get("evidence")
    if not isinstance(evidence, list):
        return []
    return [item for item in evidence[:max_evidence_items] if isinstance(item, dict)]


def _external_verification_needs(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    needs: list[dict[str, Any]] = []
    for match in matches:
        checks = match["external_boundary"].get("required_external_checks", [])
        if not isinstance(checks, list):
            checks = []
        needs.append(
            {
                "company_name": match["company_name"],
                "tickers": match["tickers"],
                "episode_ref": match["episode_ref"],
                "required_external_checks": checks,
                "external_verification_status": match["external_boundary"][
                    "external_verification_status"
                ],
                "source_status": match["external_boundary"]["source_status"],
                "data_date": match["external_boundary"]["data_date"],
            }
        )
    return needs


def _report_status(*, direct_count: int, has_partial: bool) -> str:
    if has_partial:
        return "partial-draft"
    if direct_count == 0:
        return "no-direct-podcast-evidence"
    return "final"


def _has_boundary(
    direct_evidence: list[dict[str, Any]],
    inferred_leads: list[dict[str, Any]],
) -> bool:
    for match in direct_evidence + inferred_leads:
        if match["external_boundary"].get("required_external_checks"):
            return True
    return False


def _config_file_identity(path: Path) -> dict[str, str | None]:
    try:
        raw = path.read_bytes()
    except OSError:
        return {"path": path.resolve(strict=False).as_posix(), "sha256": None}
    return {
        "path": path.resolve(strict=False).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _load_existing_report_counts(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    summary = payload.get("query_match_summary")
    warnings = payload.get("warnings")
    match_count = 0
    if isinstance(summary, dict):
        match_count = int(summary.get("matched_candidate_count", 0))
    return {
        "report_status": payload.get("report_status"),
        "match_count": match_count,
        "warning_count": len(warnings) if isinstance(warnings, list) else 0,
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _normalize_key(value: str) -> str:
    stripped = value.strip()
    return stripped.lower() if stripped.isascii() else stripped


def _render_markdown(*, display_name: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {display_name} - {payload['stock_query']} Stock Lens Report",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Stock query: {payload['stock_query']}",
        f"- Report mode: {payload['report_mode']}",
        f"- Report status: {payload['report_status']}",
        "",
        "## Query Match Summary",
        "",
        f"- Matched candidates: {payload['query_match_summary']['matched_candidate_count']}",
        f"- Direct podcast evidence: {payload['query_match_summary']['direct_podcast_evidence_count']}",
        f"- Inferred research leads: {payload['query_match_summary']['inferred_research_lead_count']}",
        "",
    ]
    if payload["query_match_summary"]["no_direct_podcast_evidence"]:
        lines.extend(["no direct podcast evidence found", ""])

    lines.extend(["## Direct Podcast Evidence", ""])
    if not payload["direct_podcast_evidence"]:
        lines.extend(["No direct podcast evidence found.", ""])
    for match in payload["direct_podcast_evidence"]:
        lines.extend(_match_lines(match))

    lines.extend(["## Inferred Research Leads", ""])
    if not payload["inferred_research_leads"]:
        lines.extend(["No inferred research leads matched.", ""])
    for match in payload["inferred_research_leads"]:
        lines.extend(_match_lines(match))

    lines.extend(["## Gooaye Lens Dimensions", ""])
    for dimension in payload["gooaye_lens"]["dimensions"]:
        lines.append(f"- {dimension['label']} ({dimension['id']}): {dimension['output_guidance']}")
    lines.extend(["", "## External Verification Needs", ""])
    if not payload["external_verification_needs"]:
        lines.extend(["No matched candidates require external verification in this report.", ""])
    for need in payload["external_verification_needs"]:
        check_types = ", ".join(
            check.get("data_type", "") for check in need["required_external_checks"]
        )
        if not check_types:
            check_types = "not configured"
        lines.append(
            f"- {need['company_name']}: {need['external_verification_status']} / "
            f"{need['source_status']} / data_date={need['data_date']} / checks={check_types}"
        )
    lines.extend(["", "## Warnings", ""])
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- No warnings.")
    lines.extend(
        [
            "",
            "## 注意事項",
            "",
            "本報告不構成投資建議。",
            "No buy/sell/hold advice. No target price. No guaranteed returns.",
            "inferred_from_industry candidates 是未查證研究線索，不代表 podcast 明確提到。",
            "本階段未查詢外部市場資料。",
            "",
        ]
    )
    return "\n".join(lines)


def _match_lines(match: dict[str, Any]) -> list[str]:
    tickers = ", ".join(match["tickers"]) if match["tickers"] else "unverified"
    lines = [
        f"### {match['company_name']} [{tickers}] - {match['episode_ref']}",
        "",
        f"- Evidence status: {match['evidence_status']}",
        f"- Verification status: {match['verification_status']}",
        f"- External status: {match['external_boundary']['external_verification_status']} / {match['external_boundary']['source_status']}",
    ]
    for evidence in match["evidence"]:
        lines.append(f"- `{evidence.get('timestamp', '')}` {evidence.get('text', '')}")
    lines.append("")
    return lines


def _write_report(
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
        raise StockLensReportFailedError(f"寫入 stock lens report 失敗：{exc}") from exc
