from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .canonical_transcript import resolve_canonical_transcript_asset_paths
from .config import load_podcast_profile
from .episode_claim import episode_writer_claimed
from .errors import (
    MentionExtractionFailedError,
    MentionExtractionInputError,
    TranscriptMissingError,
    TranscriptParseError,
)
from .models import Mention, MentionEvidence, MentionExtractionAsset
from .storage import mention_asset_paths
from .validator import validate_transcript

EXTRACTION_MODE = "deterministic-rules"
MENTION_RULES: dict[str, list[str]] = {
    "company": [
        "NVIDIA",
        "NVDA",
        "台積電",
        "TSMC",
        "Apple",
        "蘋果",
        "Microsoft",
        "微軟",
        "Google",
        "Alphabet",
        "Meta",
        "Amazon",
        "Tesla",
        "特斯拉",
        "OpenAI",
        "Anthropic",
    ],
    "industry": [
        "AI",
        "人工智慧",
        "半導體",
        "晶片",
        "GPU",
        "資料中心",
        "雲端",
        "電動車",
        "金融",
        "航運",
        "生技",
        "房地產",
    ],
    "macro_topic": [
        "通膨",
        "利率",
        "降息",
        "升息",
        "Fed",
        "聯準會",
        "CPI",
        "PCE",
        "非農",
        "就業",
        "美元",
        "日圓",
        "美債",
        "殖利率",
        "GDP",
        "景氣",
        "衰退",
    ],
    "crypto": [
        "Bitcoin",
        "BTC",
        "比特幣",
        "Ethereum",
        "ETH",
        "以太幣",
        "Solana",
        "SOL",
    ],
    "place": [
        "日本",
        "沖繩",
        "東京",
        "台灣",
        "美國",
        "中國",
        "香港",
        "新加坡",
        "韓國",
    ],
}
KNOWN_TICKERS = ["NVDA", "TSMC", "AAPL", "MSFT", "GOOGL", "META", "AMZN", "TSLA", "BTC", "ETH", "SOL"]
MARKDOWN_TYPE_ORDER = [
    "company",
    "stock_or_ticker",
    "industry",
    "macro_topic",
    "crypto",
    "place",
    "person",
    "book",
    "movie",
    "music",
    "restaurant",
    "product",
    "unknown",
]
MARKDOWN_TYPE_TITLES = {
    "company": "Company",
    "stock_or_ticker": "Stock / Ticker",
    "industry": "Industry",
    "macro_topic": "Macro Topic",
    "crypto": "Crypto",
    "place": "Place",
}


@episode_writer_claimed
def extract_mentions(
    podcast_id: str,
    episode_ref: str,
    *,
    force: bool = False,
    allow_partial: bool = False,
    max_evidence_per_mention: int = 5,
) -> MentionExtractionAsset:
    """從 transcript segments 擷取 deterministic mentions。"""

    if max_evidence_per_mention < 1:
        raise MentionExtractionInputError("max_evidence_per_mention 必須大於 0。")

    profile = load_podcast_profile(podcast_id)
    validation = validate_transcript(podcast_id, episode_ref)
    _raise_for_invalid_transcript(validation.status, validation.problems, allow_partial)

    transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    if transcript_paths is None:
        raise TranscriptMissingError(f"找不到逐字稿 JSON：{podcast_id}/{episode_ref}")

    payload = _load_transcript_payload(transcript_paths.json_path)
    title = _required_text(payload, "title")
    payload_podcast_id = _required_text(payload, "podcast_id")
    payload_episode_ref = _required_text(payload, "episode_ref")
    if payload_podcast_id != podcast_id or payload_episode_ref != episode_ref:
        raise TranscriptParseError("逐字稿 JSON 的 podcast_id 或 episode_ref 不符合請求。")

    segment_count = _required_int(payload, "segment_count")
    segments = _normalize_segments(payload.get("segments"))
    output_paths = mention_asset_paths(podcast_id, episode_ref, title)
    if output_paths.json_path.exists() and output_paths.markdown_path.exists() and not force:
        return MentionExtractionAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            source_transcript_json_path=transcript_paths.json_path,
            mentions_json_path=output_paths.json_path,
            mentions_markdown_path=output_paths.markdown_path,
            mention_count=_existing_mention_count(output_paths.json_path),
            segment_count=segment_count,
            extraction_mode=EXTRACTION_MODE,
            generated=False,
            already_exists=True,
        )

    mentions = _extract_from_segments(segments, max_evidence_per_mention)
    payload_out = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "extraction_mode": EXTRACTION_MODE,
        "generation_options": {"max_evidence_per_mention": max_evidence_per_mention},
        "segment_count": segment_count,
        "mention_count": len(mentions),
        "mentions": [_mention_to_dict(mention) for mention in mentions],
    }
    markdown = _render_markdown(
        display_name=profile.display_name,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        segment_count=segment_count,
        mentions=mentions,
    )
    _write_outputs(output_paths.json_path, output_paths.markdown_path, payload_out, markdown)

    return MentionExtractionAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        source_transcript_json_path=transcript_paths.json_path,
        mentions_json_path=output_paths.json_path,
        mentions_markdown_path=output_paths.markdown_path,
        mention_count=len(mentions),
        segment_count=segment_count,
        extraction_mode=EXTRACTION_MODE,
        generated=True,
        already_exists=False,
    )


def _raise_for_invalid_transcript(
    status: str, problems: list[str], allow_partial: bool
) -> None:
    details = "; ".join(problems)
    if status == "missing":
        raise TranscriptMissingError(f"找不到逐字稿：{details}")
    if status == "incomplete_outputs":
        raise TranscriptMissingError(f"逐字稿輸出不完整：{details}")
    if status == "corrupt":
        raise TranscriptParseError(f"逐字稿 JSON 格式錯誤：{details}")
    if status == "partial" and not allow_partial:
        raise TranscriptParseError("transcript validation status is partial；請使用 --allow-partial。")


def _load_transcript_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TranscriptParseError(f"逐字稿 JSON 格式錯誤：{json_path}") from exc
    except OSError as exc:
        raise TranscriptMissingError(f"無法讀取逐字稿 JSON：{exc}") from exc
    if not isinstance(payload, dict):
        raise TranscriptParseError("逐字稿 JSON 必須是 object。")
    return payload


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TranscriptParseError(f"逐字稿 JSON 缺少有效欄位：{key}")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise TranscriptParseError(f"逐字稿 JSON 缺少有效欄位：{key}")
    return value


def _normalize_segments(raw_segments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_segments, list):
        raise TranscriptParseError("逐字稿 JSON 的 segments 必須是 list。")

    segments: list[dict[str, Any]] = []
    for index, segment in enumerate(raw_segments, start=1):
        if not isinstance(segment, dict):
            raise TranscriptParseError("逐字稿 JSON 的每個 segment 必須是 object。")
        try:
            start = float(segment["start"])
            end = float(segment["end"])
            text = str(segment.get("text", "")).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise TranscriptParseError("逐字稿 segment 缺少 start、end 或 text。") from exc
        segments.append(
            {
                "id": segment.get("id", index),
                "start": start,
                "end": end,
                "text": text,
            }
        )
    return segments


def _extract_from_segments(
    segments: list[dict[str, Any]], max_evidence_per_mention: int
) -> list[Mention]:
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for segment in segments:
        if not segment["text"]:
            continue
        for mention_type, terms in MENTION_RULES.items():
            for term in terms:
                _record_term_matches(
                    found,
                    mention_type,
                    term,
                    segment,
                    max_evidence_per_mention,
                )
        for ticker in KNOWN_TICKERS:
            _record_term_matches(
                found,
                "stock_or_ticker",
                ticker,
                segment,
                max_evidence_per_mention,
            )

    mentions = [
        Mention(
            type=value["type"],
            text=value["text"],
            normalized_text=value["normalized_text"],
            evidence=value["evidence"],
            count=value["count"],
            confidence="rule",
        )
        for value in found.values()
    ]
    return sorted(
        mentions,
        key=lambda mention: (
            MARKDOWN_TYPE_ORDER.index(mention.type)
            if mention.type in MARKDOWN_TYPE_ORDER
            else len(MARKDOWN_TYPE_ORDER),
            mention.normalized_text,
        ),
    )


def _record_term_matches(
    found: dict[tuple[str, str], dict[str, Any]],
    mention_type: str,
    term: str,
    segment: dict[str, Any],
    max_evidence_per_mention: int,
) -> None:
    matches = list(_find_term_matches(segment["text"], term))
    if not matches:
        return
    normalized_text = _normalize_mention_text(term)
    key = (mention_type, normalized_text)
    if key not in found:
        found[key] = {
            "type": mention_type,
            "text": term,
            "normalized_text": normalized_text,
            "evidence": [],
            "count": 0,
        }
    entry = found[key]
    entry["count"] += len(matches)
    for _match in matches:
        if len(entry["evidence"]) >= max_evidence_per_mention:
            break
        entry["evidence"].append(
            MentionEvidence(
                segment_id=segment["id"],
                start=segment["start"],
                end=segment["end"],
                timestamp=f"[{_format_clock(segment['start'])} - {_format_clock(segment['end'])}]",
                text=segment["text"],
            )
        )


def _find_term_matches(text: str, term: str):
    if term.isascii() and term.replace("-", "").isalnum():
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)
        yield from pattern.finditer(text)
        return
    start = 0
    while True:
        index = text.find(term, start)
        if index < 0:
            return
        yield re.match(re.escape(term), text[index : index + len(term)])
        start = index + len(term)


def _normalize_mention_text(text: str) -> str:
    stripped = text.strip()
    if stripped.isascii():
        return stripped.lower()
    return stripped


def _mention_to_dict(mention: Mention) -> dict[str, Any]:
    data = asdict(mention)
    return data


def _existing_mention_count(json_path: Path) -> int:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    count = payload.get("mention_count")
    return count if isinstance(count, int) else 0


def _render_markdown(
    *,
    display_name: str,
    podcast_id: str,
    episode_ref: str,
    title: str,
    segment_count: int,
    mentions: list[Mention],
) -> str:
    lines = [
        f"# {display_name} - {episode_ref} Mentions",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {podcast_id}",
        f"- Episode: {episode_ref}",
        f"- Title: {title}",
        f"- Extraction mode: {EXTRACTION_MODE}",
        f"- Segment count: {segment_count}",
        f"- Mention count: {len(mentions)}",
        "",
        "## 注意事項",
        "",
        "本檔案由 deterministic rules 產生，不代表完整語意理解。",
        "所有 mention 必須回到 timestamp evidence。",
        "本檔案不構成投資建議。",
        "",
    ]
    for mention_type in MARKDOWN_TYPE_ORDER:
        if mention_type in {"person", "book", "movie", "music", "restaurant", "product", "unknown"}:
            continue
        title_text = MARKDOWN_TYPE_TITLES.get(mention_type, mention_type.title())
        lines.extend(_mention_table(title_text, [m for m in mentions if m.type == mention_type]))

    other_mentions = [
        mention
        for mention in mentions
        if mention.type not in {"company", "stock_or_ticker", "industry", "macro_topic", "crypto", "place"}
    ]
    lines.extend(_mention_table("Other Mentions", other_mentions))
    return "\n".join(lines)


def _mention_table(title: str, mentions: list[Mention]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Mention | Count | Evidence |",
        "|---|---:|---|",
    ]
    if not mentions:
        lines.append("|  | 0 |  |")
    else:
        for mention in mentions:
            evidence = "<br>".join(
                f"{item.timestamp} {item.text}" for item in mention.evidence
            )
            lines.append(f"| {mention.text} | {mention.count} | {evidence} |")
    lines.append("")
    return lines


def _write_outputs(
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
        raise MentionExtractionFailedError(f"寫入 mention extraction 輸出失敗：{exc}") from exc


def _format_clock(seconds: float) -> str:
    whole_seconds = max(0, int(seconds))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
