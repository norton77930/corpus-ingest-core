from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import storage
from .config import load_podcast_profile
from .errors import (
    LLMProviderConfigError,
    LLMProviderRequestError,
    StockLensSynthesisFailedError,
    StockLensSynthesisInputError,
)
from .llm_provider import SemanticSummaryProvider, create_provider
from .local_env_names import (
    STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH_ENV as DEBUG_OUTPUT_PATH_ENV,
)
from .local_env_names import (
    read_env,
)
from .models import StockLensSynthesisResult
from .report_safety import strip_safety_disclaimers
from .semantic_summarizer import SEMANTIC_API_COST_ACK
from .storage import EVALS_RESEARCH_SMOKE_REPORTS_DIR as SEMANTIC_REVIEW_REPORTS_DIR
from .summary_profiles import FINANCE

SYNTHESIS_MODE = "llm-stock-lens-synthesis-v1"
SOURCE_REPORT_MODE = "deterministic-stock-lens-v1"
INPUT_BOUNDARY = "phase-6f-stock-lens-json-only"
REVIEWED_SEMANTIC_INPUT_BOUNDARY = "phase-6f-stock-lens-json-plus-reviewed-semantic-summary"

SEMANTIC_CONTEXT_TRUNCATION_MARKER = "\n[semantic context truncated]"
_SECRET_LIKE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
RISKS = [
    "Calls an external LLM API",
    "May incur API cost risk",
    "Uses only Phase 6F stock lens JSON as LLM input",
    "Does not use raw transcript text or semantic summary files",
    "Does not fetch external market data",
]


def require_finance_summary_profile(podcast_id: str) -> None:
    """Refuse stock-lens synthesis unless the podcast's summary shape is finance."""

    try:
        profile = load_podcast_profile(podcast_id)
    except KeyError as exc:
        raise StockLensSynthesisInputError(f"podcast profile not found: {podcast_id}") from exc
    if profile.summary_profile != FINANCE:
        raise StockLensSynthesisInputError(
            f"{podcast_id} summary_profile is {profile.summary_profile}, not {FINANCE}. "
            "stock lens synthesis only accepts finance-shaped summaries."
        )


PROHIBITED_ADVICE_PATTERNS = [
    ("trade_action", re.compile(r"\b(?:buy|sell|hold)\b", re.IGNORECASE)),
    (
        "target_price",
        re.compile(r"\btarget\s+price\s*(?:of|is|:)?\s*\$?\d", re.IGNORECASE),
    ),
    (
        "guaranteed_return",
        re.compile(r"\bguaranteed\s+returns?\s*(?:of|is|:)?\s*\d", re.IGNORECASE),
    ),
    (
        "trade_action",
        re.compile(r"(?:建議|不建議|應該|可以|可考慮|不要)?\s*(?:買進|賣出|持有)"),
    ),
    (
        "target_price",
        re.compile(r"目標價\s*(?:為|是|:|：)?\s*[\d一二三四五六七八九十百千萬]"),
    ),
    ("guaranteed_return", re.compile(r"保證報酬")),
]


def generate_stock_lens_synthesis_report(
    podcast_id: str,
    stock_query: str,
    *,
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    max_prompt_chars: int = 24000,
    include_semantic_context: bool = False,
    semantic_context_max_chars: int = 12000,
    require_semantic_review: bool = True,
) -> StockLensSynthesisResult:
    """從 Phase 6F stock lens JSON 產生 LLM synthesis artifact。"""

    if not stock_query.strip():
        raise ValueError("stock_query 必須是非空字串。")
    if max_prompt_chars < 1:
        raise ValueError("max_prompt_chars 必須大於 0。")
    if semantic_context_max_chars < 1:
        raise ValueError("semantic_context_max_chars 必須大於 0。")
    require_finance_summary_profile(podcast_id)

    source_paths = storage.stock_lens_report_asset_paths(podcast_id, stock_query)
    synthesis_paths = storage.stock_lens_synthesis_asset_paths(podcast_id, stock_query)
    planned_reads = [str(source_paths.json_path)]
    if include_semantic_context:
        planned_reads.extend(
            [
                str(storage.SUMMARIES_DIR / storage.title_slug(podcast_id, "podcast") / "*.semantic.md"),
                str(
                    SEMANTIC_REVIEW_REPORTS_DIR
                    / f"*__{storage.title_slug(podcast_id, 'podcast')}__*.semantic-review.json"
                ),
            ]
        )
    planned_writes = [str(synthesis_paths.json_path), str(synthesis_paths.markdown_path)]

    source_payload = _load_source_payload(source_paths.json_path, required=confirm)
    source_report_status = _source_report_status(source_payload)

    if not confirm:
        return _result(
            podcast_id=podcast_id,
            stock_query=stock_query,
            synthesis_paths=synthesis_paths,
            source_json_path=source_paths.json_path,
            synthesis_status="planned" if source_payload is not None else "blocked",
            source_report_status=source_report_status,
            dry_run=True,
            requires_confirmation=source_payload is not None,
            requires_api_cost_ack=True,
            required_acknowledgement=SEMANTIC_API_COST_ACK,
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            generated=False,
            already_exists=False,
            provider=provider,
            model=model,
            prompt_char_count=None,
            warning_count=0,
        )

    _raise_for_missing_ack(api_cost_ack)
    if source_payload is None:
        raise StockLensSynthesisInputError(f"stock lens report missing: {source_paths.json_path}")
    _validate_source_payload(source_payload, allow_partial=allow_partial)
    source_report_status = _required_text(source_payload, "report_status")
    synthesis_status = _synthesis_status(source_report_status)

    if synthesis_paths.json_path.exists() and synthesis_paths.markdown_path.exists() and not force:
        existing = _load_existing_synthesis(synthesis_paths.json_path)
        return _result(
            podcast_id=podcast_id,
            stock_query=stock_query,
            synthesis_paths=synthesis_paths,
            source_json_path=source_paths.json_path,
            synthesis_status=existing.get("synthesis_status", synthesis_status),
            source_report_status=source_report_status,
            dry_run=False,
            requires_confirmation=False,
            requires_api_cost_ack=False,
            required_acknowledgement=None,
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            generated=False,
            already_exists=True,
            provider=existing.get("provider"),
            model=existing.get("model"),
            prompt_char_count=existing.get("prompt_char_count"),
            warning_count=int(existing.get("warning_count", 0)),
        )

    semantic_context, semantic_context_warnings = _semantic_context_for_source(
        source_payload,
        include_semantic_context=include_semantic_context,
        semantic_context_max_chars=semantic_context_max_chars,
        require_semantic_review=require_semantic_review,
    )
    compact_source = _compact_source_payload(
        source_payload,
        semantic_context=semantic_context,
    )
    messages = _messages_for_source(compact_source)
    prompt_char_count = sum(len(message["content"]) for message in messages)
    if prompt_char_count > max_prompt_chars:
        raise StockLensSynthesisInputError(
            f"stock lens synthesis prompt exceeds max_prompt_chars: {prompt_char_count} > {max_prompt_chars}"
        )

    llm_provider = _build_provider(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        api_cost_ack=api_cost_ack,
    )
    try:
        synthesis_text = llm_provider.complete(messages)
    except (LLMProviderConfigError, LLMProviderRequestError):
        raise
    except Exception as exc:
        raise StockLensSynthesisFailedError(f"stock lens synthesis failed: {exc}") from exc
    _write_debug_output_if_requested(synthesis_text)
    _raise_for_prohibited_output(synthesis_text)

    payload = {
        "podcast_id": podcast_id,
        "stock_query": stock_query,
        "synthesis_mode": SYNTHESIS_MODE,
        "synthesis_status": synthesis_status,
        "source_report_mode": SOURCE_REPORT_MODE,
        "source_report_status": source_report_status,
        "source_stock_lens_json_path": str(source_paths.json_path),
        "llm_input_boundary": (REVIEWED_SEMANTIC_INPUT_BOUNDARY if semantic_context else INPUT_BOUNDARY),
        "provider": getattr(llm_provider, "provider_name", provider),
        "model": getattr(llm_provider, "model", model),
        "prompt_char_count": prompt_char_count,
        "source_query_match_summary": compact_source["query_match_summary"],
        "source_direct_podcast_evidence": compact_source["direct_podcast_evidence"],
        "source_inferred_research_leads": compact_source["inferred_research_leads"],
        "source_external_verification_needs": compact_source["external_verification_needs"],
        "source_semantic_context": compact_source["reviewed_semantic_context"],
        "source_warnings": compact_source["warnings"],
        "synthesis_text": synthesis_text,
        "warnings": _warnings_for_source(
            source_report_status,
            compact_source,
            semantic_context_warnings=semantic_context_warnings,
        ),
        "not_investment_advice": True,
    }
    markdown = _render_markdown(payload)
    _write_synthesis(synthesis_paths.json_path, synthesis_paths.markdown_path, payload, markdown)

    return _result(
        podcast_id=podcast_id,
        stock_query=stock_query,
        synthesis_paths=synthesis_paths,
        source_json_path=source_paths.json_path,
        synthesis_status=synthesis_status,
        source_report_status=source_report_status,
        dry_run=False,
        requires_confirmation=False,
        requires_api_cost_ack=False,
        required_acknowledgement=None,
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        generated=True,
        already_exists=False,
        provider=payload["provider"],
        model=payload["model"],
        prompt_char_count=prompt_char_count,
        warning_count=len(payload["warnings"]),
    )


def _build_provider(
    *,
    provider: str,
    model: str | None,
    base_url: str | None,
    api_key_env: str,
    api_cost_ack: str,
) -> SemanticSummaryProvider:
    return create_provider(
        provider,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        api_cost_ack=api_cost_ack,
    )


def _raise_for_missing_ack(api_cost_ack: str) -> None:
    if api_cost_ack != SEMANTIC_API_COST_ACK:
        raise StockLensSynthesisInputError(f"stock lens synthesis requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}")


def _load_source_payload(json_path: Path, *, required: bool) -> dict[str, Any] | None:
    if not json_path.exists():
        if required:
            raise StockLensSynthesisInputError(f"stock lens report missing: {json_path}")
        return None
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StockLensSynthesisInputError(f"stock lens JSON 格式錯誤：{json_path}") from exc
    except OSError as exc:
        raise StockLensSynthesisInputError(f"無法讀取 stock lens report：{exc}") from exc
    if not isinstance(payload, dict):
        raise StockLensSynthesisInputError("stock lens JSON 必須是 object。")
    return payload


def _source_report_status(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "missing"
    status = payload.get("report_status")
    return status if isinstance(status, str) and status.strip() else "unknown"


def _validate_source_payload(payload: dict[str, Any], *, allow_partial: bool) -> None:
    if _required_text(payload, "report_mode") != SOURCE_REPORT_MODE:
        raise StockLensSynthesisInputError("stock lens report_mode 不支援。")
    status = _required_text(payload, "report_status")
    if status == "partial-draft":
        if not allow_partial:
            raise StockLensSynthesisInputError("stock lens report status is partial-draft；請使用 --allow-partial。")
    elif status not in {"final", "no-direct-podcast-evidence"}:
        raise StockLensSynthesisInputError(f"stock lens report_status 不支援：{status}")
    _required_text(payload, "podcast_id")
    _required_text(payload, "stock_query")
    for key in (
        "query_match_summary",
        "direct_podcast_evidence",
        "inferred_research_leads",
        "gooaye_lens",
        "external_verification_needs",
    ):
        if key not in payload:
            raise StockLensSynthesisInputError(f"stock lens report 缺少欄位：{key}")


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StockLensSynthesisInputError(f"stock lens synthesis input 缺少有效欄位：{key}")
    return value


def _synthesis_status(source_report_status: str) -> str:
    if source_report_status == "partial-draft":
        return "partial-draft"
    if source_report_status == "no-direct-podcast-evidence":
        return "no-direct-podcast-evidence"
    return "final"


def _compact_source_payload(
    payload: dict[str, Any],
    *,
    semantic_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lens = _dict(payload.get("gooaye_lens"))
    return {
        "podcast_id": payload["podcast_id"],
        "stock_query": payload["stock_query"],
        "report_status": payload["report_status"],
        "query_match_summary": _dict(payload.get("query_match_summary")),
        "direct_podcast_evidence": _list_of_dicts(payload.get("direct_podcast_evidence")),
        "inferred_research_leads": _list_of_dicts(payload.get("inferred_research_leads")),
        "gooaye_lens": {
            "name": lens.get("name"),
            "version": lens.get("version"),
            "dimensions": _list_of_dicts(lens.get("dimensions")),
            "safety_rules": _string_list(lens.get("safety_rules")),
        },
        "external_verification_needs": _list_of_dicts(payload.get("external_verification_needs")),
        "reviewed_semantic_context": semantic_context or [],
        "warnings": _string_list(payload.get("warnings")),
        "not_investment_advice": payload.get("not_investment_advice") is True,
    }


def _semantic_context_for_source(
    payload: dict[str, Any],
    *,
    include_semantic_context: bool,
    semantic_context_max_chars: int,
    require_semantic_review: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not include_semantic_context:
        return [], []

    contexts: list[dict[str, Any]] = []
    warnings: list[str] = []
    remaining_chars = semantic_context_max_chars
    podcast_id = _required_text(payload, "podcast_id")

    for episode_ref in _episode_refs_from_source(payload):
        if remaining_chars <= 0:
            warnings.append("semantic context truncated because max chars was reached")
            break

        summary_path = _find_semantic_summary_path(podcast_id, episode_ref)
        if summary_path is None:
            warnings.append(f"semantic summary missing: {episode_ref}")
            continue

        review_path: Path | None = None
        review_status = "not_required"
        if require_semantic_review:
            review_payload, review_path, review_warning = _latest_semantic_review(
                podcast_id,
                episode_ref,
            )
            if review_warning:
                warnings.append(review_warning)
                continue
            review_status = str(review_payload.get("review_status", "")).strip()
            if review_status != "passed":
                warnings.append(f"semantic review not passed: {episode_ref}")
                continue

        content, extraction_warnings = _extract_semantic_context(summary_path)
        warnings.extend(f"semantic context {episode_ref}: {warning}" for warning in extraction_warnings)
        if not content:
            warnings.append(f"semantic context empty: {episode_ref}")
            continue

        if len(content) > remaining_chars:
            keep_chars = max(0, remaining_chars)
            content = content[:keep_chars].rstrip() + SEMANTIC_CONTEXT_TRUNCATION_MARKER
            warnings.append("semantic context truncated because max chars was reached")
            remaining_chars = 0
        else:
            remaining_chars -= len(content)

        contexts.append(
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "semantic_summary_path": str(summary_path),
                "semantic_review_path": str(review_path) if review_path else None,
                "review_status": review_status,
                "content": content,
            }
        )

    return contexts, warnings


def _episode_refs_from_source(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for collection_key in ("direct_podcast_evidence", "inferred_research_leads"):
        for item in _list_of_dicts(payload.get(collection_key)):
            episode_ref = item.get("episode_ref")
            if isinstance(episode_ref, str) and episode_ref.strip():
                normalized = episode_ref.strip()
                if normalized not in refs:
                    refs.append(normalized)
            for evidence in _list_of_dicts(item.get("evidence")):
                episode_ref = evidence.get("episode_ref")
                if isinstance(episode_ref, str) and episode_ref.strip():
                    normalized = episode_ref.strip()
                    if normalized not in refs:
                        refs.append(normalized)
    return refs


def _find_semantic_summary_path(podcast_id: str, episode_ref: str) -> Path | None:
    summary_dir = storage.SUMMARIES_DIR / storage.title_slug(podcast_id, "podcast")
    safe_ref = storage.title_slug(episode_ref, "episode")
    matches = sorted(summary_dir.glob(f"{safe_ref}__*.semantic.md"))
    if not matches:
        return None
    return matches[0]


def _latest_semantic_review(
    podcast_id: str,
    episode_ref: str,
) -> tuple[dict[str, Any], Path | None, str | None]:
    safe_podcast = storage.title_slug(podcast_id, "podcast")
    safe_episode = storage.title_slug(episode_ref, "episode")
    matches = sorted(SEMANTIC_REVIEW_REPORTS_DIR.glob(f"*__{safe_podcast}__{safe_episode}.semantic-review.json"))
    if not matches:
        return {}, None, f"semantic review missing: {episode_ref}"
    review_path = matches[-1]
    try:
        payload = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, review_path, f"semantic review unreadable: {episode_ref}"
    if not isinstance(payload, dict):
        return {}, review_path, f"semantic review unsupported: {episode_ref}"
    return payload, review_path, None


def _extract_semantic_context(summary_path: Path) -> tuple[str, list[str]]:
    try:
        text = summary_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StockLensSynthesisInputError(f"無法讀取 semantic summary context：{summary_path}") from exc

    before_chunks = re.split(r"(?im)^##\s+Chunk Summaries\s*$", text, maxsplit=1)[0]
    before_chunks = _SECRET_LIKE_PATTERN.sub("[redacted-secret]", before_chunks)
    warnings: list[str] = []
    if "[redacted-secret]" in before_chunks:
        warnings.append("secret-like value redacted from semantic context")
    return before_chunks.strip(), warnings


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _messages_for_source(compact_source: dict[str, Any]) -> list[dict[str, str]]:
    has_semantic_context = bool(compact_source.get("reviewed_semantic_context"))
    system_boundary = (
        "Phase 6F stock lens JSON 與 reviewed semantic summary context"
        if has_semantic_context
        else "Phase 6F stock lens JSON"
    )
    user_boundary = (
        "可使用 reviewed semantic summary context；它是通過 review 的 LLM intermediate artifact，"
        "不是 raw transcript，也不是外部市場事實。"
        if has_semantic_context
        else "不要加入逐字稿原文以外的猜測；不要引用 semantic summary artifact；不要查外部資料。"
    )
    return [
        {
            "role": "system",
            "content": (
                "你是 Gooaye stock lens synthesis writer。只能根據使用者提供的 "
                f"{system_boundary} 產生研究敘事。不得使用外部市場資料、不得假裝有 raw "
                "transcript、不得提供 buy/sell/hold、target price 或 guaranteed return。"
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "請根據以下 6F stock lens JSON 產生 Markdown synthesis。",
                    "必須清楚區分 direct podcast evidence、inferred research leads、external-data status。",
                    "`not_requested`、`not_fetched`、`data_date=null` 不是市場事實，只代表尚未查證。",
                    "若沒有 direct podcast evidence，必須明確說 no direct podcast evidence found。",
                    user_boundary,
                    "",
                    json.dumps(compact_source, ensure_ascii=False, indent=2),
                ]
            ),
        },
    ]


def _raise_for_prohibited_output(text: str) -> None:
    review_text = strip_safety_disclaimers(text)
    matched_guard = _matched_prohibited_guard(review_text)
    if matched_guard is not None:
        raise StockLensSynthesisInputError(
            f"LLM output appears to contain prohibited investment advice. matched_guard={matched_guard}"
        )


def _matched_prohibited_guard(text: str) -> str | None:
    for name, pattern in PROHIBITED_ADVICE_PATTERNS:
        if pattern.search(text):
            return name
    return None


def _write_debug_output_if_requested(text: str) -> None:
    raw_path = (read_env(DEBUG_OUTPUT_PATH_ENV) or "").strip()
    if not raw_path:
        return
    output_path = Path(raw_path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise StockLensSynthesisFailedError(f"failed to write debug LLM output: {output_path}") from exc


def _warnings_for_source(
    source_report_status: str,
    compact_source: dict[str, Any],
    *,
    semantic_context_warnings: list[str] | None = None,
) -> list[str]:
    warnings = list(compact_source["warnings"])
    warnings.extend(semantic_context_warnings or [])
    if source_report_status == "partial-draft":
        warnings.append("source stock lens report is partial-draft")
    if compact_source["query_match_summary"].get("no_direct_podcast_evidence") is True:
        warnings.append("no direct podcast evidence found")
    warnings.append("no raw transcript was used")
    warnings.append("no external market data was fetched")
    if compact_source.get("reviewed_semantic_context"):
        warnings.append("reviewed semantic summary context was used")
    return warnings


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['stock_query']} Stock Lens LLM Synthesis",
        "",
        "## Metadata",
        "",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Stock query: {payload['stock_query']}",
        f"- Synthesis mode: {payload['synthesis_mode']}",
        f"- Synthesis status: {payload['synthesis_status']}",
        f"- Source report status: {payload['source_report_status']}",
        f"- LLM input boundary: {payload['llm_input_boundary']}",
        "- raw transcript was not used",
        "- external market data was not fetched",
        "- reviewed semantic summary context may be used only when explicitly enabled and review-passed",
        "",
        "## Synthesis",
        "",
        payload["synthesis_text"],
        "",
        "## Source Status",
        "",
        f"- Direct podcast evidence: {payload['source_query_match_summary'].get('direct_podcast_evidence_count', 0)}",
        f"- Inferred research leads: {payload['source_query_match_summary'].get('inferred_research_lead_count', 0)}",
        "- External status values such as not_requested, not_fetched, and data_date=null are unavailable-data markers.",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in payload["warnings"])
    lines.extend(
        [
            "",
            "## 注意事項",
            "",
            "本報告不構成投資建議。",
            "No buy/sell/hold advice. No target price. No guaranteed returns.",
            (
                "This artifact is LLM-assisted synthesis over Phase 6F JSON and reviewed semantic summary context."
                if payload["source_semantic_context"]
                else "This artifact is LLM-assisted synthesis over Phase 6F JSON only."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _write_synthesis(
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
        raise StockLensSynthesisFailedError(f"寫入 stock lens synthesis 失敗：{exc}") from exc


def _load_existing_synthesis(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _result(
    *,
    podcast_id: str,
    stock_query: str,
    synthesis_paths: storage.StockLensSynthesisAssetPaths,
    source_json_path: Path,
    synthesis_status: str,
    source_report_status: str,
    dry_run: bool,
    requires_confirmation: bool,
    requires_api_cost_ack: bool,
    required_acknowledgement: str | None,
    planned_reads: list[str],
    planned_writes: list[str],
    generated: bool,
    already_exists: bool,
    provider: str | None,
    model: str | None,
    prompt_char_count: int | None,
    warning_count: int,
) -> StockLensSynthesisResult:
    return StockLensSynthesisResult(
        podcast_id=podcast_id,
        stock_query=stock_query,
        synthesis_json_path=synthesis_paths.json_path,
        synthesis_markdown_path=synthesis_paths.markdown_path,
        source_stock_lens_json_path=source_json_path,
        synthesis_status=synthesis_status,
        source_report_status=source_report_status,
        dry_run=dry_run,
        requires_confirmation=requires_confirmation,
        requires_api_cost_ack=requires_api_cost_ack,
        required_acknowledgement=required_acknowledgement,
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        risks=RISKS.copy(),
        generated=generated,
        already_exists=already_exists,
        provider=provider,
        model=model,
        prompt_char_count=prompt_char_count,
        warning_count=warning_count,
        not_investment_advice=True,
    )
