from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from . import storage
from .canonical_transcript import current_canonical_transcript_identity
from .config import load_podcast_profile
from .episode_claim import episode_writer_claimed
from .errors import IndustryMappingFailedError, IndustryMappingInputError
from .models import IndustryChainMappingAsset
from .storage import industry_chain_mapping_asset_paths

MAPPING_MODE = "deterministic-industry-chain-v1"
DEFAULT_MAPPING_CONFIG_PATH = Path("config/industry_chain_mappings.yaml")


@episode_writer_claimed
def generate_industry_chain_mapping(
    podcast_id: str,
    episode_ref: str,
    *,
    force: bool = False,
    allow_partial: bool = False,
    max_candidates_per_node: int = 5,
    max_evidence_per_candidate: int = 5,
) -> IndustryChainMappingAsset:
    """從 Phase 6B episode intelligence report 產生 deterministic industry mapping。"""

    if max_candidates_per_node < 1:
        raise ValueError("max_candidates_per_node 必須大於 0。")
    if max_evidence_per_candidate < 1:
        raise ValueError("max_evidence_per_candidate 必須大於 0。")

    profile = load_podcast_profile(podcast_id)
    transcript_identity = current_canonical_transcript_identity(podcast_id, episode_ref)
    report_paths = (
        None
        if transcript_identity is None
        else storage.episode_intelligence_report_asset_paths(
            podcast_id, episode_ref, transcript_identity.title
        )
    )
    if report_paths is None or not report_paths.json_path.exists():
        raise IndustryMappingInputError(
            f"找不到 episode intelligence report：{podcast_id}/{episode_ref}"
        )

    report_payload = _load_report_payload(report_paths.json_path)
    _validate_report_identity(report_payload, podcast_id, episode_ref)
    report_status = _required_text(report_payload, "report_status")
    if report_status == "partial-draft" and not allow_partial:
        raise IndustryMappingInputError(
            "episode intelligence report status is partial-draft；請使用 --allow-partial。"
        )
    if report_status not in {"final", "partial-draft"}:
        raise IndustryMappingInputError(
            f"episode intelligence report status 不支援：{report_status}"
        )

    title = _required_text(report_payload, "title")
    mapping_paths = industry_chain_mapping_asset_paths(podcast_id, episode_ref, title)
    mapping_config, warnings = _load_mapping_config(DEFAULT_MAPPING_CONFIG_PATH)
    if (
        mapping_paths.json_path.exists()
        and mapping_paths.markdown_path.exists()
        and not force
    ):
        existing = _load_existing_mapping_counts(mapping_paths.json_path)
        return IndustryChainMappingAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            mapping_json_path=mapping_paths.json_path,
            mapping_markdown_path=mapping_paths.markdown_path,
            mapping_status=existing.get("mapping_status", _mapping_status(report_status)),
            node_count=existing.get("node_count", 0),
            candidate_count=existing.get("candidate_count", 0),
            warning_count=existing.get("warning_count", len(warnings)),
            generated=False,
            already_exists=True,
        )

    if mapping_config:
        nodes, stock_candidates, mapping_warnings = _build_mapping(
            report_payload=report_payload,
            mapping_config=mapping_config,
            max_candidates_per_node=max_candidates_per_node,
            max_evidence_per_candidate=max_evidence_per_candidate,
        )
    else:
        nodes, stock_candidates, mapping_warnings = [], [], []
    warnings.extend(mapping_warnings)
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "mapping_mode": MAPPING_MODE,
        "generation_options": {
            "max_candidates_per_node": max_candidates_per_node,
            "max_evidence_per_candidate": max_evidence_per_candidate,
        },
        "mapping_config": _config_file_identity(DEFAULT_MAPPING_CONFIG_PATH),
        "mapping_status": _mapping_status(report_status),
        "source_status": {
            "episode_intelligence_report": "available",
            "mapping_config": "available" if mapping_config else "missing_or_empty",
        },
        "source_report_path": str(report_paths.json_path),
        "industry_chain_nodes": nodes,
        "stock_candidates": stock_candidates,
        "warnings": warnings,
        "not_investment_advice": True,
    }
    markdown = _render_markdown(
        display_name=profile.display_name,
        payload=payload,
    )
    _write_mapping(mapping_paths.json_path, mapping_paths.markdown_path, payload, markdown)

    return IndustryChainMappingAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        mapping_json_path=mapping_paths.json_path,
        mapping_markdown_path=mapping_paths.markdown_path,
        mapping_status=payload["mapping_status"],
        node_count=len(nodes),
        candidate_count=len(stock_candidates),
        warning_count=len(warnings),
        generated=True,
        already_exists=False,
    )


def _load_report_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IndustryMappingInputError(
            f"episode intelligence report JSON 格式錯誤：{json_path}"
        ) from exc
    except OSError as exc:
        raise IndustryMappingInputError(f"無法讀取 episode intelligence report：{exc}") from exc
    if not isinstance(payload, dict):
        raise IndustryMappingInputError("episode intelligence report JSON 必須是 object。")
    return payload


def _validate_report_identity(
    payload: dict[str, Any], podcast_id: str, episode_ref: str
) -> None:
    payload_podcast_id = _required_text(payload, "podcast_id")
    payload_episode_ref = _required_text(payload, "episode_ref")
    if payload_podcast_id != podcast_id or payload_episode_ref != episode_ref:
        raise IndustryMappingInputError(
            "episode intelligence report 的 podcast_id 或 episode_ref 不符合請求。"
        )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise IndustryMappingInputError(f"episode intelligence report 缺少有效欄位：{key}")
    return value


def _mapping_status(report_status: str) -> str:
    return "partial-draft" if report_status == "partial-draft" else "final"


def _load_mapping_config(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"mapping config missing: {path}"]
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return {}, [f"mapping config unreadable: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["mapping config must be a mapping"]
    industry_nodes = payload.get("industry_nodes")
    company_aliases = payload.get("company_aliases")
    if not isinstance(industry_nodes, dict) or not isinstance(company_aliases, dict):
        return {}, ["mapping config must include industry_nodes and company_aliases mappings"]
    return payload, []


def _config_file_identity(path: Path) -> dict[str, str | None]:
    try:
        raw = path.read_bytes()
    except OSError:
        return {"path": path.resolve(strict=False).as_posix(), "sha256": None}
    return {
        "path": path.resolve(strict=False).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _load_existing_mapping_counts(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    nodes = payload.get("industry_chain_nodes")
    candidates = payload.get("stock_candidates")
    warnings = payload.get("warnings")
    return {
        "mapping_status": payload.get("mapping_status"),
        "node_count": len(nodes) if isinstance(nodes, list) else 0,
        "candidate_count": len(candidates) if isinstance(candidates, list) else 0,
        "warning_count": len(warnings) if isinstance(warnings, list) else 0,
    }


def _build_mapping(
    *,
    report_payload: dict[str, Any],
    mapping_config: dict[str, Any],
    max_candidates_per_node: int,
    max_evidence_per_candidate: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    industry_nodes_config = mapping_config.get("industry_nodes", {})
    company_aliases = mapping_config.get("company_aliases", {})
    warnings: list[str] = []
    node_builders: dict[str, dict[str, Any]] = {}
    stock_candidates: dict[tuple[str, str], dict[str, Any]] = {}
    explicit_company_names: set[str] = set()

    for mention in _mentions(report_payload, "company") + _mentions(
        report_payload, "stock_or_ticker"
    ):
        alias = _lookup_alias(company_aliases, str(mention.get("text", "")))
        company_name = str(alias.get("company_name") or mention.get("text", "")).strip()
        if not company_name:
            continue
        explicit_company_names.add(_normalize_key(company_name))
        evidence = _evidence(mention, max_evidence_per_candidate)
        candidate = {
            "company_name": company_name,
            "tickers": _string_list(alias.get("tickers")),
            "relation": "podcast_mention",
            "relation_type": "podcast_explicit",
            "evidence_status": "podcast_explicit",
            "verification_status": "podcast_evidence",
            "source_terms": [str(mention.get("text", ""))],
            "evidence": evidence,
        }
        stock_candidates[(_normalize_key(company_name), "podcast_explicit")] = candidate
        for node_id in _string_list(alias.get("industry_node_ids")):
            node_config = industry_nodes_config.get(node_id)
            if not isinstance(node_config, dict):
                continue
            node = _node_builder(node_builders, node_id, node_config)
            _append_unique(node["source_terms"], str(mention.get("text", "")))
            _extend_evidence(node["evidence"], evidence, max_evidence_per_candidate)
            node["stock_candidates"][(_normalize_key(company_name), "podcast_explicit")] = candidate

    for clue in _industry_clues(report_payload):
        text = str(clue.get("text", "")).strip()
        if not text:
            continue
        matched_node_ids = _matching_node_ids(industry_nodes_config, text)
        if not matched_node_ids:
            warnings.append(f"unmatched industry clue: {text}")
            continue
        clue_evidence = _evidence(clue, max_evidence_per_candidate)
        for node_id in matched_node_ids:
            node_config = industry_nodes_config.get(node_id)
            if not isinstance(node_config, dict):
                continue
            node = _node_builder(node_builders, node_id, node_config)
            _append_unique(node["source_terms"], text)
            _extend_evidence(node["evidence"], clue_evidence, max_evidence_per_candidate)
            for raw_candidate in _candidate_configs(node_config)[:max_candidates_per_node]:
                company_name = str(raw_candidate.get("company_name", "")).strip()
                if not company_name or _normalize_key(company_name) in explicit_company_names:
                    continue
                candidate = {
                    "company_name": company_name,
                    "tickers": _string_list(raw_candidate.get("tickers")),
                    "relation": str(raw_candidate.get("relation", "industry_related")),
                    "relation_type": "inferred_from_industry",
                    "evidence_status": "inferred_from_industry",
                    "verification_status": "needs_verification",
                    "source_terms": [text],
                    "evidence": clue_evidence,
                }
                key = (_normalize_key(company_name), "inferred_from_industry")
                if key not in stock_candidates:
                    stock_candidates[key] = candidate
                node["stock_candidates"][key] = stock_candidates[key]

    nodes = []
    for node_id in sorted(node_builders):
        node = node_builders[node_id]
        node_candidates = list(node["stock_candidates"].values())[:max_candidates_per_node]
        nodes.append(
            {
                "node_id": node_id,
                "label": node["label"],
                "source_terms": node["source_terms"],
                "evidence": node["evidence"],
                "stock_candidates": node_candidates,
            }
        )
    return nodes, list(stock_candidates.values()), warnings


def _mentions(payload: dict[str, Any], mention_type: str) -> list[dict[str, Any]]:
    mentions_by_type = payload.get("mentions_by_type")
    if not isinstance(mentions_by_type, dict):
        return []
    mentions = mentions_by_type.get(mention_type)
    if not isinstance(mentions, list):
        return []
    return [mention for mention in mentions if isinstance(mention, dict)]


def _industry_clues(payload: dict[str, Any]) -> list[dict[str, Any]]:
    clues = payload.get("industry_clues")
    if not isinstance(clues, list):
        return []
    return [clue for clue in clues if isinstance(clue, dict)]


def _lookup_alias(company_aliases: dict[str, Any], text: str) -> dict[str, Any]:
    for key, value in company_aliases.items():
        if _normalize_key(str(key)) == _normalize_key(text) and isinstance(value, dict):
            return value
    return {}


def _matching_node_ids(industry_nodes_config: dict[str, Any], text: str) -> list[str]:
    matched = []
    normalized_text = _normalize_key(text)
    for node_id, node_config in industry_nodes_config.items():
        if not isinstance(node_config, dict):
            continue
        aliases = _string_list(node_config.get("aliases"))
        if any(_normalize_key(alias) == normalized_text for alias in aliases):
            matched.append(str(node_id))
    return matched


def _node_builder(
    builders: dict[str, dict[str, Any]], node_id: str, node_config: dict[str, Any]
) -> dict[str, Any]:
    if node_id not in builders:
        builders[node_id] = {
            "label": str(node_config.get("label", node_id)),
            "source_terms": [],
            "evidence": [],
            "stock_candidates": {},
        }
    return builders[node_id]


def _candidate_configs(node_config: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = node_config.get("candidates")
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _evidence(mention: dict[str, Any], max_evidence: int) -> list[dict[str, Any]]:
    raw_evidence = mention.get("evidence")
    if not isinstance(raw_evidence, list):
        return []
    evidence: list[dict[str, Any]] = []
    for item in raw_evidence[:max_evidence]:
        if not isinstance(item, dict):
            continue
        evidence.append(
            {
                "segment_id": item.get("segment_id"),
                "start": item.get("start"),
                "end": item.get("end"),
                "timestamp": str(item.get("timestamp", "")),
                "text": str(item.get("text", "")),
            }
        )
    return evidence


def _extend_evidence(
    target: list[dict[str, Any]], source: list[dict[str, Any]], limit: int
) -> None:
    seen = {(item.get("segment_id"), item.get("timestamp")) for item in target}
    for item in source:
        key = (item.get("segment_id"), item.get("timestamp"))
        if key in seen:
            continue
        target.append(item)
        seen.add(key)
        if len(target) >= limit:
            return


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _normalize_key(value: str) -> str:
    stripped = value.strip()
    return stripped.lower() if stripped.isascii() else stripped


def _render_markdown(*, display_name: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {display_name} - {payload['episode_ref']} Industry Chain Mapping",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Episode: {payload['episode_ref']}",
        f"- Title: {payload['title']}",
        f"- Mapping mode: {payload['mapping_mode']}",
        f"- Mapping status: {payload['mapping_status']}",
        "",
        "## Warnings",
        "",
    ]
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- No warnings.")
    lines.extend(["", "## Industry Chain Nodes", ""])
    if not payload["industry_chain_nodes"]:
        lines.extend(["No matched industry chain nodes.", ""])
    for node in payload["industry_chain_nodes"]:
        lines.extend([f"### {node['label']} ({node['node_id']})", ""])
        lines.append(f"- Source terms: {', '.join(node['source_terms'])}")
        for candidate in node["stock_candidates"]:
            tickers = ", ".join(candidate["tickers"]) if candidate["tickers"] else "unverified"
            lines.append(
                f"- {candidate['company_name']} [{tickers}] "
                f"{candidate['evidence_status']} / {candidate['verification_status']}"
            )
        lines.append("")
    lines.extend(["## Stock Candidates", ""])
    if not payload["stock_candidates"]:
        lines.extend(["No stock candidates generated.", ""])
    for candidate in payload["stock_candidates"]:
        tickers = ", ".join(candidate["tickers"]) if candidate["tickers"] else "unverified"
        timestamps = ", ".join(item["timestamp"] for item in candidate["evidence"])
        lines.append(
            f"- {candidate['company_name']} [{tickers}] "
            f"{candidate['evidence_status']} / {candidate['verification_status']}: {timestamps}"
        )
    lines.extend(
        [
            "",
            "## 注意事項",
            "",
            "本檔案不構成投資建議。",
            "inferred_from_industry candidates 是未查證研究線索，不代表 podcast 明確提到。",
            "本階段未查詢外部市場資料。",
            "",
        ]
    )
    return "\n".join(lines)


def _write_mapping(
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
        raise IndustryMappingFailedError(f"寫入 industry chain mapping 失敗：{exc}") from exc
