"""Dry-run-first study-guide bundle runner.

Reads an existing learning-notes semantic summary and writes 00/03/04/07.
Never sends transcript text to a provider.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
import shutil
from typing import Any

from . import storage
from .config import load_podcast_profile
from .errors import StudyGuideBundleError
from .llm_provider import create_provider, require_exact_api_cost_ack
from .models import StudyGuideBundleResult
from .report_safety import matched_investment_advice_guard
from .run_report_io import write_part_staged_report_pair
from .semantic_summary_identity import canonical_semantic_summary_path
from .study_guide_profiles import (
    BUNDLE_KEYS,
    COVER_FILENAME,
    FINANCE_HEADINGS,
    GUIDE_FILENAME,
    NOTES_FILENAME,
    STUDY_GUIDE_PROFILE,
    SUMMARY_FILENAME,
    WORKFLOW_MARKERS,
)
from .summary_profiles import LEARNING_NOTES


CACHE_STALE_WARNING = (
    "SQLite cache may be stale; rebuild cache manually. "
    "本流程不會自動重建。"
)
_CHUNK_SPLIT = re.compile(r"(?im)^##\s+Chunk Summaries\s*$")
_HEADING = re.compile(r"(?im)^#{1,3}\s*(?:\d+\.\s*)?(.+?)\s*$")
_TIMESTAMP = re.compile(r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]")
_CLOCK = re.compile(r"\b\d{2}:\d{2}:\d{2}\b")
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
_MAX_SOURCE_BYTES = 2 * 1024 * 1024
REQUIRED_PROFILE = LEARNING_NOTES


def run_study_guide_bundle(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
) -> StudyGuideBundleResult:
    """Plan or write one study-guide bundle for a learning-notes episode."""

    profile = load_podcast_profile(podcast_id)
    if profile.summary_profile != REQUIRED_PROFILE:
        raise StudyGuideBundleError(
            f"study-guide bundle requires summary_profile={REQUIRED_PROFILE}; "
            f"got {profile.summary_profile!r}"
        )

    source_path = canonical_semantic_summary_path(podcast_id, episode_ref)
    if source_path is None or not source_path.is_file():
        raise StudyGuideBundleError(
            "canonical learning-notes semantic summary is missing; "
            "generate it first — this runner does not create summaries"
        )

    source_text = _read_capped_utf8(source_path)
    if _is_finance_shaped(source_text):
        raise StudyGuideBundleError(
            "source semantic summary is finance-shaped; "
            "refusing to generate a study-guide bundle"
        )

    title = _episode_title(podcast_id, episode_ref, source_path)
    stem = source_path.name.removesuffix(".semantic.md")
    paths = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    file_map = _file_map(paths)
    existing_readable = {
        label
        for label, path in file_map.items()
        if path.is_file() and _is_readable(path)
    }
    lecture_complete = {"03", "04", "07"} <= existing_readable
    complete = existing_readable == {"00", "03", "04", "07"}
    reuse_all = complete and not force
    cover_only = lecture_complete and "00" not in existing_readable and not force
    if existing_readable and not reuse_all and not cover_only and not force:
        raise StudyGuideBundleError(
            "incomplete study-guide bundle; pass force=true to replace the whole set"
        )

    planned_reads = [str(source_path)]
    seed_path = storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)
    if seed_path.is_file():
        planned_reads.append(str(seed_path))
    audio_path = _find_audio(podcast_id, episode_ref)
    if audio_path is not None:
        planned_reads.append(str(audio_path))

    if reuse_all:
        planned_writes: list[str] = []
        planned_reuses = [str(path) for path in file_map.values()]
    elif cover_only:
        planned_writes = [str(file_map["00"])]
        planned_reuses = [str(file_map[label]) for label in ("03", "04", "07")]
    else:
        planned_writes = [str(path) for path in file_map.values()]
        planned_reuses = []

    if not confirm:
        return _result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            source_summary_path=str(source_path),
            bundle_dir=str(paths.bundle_dir),
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            planned_reuses=planned_reuses,
            output_paths={},
            report_json_path=None,
            report_markdown_path=None,
            reused=reuse_all,
            warnings=[CACHE_STALE_WARNING] if planned_writes else [],
        )

    generated = {
        "00": _render_cover(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            seed_path=seed_path,
            audio_path=audio_path,
        )
    }
    if reuse_all or cover_only:
        bodies = {
            "03": paths.summary_path.read_text(encoding="utf-8"),
            "04": paths.notes_path.read_text(encoding="utf-8"),
            "07": paths.guide_path.read_text(encoding="utf-8"),
        }
    else:
        require_exact_api_cost_ack(api_cost_ack)
        llm = create_provider(
            provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            reasoning_effort=reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            api_cost_ack=api_cost_ack,
        )
        raw = llm.complete(_build_messages(source_text))
        parsed = _parse_bundle_payload(raw)
        _validate_generated(parsed, source_text)
        bodies = {
            "03": parsed["03_full_summary"],
            "04": parsed["04_learning_notes"],
            "07": parsed["07_final_study_guide"],
        }

    if not reuse_all:
        _atomic_write_bundle(
            paths,
            {
                COVER_FILENAME: generated["00"],
                SUMMARY_FILENAME: bodies["03"],
                NOTES_FILENAME: bodies["04"],
                GUIDE_FILENAME: bodies["07"],
            },
        )

    report_paths = storage.study_guide_run_asset_paths(podcast_id, episode_ref)
    result = _result(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=True,
        source_summary_path=str(source_path),
        bundle_dir=str(paths.bundle_dir),
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        planned_reuses=planned_reuses,
        output_paths={label: str(path) for label, path in file_map.items()},
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        reused=reuse_all,
        warnings=[CACHE_STALE_WARNING],
    )
    _write_run_report(result)
    return result


def result_to_dict(result: StudyGuideBundleResult) -> dict[str, Any]:
    """Serialize a bundle result to metadata-only JSON."""

    payload = asdict(result)
    payload["report_json_path"] = _path_or_none(result.report_json_path)
    payload["report_markdown_path"] = _path_or_none(result.report_markdown_path)
    payload["dry_run"] = not result.confirm
    return payload


def _result(**kwargs: Any) -> StudyGuideBundleResult:
    confirm = bool(kwargs["confirm"])
    return StudyGuideBundleResult(
        run_mode="confirmed" if confirm else "dry-run",
        not_investment_advice=True,
        **kwargs,
    )


def _file_map(paths: storage.StudyGuideBundlePaths) -> dict[str, Path]:
    return {
        "00": paths.cover_path,
        "03": paths.summary_path,
        "04": paths.notes_path,
        "07": paths.guide_path,
    }


def _episode_title(podcast_id: str, episode_ref: str, source_path: Path) -> str:
    stem = source_path.name.removesuffix(".semantic.md")
    if "__" in stem:
        return stem.split("__", 1)[1].replace("_", " ")
    seed_path = storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)
    if seed_path.is_file():
        try:
            payload = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
    return episode_ref


def _find_audio(podcast_id: str, episode_ref: str) -> Path | None:
    audio_dir = storage.AUDIO_DIR / podcast_id
    if not audio_dir.is_dir():
        return None
    suffix = {".mp3", ".m4a", ".wav", ".aac", ".flac"}
    matches = sorted(
        path
        for path in audio_dir.glob(f"{episode_ref}__*")
        if path.suffix.lower() in suffix
    )
    return matches[0] if matches else None


def _read_capped_utf8(path: Path) -> str:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise StudyGuideBundleError(f"semantic summary is unreadable: {path}") from exc
    if len(payload) > _MAX_SOURCE_BYTES:
        raise StudyGuideBundleError("semantic summary exceeded the read size cap")
    try:
        return payload.decode("utf-8")
    except UnicodeError as exc:
        raise StudyGuideBundleError("semantic summary is not readable UTF-8") from exc


def _is_readable(path: Path) -> bool:
    try:
        _read_capped_utf8(path)
    except StudyGuideBundleError:
        return False
    return True


def _is_finance_shaped(text: str) -> bool:
    headings = _heading_titles(text)
    return any(name in headings for name in FINANCE_HEADINGS)


def _heading_titles(text: str) -> set[str]:
    titles: set[str] = set()
    for match in _HEADING.finditer(text):
        titles.add(match.group(1).strip())
    return titles


def _source_window(source_text: str) -> str:
    if _CHUNK_SPLIT.search(source_text) is None:
        raise StudyGuideBundleError(
            "source semantic summary is missing the Chunk Summaries heading"
        )
    return _CHUNK_SPLIT.split(source_text, maxsplit=1)[0]


def _build_messages(source_text: str) -> list[dict[str, str]]:
    window = _source_window(source_text)
    return [
        {"role": "system", "content": STUDY_GUIDE_PROFILE.system_message},
        {
            "role": "user",
            "content": STUDY_GUIDE_PROFILE.user_instructions + "\n\n" + window,
        },
    ]


def _parse_bundle_payload(raw: str) -> dict[str, str]:
    text = raw.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StudyGuideBundleError("study-guide model output is not JSON") from exc
    if not isinstance(payload, dict):
        raise StudyGuideBundleError("study-guide model output is not an object")
    missing = [key for key in BUNDLE_KEYS if key not in payload]
    if missing:
        raise StudyGuideBundleError(
            f"study-guide model output missing keys: {', '.join(missing)}"
        )
    parsed: dict[str, str] = {}
    for key in BUNDLE_KEYS:
        value = payload[key]
        if not isinstance(value, str) or not value.strip():
            raise StudyGuideBundleError(f"study-guide model output {key} is empty")
        parsed[key] = value
    return parsed


def _validate_generated(parsed: dict[str, str], source_text: str) -> None:
    required = {
        "03_full_summary": STUDY_GUIDE_PROFILE.summary_headings,
        "04_learning_notes": STUDY_GUIDE_PROFILE.notes_headings,
        "07_final_study_guide": STUDY_GUIDE_PROFILE.guide_headings,
    }
    source_window = _source_window(source_text)
    for key, headings in required.items():
        body = parsed[key]
        titles = _heading_titles(body)
        missing = [
            heading
            for heading in headings
            if not _has_heading(titles, heading) and heading not in body
        ]
        if missing:
            raise StudyGuideBundleError(
                f"{key} missing required headings: {', '.join(missing)}"
            )
        if any(_has_heading(titles, heading) for heading in FINANCE_HEADINGS):
            raise StudyGuideBundleError(f"{key} contains finance headings")
        for marker in WORKFLOW_MARKERS:
            if marker in body and marker not in source_window:
                raise StudyGuideBundleError(
                    f"{key} invents workflow marker {marker!r}"
                )
        if matched_investment_advice_guard(body) is not None:
            raise StudyGuideBundleError(f"{key} failed prohibited_advice")
        source_clocks = set(_CLOCK.findall(source_window))
        for stamp in _TIMESTAMP.findall(body) + [
            f"[{clock}]" for clock in _CLOCK.findall(body)
        ]:
            clocks = _CLOCK.findall(stamp)
            if clocks and any(clock not in source_clocks for clock in clocks):
                raise StudyGuideBundleError(
                    f"{key} uses timestamp {stamp} that is not in the source summary"
                )


def _has_heading(titles: set[str], expected: str) -> bool:
    for title in titles:
        if title == expected or title.endswith(expected) or expected in title:
            return True
    return False


def _render_cover(
    *,
    podcast_id: str,
    episode_ref: str,
    title: str,
    seed_path: Path,
    audio_path: Path | None,
) -> str:
    seed: dict[str, Any] = {}
    if seed_path.is_file():
        try:
            loaded = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}
        if isinstance(loaded, dict):
            seed = loaded
    lines = [
        "# Video Info",
        "",
        f"- Podcast ID: `{podcast_id}`",
        f"- Episode: `{episode_ref}`",
        f"- Title: `{title}`",
    ]
    for key, label in (
        ("seed_source", "Source"),
        ("selector", "Selector"),
        ("published_at", "Published"),
        ("duration", "Duration"),
    ):
        value = seed.get(key)
        if isinstance(value, str) and value.strip():
            lines.append(f"- {label}: `{value}`")
    if audio_path is not None and audio_path.is_file():
        size = audio_path.stat().st_size
        lines.append(f"- Audio: `{audio_path.name}` (`{size}` bytes)")
    lines.append("")
    return "\n".join(lines)


def _atomic_write_bundle(paths: storage.StudyGuideBundlePaths, files: dict[str, str]) -> None:
    dest = paths.bundle_dir
    part = dest.with_name(dest.name + ".part")
    old = dest.with_name(dest.name + ".old")
    try:
        if not dest.exists() and old.exists():
            old.rename(dest)
        if part.exists():
            shutil.rmtree(part)
        part.mkdir(parents=True)
        for name, content in files.items():
            (part / name).write_text(content, encoding="utf-8")
        replaced = dest.exists()
        if replaced:
            if old.exists():
                shutil.rmtree(old)
            dest.rename(old)
        try:
            part.rename(dest)
        except OSError:
            if replaced and old.exists() and not dest.exists():
                old.rename(dest)
            raise
        if old.exists():
            shutil.rmtree(old)
    except OSError as exc:
        if part.exists():
            shutil.rmtree(part, ignore_errors=True)
        raise StudyGuideBundleError("failed to write study-guide bundle") from exc


def _write_run_report(result: StudyGuideBundleResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    markdown = "\n".join(
        [
            f"# Study-guide run — {result.podcast_id} / {result.episode_ref}",
            "",
            f"- run_mode: {result.run_mode}",
            f"- reused: {result.reused}",
            f"- source: {result.source_summary_path}",
            "",
        ]
    )
    try:
        write_part_staged_report_pair(
            result.report_json_path,
            result.report_markdown_path,
            payload,
            markdown,
        )
    except OSError as exc:
        raise StudyGuideBundleError("failed to write study-guide run report") from exc


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None
