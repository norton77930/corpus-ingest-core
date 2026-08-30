from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .canonical_transcript import resolve_canonical_transcript_asset_paths
from .config import load_podcast_profile
from .episode_claim import episode_writer_claimed
from .errors import (
    EpisodeIntelligenceReportFailedError,
    TranscriptMissingError,
    TranscriptParseError,
)
from .models import EpisodeIntelligenceReportAsset
from .storage import (
    episode_intelligence_report_asset_paths,
    mention_asset_paths,
)
from .validator import validate_transcript

REPORT_MODE = "deterministic-episode-intelligence-v1"


@episode_writer_claimed
def generate_episode_intelligence_report(
    podcast_id: str,
    episode_ref: str,
    *,
    force: bool = False,
    allow_partial: bool = False,
    window_seconds: int = 300,
    max_evidence_per_section: int = 5,
) -> EpisodeIntelligenceReportAsset:
    """從既有 transcript 與 mentions artifact 產生 deterministic episode intelligence report。"""

    if window_seconds < 1:
        raise ValueError("window_seconds must be greater than 0.")
    if max_evidence_per_section < 1:
        raise ValueError("max_evidence_per_section must be greater than 0.")

    profile = load_podcast_profile(podcast_id)
    validation = validate_transcript(podcast_id, episode_ref)
    _raise_for_invalid_transcript(validation.status, validation.problems, allow_partial)

    transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    if transcript_paths is None:
        raise TranscriptMissingError(f"Transcript JSON not found: {podcast_id}/{episode_ref}")

    payload = _load_transcript_payload(transcript_paths.json_path)
    title = _required_text(payload, "title")
    payload_podcast_id = _required_text(payload, "podcast_id")
    payload_episode_ref = _required_text(payload, "episode_ref")
    if payload_podcast_id != podcast_id or payload_episode_ref != episode_ref:
        raise TranscriptParseError("The transcript JSON's podcast_id or episode_ref does not match the request.")

    segment_count = _required_int(payload, "segment_count")
    segments = _normalize_segments(payload.get("segments"))
    report_paths = episode_intelligence_report_asset_paths(podcast_id, episode_ref, title)
    mentions, mentions_status, source_warnings = _load_mentions(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
    )
    source_warnings.extend(validation.warnings)

    if report_paths.json_path.exists() and report_paths.markdown_path.exists() and not force:
        return EpisodeIntelligenceReportAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            report_json_path=report_paths.json_path,
            report_markdown_path=report_paths.markdown_path,
            transcript_status=validation.status,
            segment_count=segment_count,
            generated=False,
            already_exists=True,
            source_status_warnings=source_warnings,
        )

    mentions_by_type = _mentions_by_type(mentions, max_evidence_per_section)
    report_status = "partial-draft" if validation.status == "partial" else "final"
    timeline = _timeline(segments, window_seconds, max_evidence_per_section)
    risks = _risks_and_uncertainties(validation.status, mentions_status, source_warnings)
    report_payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "report_mode": REPORT_MODE,
        "generation_options": {
            "window_seconds": window_seconds,
            "max_evidence_per_section": max_evidence_per_section,
        },
        "report_status": report_status,
        "source_status": {
            "transcript": validation.status,
            "mentions": mentions_status,
        },
        "transcript_validation": {
            "status": validation.status,
            "valid": validation.valid,
            "segment_count": validation.segment_count,
            "last_segment_end_seconds": validation.last_segment_end_seconds,
            "problems": validation.problems,
            "warnings": validation.warnings,
        },
        "episode_overview": {
            "podcast": profile.display_name,
            "segment_count": segment_count,
            "estimated_duration": _estimated_duration(segments),
            "non_empty_segment_count": len([segment for segment in segments if segment["text"]]),
        },
        "timeline": timeline,
        "mentions_by_type": mentions_by_type,
        "industry_clues": mentions_by_type.get("industry", []),
        "macro_variables": mentions_by_type.get("macro_topic", []),
        "risks_and_uncertainties": risks,
        "not_investment_advice": True,
    }
    markdown = _render_markdown(
        display_name=profile.display_name,
        payload=report_payload,
        source_warnings=source_warnings,
    )
    _write_report(report_paths.json_path, report_paths.markdown_path, report_payload, markdown)

    return EpisodeIntelligenceReportAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        transcript_status=validation.status,
        segment_count=segment_count,
        generated=True,
        already_exists=False,
        source_status_warnings=source_warnings,
    )


def _raise_for_invalid_transcript(status: str, problems: list[str], allow_partial: bool) -> None:
    details = "; ".join(problems)
    if status == "missing":
        raise TranscriptMissingError(f"Transcript not found: {details}")
    if status == "incomplete_outputs":
        raise TranscriptMissingError(f"Transcript output is incomplete: {details}")
    if status == "corrupt":
        raise TranscriptParseError(f"Malformed transcript JSON: {details}")
    if status == "partial" and not allow_partial:
        raise TranscriptParseError("transcript validation status is partial; pass --allow-partial to proceed.")


def _load_transcript_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TranscriptParseError(f"Malformed transcript JSON: {json_path}") from exc
    except OSError as exc:
        raise TranscriptMissingError(f"Could not read the transcript JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise TranscriptParseError("The transcript JSON must be an object.")
    return payload


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TranscriptParseError(f"Transcript JSON is missing a valid field: {key}")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise TranscriptParseError(f"Transcript JSON is missing a valid field: {key}")
    return value


def _normalize_segments(raw_segments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_segments, list):
        raise TranscriptParseError("The transcript JSON's segments must be a list.")

    segments: list[dict[str, Any]] = []
    for index, segment in enumerate(raw_segments, start=1):
        if not isinstance(segment, dict):
            raise TranscriptParseError("Every segment in the transcript JSON must be an object.")
        try:
            start = float(segment["start"])
            end = float(segment["end"])
            text = str(segment.get("text", "")).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise TranscriptParseError("A transcript segment is missing start, end, or text.") from exc
        segments.append(
            {
                "id": segment.get("id", index),
                "start": start,
                "end": end,
                "text": text,
            }
        )
    return segments


def _load_mentions(
    *,
    podcast_id: str,
    episode_ref: str,
    title: str,
) -> tuple[list[dict[str, Any]], str, list[str]]:
    paths = mention_asset_paths(podcast_id, episode_ref, title)
    if not paths.json_path.exists():
        return [], "missing", [f"mentions artifact missing: {paths.json_path}"]
    try:
        payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], "unavailable", [f"mentions artifact unreadable: {exc}"]
    mentions = payload.get("mentions")
    if not isinstance(mentions, list):
        return [], "unavailable", ["mentions artifact has invalid mentions list"]
    return [mention for mention in mentions if isinstance(mention, dict)], "available", []


def _mentions_by_type(mentions: list[dict[str, Any]], max_evidence_per_section: int) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mention in mentions:
        mention_type = str(mention.get("type", "unknown"))
        grouped[mention_type].append(_trim_mention(mention, max_evidence_per_section))
    return {key: grouped[key] for key in sorted(grouped)}


def _trim_mention(mention: dict[str, Any], max_evidence_per_section: int) -> dict[str, Any]:
    evidence = mention.get("evidence")
    return {
        "type": str(mention.get("type", "unknown")),
        "text": str(mention.get("text", "")),
        "normalized_text": str(mention.get("normalized_text", "")),
        "count": mention.get("count", 0),
        "confidence": mention.get("confidence", ""),
        "evidence": evidence[:max_evidence_per_section] if isinstance(evidence, list) else [],
    }


def _timeline(
    segments: list[dict[str, Any]],
    window_seconds: int,
    max_evidence_per_section: int,
) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for segment in segments:
        if not segment["text"]:
            continue
        window_start = int(segment["start"] // window_seconds) * window_seconds
        grouped[window_start].append(segment)

    timeline: list[dict[str, Any]] = []
    for window_start in sorted(grouped):
        window_end = window_start + window_seconds
        timeline.append(
            {
                "window_start_seconds": window_start,
                "window_end_seconds": window_end,
                "timestamp": f"[{_format_clock(window_start)} - {_format_clock(window_end)}]",
                "evidence": [
                    _segment_evidence(segment) for segment in grouped[window_start][:max_evidence_per_section]
                ],
            }
        )
    return timeline


def _segment_evidence(segment: dict[str, Any]) -> dict[str, Any]:
    return {
        "segment_id": segment["id"],
        "start": segment["start"],
        "end": segment["end"],
        "timestamp": f"[{_format_clock(segment['start'])} - {_format_clock(segment['end'])}]",
        "text": segment["text"],
    }


def _risks_and_uncertainties(
    transcript_status: str,
    mentions_status: str,
    source_warnings: list[str],
) -> list[str]:
    risks: list[str] = []
    if transcript_status == "partial":
        risks.append("partial transcript: report is a draft and formal conclusions are downgraded.")
    if mentions_status != "available":
        risks.append("mentions artifact is not available; mention-derived sections may be incomplete.")
    risks.extend(source_warnings)
    if not risks:
        risks.append("No external market data was checked; this report only summarizes podcast evidence.")
    return risks


def _render_markdown(
    *,
    display_name: str,
    payload: dict[str, Any],
    source_warnings: list[str],
) -> str:
    lines = [
        f"# {display_name} - {payload['episode_ref']} Episode Intelligence Report",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Episode: {payload['episode_ref']}",
        f"- Title: {payload['title']}",
        f"- Report mode: {REPORT_MODE}",
        f"- Report status: {payload['report_status']}",
        f"- Transcript status: {payload['transcript_validation']['status']}",
        f"- Transcript segments: {payload['transcript_validation']['segment_count']}",
        "",
        "## Source Status",
        "",
        f"- Transcript: {payload['source_status']['transcript']}",
        f"- Mentions: {payload['source_status']['mentions']}",
        "",
    ]
    if source_warnings:
        lines.extend(["## Source Warnings", ""])
        lines.extend(f"- {warning}" for warning in source_warnings)
        lines.append("")

    lines.extend(["## Episode Overview", ""])
    overview = payload["episode_overview"]
    lines.extend(
        [
            f"- Estimated duration: {overview['estimated_duration']}",
            f"- Non-empty transcript segments: {overview['non_empty_segment_count']}",
            "",
            "## Timeline Evidence",
            "",
        ]
    )
    if not payload["timeline"]:
        lines.extend(["No transcript evidence segments available.", ""])
    else:
        for window in payload["timeline"]:
            lines.extend([f"### {window['timestamp']}", ""])
            for evidence in window["evidence"]:
                lines.append(f"- `{evidence['timestamp']}` {evidence['text']}")
            lines.append("")

    lines.extend(["## Explicit Mentions", ""])
    if not payload["mentions_by_type"]:
        lines.extend(["No deterministic mentions artifact was available.", ""])
    else:
        for mention_type, mentions in payload["mentions_by_type"].items():
            lines.extend([f"### {mention_type}", ""])
            for mention in mentions:
                timestamps = ", ".join(str(item.get("timestamp", "")) for item in mention["evidence"])
                lines.append(f"- {mention['text']} ({mention['count']}): {timestamps}")
            lines.append("")

    lines.extend(["## Industry Clues", ""])
    lines.extend(_mention_bullets(payload["industry_clues"]))
    lines.extend(["## Macro Variables", ""])
    lines.extend(_mention_bullets(payload["macro_variables"]))
    lines.extend(["## Risks And Uncertainties", ""])
    lines.extend(f"- {risk}" for risk in payload["risks_and_uncertainties"])
    lines.extend(
        [
            "",
            "## 注意事項",
            "",
            "本報告不構成投資建議。",
            "本報告只整理 podcast evidence，未查證外部市場資料。",
            "",
        ]
    )
    return "\n".join(lines)


def _mention_bullets(mentions: list[dict[str, Any]]) -> list[str]:
    if not mentions:
        return ["No evidence in deterministic mentions.", ""]
    lines: list[str] = []
    for mention in mentions:
        timestamps = ", ".join(str(item.get("timestamp", "")) for item in mention["evidence"])
        lines.append(f"- {mention['text']}: {timestamps}")
    lines.append("")
    return lines


def _estimated_duration(segments: list[dict[str, Any]]) -> str:
    if not segments:
        return "0 秒"
    return _format_clock(max(segment["end"] for segment in segments))


def _format_clock(seconds: float) -> str:
    whole_seconds = max(0, int(seconds))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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
        raise EpisodeIntelligenceReportFailedError(f"Failed to write the episode intelligence report: {exc}") from exc
