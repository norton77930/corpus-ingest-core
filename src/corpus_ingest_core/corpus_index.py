from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from . import storage
from .errors import CorpusIndexFailedError
from .models import (
    CorpusArtifactFamilyCounts,
    CorpusEpisodeRow,
    CorpusIndexResult,
)
from .semantic_review_artifact import (
    inspect_semantic_review,
    parse_semantic_review_filename,
    semantic_review_candidates,
)
from .semantic_summary_identity import canonical_semantic_summary_path
from .storage import EVALS_RESEARCH_SMOKE_REPORTS_DIR as SEMANTIC_REVIEW_REPORTS_DIR

INDEX_MODE = "deterministic-corpus-artifact-index-v1"
SOURCE_SCOPE = "local-per-episode-artifacts-only"
SUPPORTED_ARTIFACT_FAMILIES = (
    "audio",
    "transcript",
    "extractive_summary",
    "semantic_summary",
    "semantic_review",
    "mentions",
    "episode_intelligence",
    "industry_mapping",
    "external_boundary",
    "study_guide",
    "workflow_derivation",
)

_AUDIO_SUFFIXES = {".mp3", ".m4a", ".wav", ".aac", ".flac"}
_ARRAY_COUNTS_KEY = "__array_counts__"
_SEMANTIC_SUMMARY_MAX_READ_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class _CorpusIndexSnapshot:
    result: CorpusIndexResult
    payload: dict[str, Any]
    markdown: str


def generate_corpus_index(podcast_id: str) -> CorpusIndexResult:
    """Generate deterministic local artifact status index for one podcast."""

    return _persist_corpus_index_snapshot(_build_corpus_index_snapshot(podcast_id))


def discover_local_episode_refs(podcast_id: str) -> list[str]:
    """Return sorted local episode refs for one podcast without writing an index."""

    return _discover_episode_refs(podcast_id)


def _build_corpus_index_snapshot(podcast_id: str) -> _CorpusIndexSnapshot:
    paths = storage.corpus_index_asset_paths(podcast_id)
    episode_refs = discover_local_episode_refs(podcast_id)
    rows = [_build_episode_row(podcast_id, episode_ref) for episode_ref in episode_refs]
    family_counts = _artifact_family_counts(rows)
    warning_count = sum(len(row.warnings) for row in rows)
    payload = {
        "podcast_id": podcast_id,
        "index_mode": INDEX_MODE,
        "source_scope": SOURCE_SCOPE,
        "episode_count": len(rows),
        "artifact_family_counts": {family: asdict(counts) for family, counts in family_counts.items()},
        "warning_count": warning_count,
        "episodes": [asdict(row) for row in rows],
        "not_investment_advice": True,
    }
    result = CorpusIndexResult(
        podcast_id=podcast_id,
        index_json_path=paths.json_path,
        index_markdown_path=paths.markdown_path,
        episode_count=len(rows),
        warning_count=warning_count,
        artifact_family_counts=family_counts,
    )
    return _CorpusIndexSnapshot(
        result=result,
        payload=payload,
        markdown=_render_markdown(payload),
    )


def _persist_corpus_index_snapshot(snapshot: _CorpusIndexSnapshot) -> CorpusIndexResult:
    _write_index(
        snapshot.result.index_json_path,
        snapshot.result.index_markdown_path,
        snapshot.payload,
        snapshot.markdown,
    )
    return snapshot.result


def _discover_episode_refs(podcast_id: str) -> list[str]:
    refs: set[str] = set()
    for directory, predicate in (
        (storage.AUDIO_DIR / podcast_id, _is_audio_path),
        (storage.TRANSCRIPTS_DIR / podcast_id, lambda path: path.suffix == ".json"),
        (storage.SUMMARIES_DIR / podcast_id, lambda path: path.suffix == ".md"),
        (storage.MENTIONS_DIR / podcast_id, lambda path: path.name.endswith(".mentions.json")),
        (storage.REPORTS_DIR / podcast_id, lambda path: path.name.endswith(".intelligence.json")),
        (storage.MAPPINGS_DIR / podcast_id, lambda path: path.name.endswith(".industry-map.json")),
        (storage.EXTERNAL_DIR / podcast_id, lambda path: path.name.endswith(".external-boundary.json")),
        (
            storage.CORPUS_DIR / podcast_id / "episode-seeds",
            lambda path: path.name.endswith(".episode-seed.json"),
        ),
    ):
        refs.update(_episode_refs_from_directory(directory, predicate))
    refs.update(_episode_refs_from_semantic_reviews(podcast_id))
    return sorted(refs)


def _episode_refs_from_directory(directory: Path, predicate: Callable[[Path], bool]) -> set[str]:
    if not directory.exists():
        return set()
    refs: set[str] = set()
    for path in sorted(directory.iterdir()):
        if path.is_file() and predicate(path):
            refs.add(_episode_ref_from_artifact_name(path))
    return refs


def _episode_refs_from_semantic_reviews(podcast_id: str) -> set[str]:
    if not SEMANTIC_REVIEW_REPORTS_DIR.exists():
        return set()
    refs: set[str] = set()
    for path in sorted(SEMANTIC_REVIEW_REPORTS_DIR.glob("*.semantic-review*.json")):
        parsed = parse_semantic_review_filename(path, podcast_id)
        if parsed is not None:
            refs.add(parsed.episode_ref)
    return refs


def _episode_ref_from_artifact_name(path: Path) -> str:
    if path.name.endswith(".episode-seed.json"):
        return path.name.removesuffix(".episode-seed.json")
    if "__" in path.name:
        return path.name.split("__", 1)[0]
    return path.stem.split(".", 1)[0]


def _is_audio_path(path: Path) -> bool:
    return path.suffix.lower() in _AUDIO_SUFFIXES


def _build_episode_row(podcast_id: str, episode_ref: str) -> CorpusEpisodeRow:
    source_metadata = _source_metadata(podcast_id, episode_ref)
    transcript = _transcript_status(podcast_id, episode_ref)
    canonical_summary_path = canonical_semantic_summary_path(podcast_id, episode_ref)
    semantic_summary = _summary_status(
        podcast_id,
        episode_ref,
        semantic=True,
        canonical_path=canonical_summary_path,
    )
    semantic_summary_path = semantic_summary.get("path")
    artifact_status = {
        "audio": _audio_status(podcast_id, episode_ref),
        "transcript": transcript,
        "extractive_summary": _summary_status(podcast_id, episode_ref, semantic=False),
        "semantic_summary": semantic_summary,
        "semantic_review": _semantic_review_status(
            podcast_id,
            episode_ref,
            semantic_summary_path=(Path(semantic_summary_path) if isinstance(semantic_summary_path, str) else None),
        ),
        "mentions": _mentions_status(podcast_id, episode_ref),
        "episode_intelligence": _episode_intelligence_status(podcast_id, episode_ref),
        "industry_mapping": _industry_mapping_status(podcast_id, episode_ref),
        "external_boundary": _external_boundary_status(podcast_id, episode_ref),
        "study_guide": _study_guide_status(podcast_id, episode_ref),
        "workflow_derivation": _workflow_derivation_status(podcast_id, episode_ref),
    }
    missing_artifacts = [
        family for family in SUPPORTED_ARTIFACT_FAMILIES if artifact_status[family]["status"] == "missing"
    ]
    warnings: list[str] = []
    for family in SUPPORTED_ARTIFACT_FAMILIES:
        warnings.extend(f"{family}: {warning}" for warning in artifact_status[family].get("warnings", []))
    return CorpusEpisodeRow(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=_episode_title(episode_ref, artifact_status, source_metadata),
        artifact_status=artifact_status,
        missing_artifacts=missing_artifacts,
        warnings=warnings,
        source_metadata=source_metadata,
    )


def _audio_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    candidates = _standard_candidates(storage.AUDIO_DIR / podcast_id, episode_ref, _is_audio_path)
    if not candidates:
        return _missing_status()
    selected = candidates[0]
    warnings = _duplicate_warnings("audio", candidates, selected)
    return {
        "status": "available",
        "exists": True,
        "path": str(selected),
        "paths": {"audio": str(selected)},
        "candidate_count": len(candidates),
        "warnings": warnings,
        "warning_count": len(warnings),
    }


def _source_metadata(podcast_id: str, episode_ref: str) -> dict[str, dict[str, Any]]:
    seed_path = storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)
    if not seed_path.exists():
        return {}
    payload, unreadable_warning = _load_json_metadata(
        seed_path,
        fields=(
            "title",
            "published_at",
            "duration",
            "guid_status",
            "has_audio_url",
            "seed_source",
            "selector",
            "warning_count",
        ),
    )
    if unreadable_warning is not None:
        return {
            "episode_seed": {
                "status": "unreadable",
                "path": str(seed_path),
                "warnings": [unreadable_warning],
                "warning_count": 1,
            }
        }
    assert payload is not None
    return {
        "episode_seed": {
            "status": "available",
            "path": str(seed_path),
            "title": _safe_text(payload.get("title"), episode_ref),
            "published_at": _optional_text(payload.get("published_at")),
            "duration": _optional_text(payload.get("duration")),
            "guid_status": _safe_text(payload.get("guid_status"), "unknown"),
            "has_audio_url": bool(payload.get("has_audio_url")),
            "seed_source": _safe_text(payload.get("seed_source"), "unknown"),
            "selector": _safe_text(payload.get("selector"), "unknown"),
            "warning_count": _safe_int(payload.get("warning_count")),
            "warnings": [],
        }
    }


def _transcript_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    candidates = _standard_json_candidates(storage.TRANSCRIPTS_DIR / podcast_id, episode_ref)
    if not candidates:
        return {
            **_missing_status(),
            "validation_status": "missing",
            "segment_count": 0,
            "last_segment_end_seconds": None,
            "problem_count": 0,
            "warning_count": 0,
        }

    selected = candidates[0]
    warnings = _duplicate_warnings("transcript", candidates, selected)
    paths = {
        "json": str(selected),
        "text": str(selected.with_suffix(".txt")),
        "srt": str(selected.with_suffix(".srt")),
    }
    payload, unreadable_warning = _load_json_metadata(
        selected,
        fields=("title", "segment_count", "last_segment_end_seconds", "completed"),
        array_count_fields=("segments",),
    )
    if unreadable_warning is not None:
        warnings.append(unreadable_warning)
        return {
            "status": "unreadable",
            "validation_status": "unreadable",
            "segment_count": 0,
            "last_segment_end_seconds": None,
            "problem_count": 1,
            "warning_count": len(warnings),
            "paths": paths,
            "candidate_count": len(candidates),
            "warnings": warnings,
        }

    assert payload is not None
    problems = _transcript_output_problems(selected)
    segment_array_count = _array_count(payload, "segments")
    segment_count = _safe_int(
        payload.get("segment_count"),
        default=segment_array_count if segment_array_count is not None else 0,
    )
    last_segment_end = _safe_float(payload.get("last_segment_end_seconds"))
    if segment_array_count is not None and segment_count != segment_array_count:
        problems.append("segment_count does not match segments length")
    if payload.get("completed") is False:
        problems.append("transcript JSON marks completed=false")

    if problems:
        validation_status = "partial"
        if any("missing" in problem for problem in problems):
            validation_status = "incomplete_outputs"
    elif segment_count == 0:
        validation_status = "empty"
    else:
        validation_status = "valid"
    return {
        "status": validation_status,
        "validation_status": validation_status,
        "segment_count": segment_count,
        "last_segment_end_seconds": last_segment_end,
        "problem_count": len(problems),
        "warning_count": len(warnings),
        "paths": paths,
        "candidate_count": len(candidates),
        "warnings": warnings,
    }


def _summary_status(
    podcast_id: str,
    episode_ref: str,
    *,
    semantic: bool,
    canonical_path: Path | None = None,
) -> dict[str, Any]:
    summary_dir = storage.SUMMARIES_DIR / podcast_id
    if semantic:
        candidates = sorted(summary_dir.glob(f"{episode_ref}__*.semantic.md"))
    else:
        candidates = [
            path for path in sorted(summary_dir.glob(f"{episode_ref}__*.md")) if not path.name.endswith(".semantic.md")
        ]
    if not candidates:
        missing = {**_missing_status(), "exists": False, "path": None}
        if semantic:
            missing.update(readable=False, readability_status="missing")
        return missing
    if semantic:
        # A stale title variant is not a substitute for the transcript-bound
        # semantic summary.  The caller must generate/review the canonical path.
        if canonical_path is None or canonical_path not in candidates:
            return {
                **_missing_status(),
                "exists": False,
                "path": None,
                "readable": False,
                "readability_status": "missing",
                "candidate_count": len(candidates),
                "warnings": [
                    "noncanonical semantic summary candidates ignored; transcript-title-bound summary is missing"
                ],
                "warning_count": 1,
            }
        selected = canonical_path
    else:
        selected = candidates[0]
    family = "semantic_summary" if semantic else "extractive_summary"
    warnings = _duplicate_warnings(family, candidates, selected)
    readability: dict[str, Any] = {}
    if semantic:
        readable, readability_warning = _semantic_summary_readability(selected)
        readability = {
            "readable": readable,
            "readability_status": "readable" if readable else "unreadable",
        }
        if readability_warning is not None:
            warnings.append(readability_warning)
    return {
        "status": "available",
        "exists": True,
        "path": str(selected),
        "paths": {"markdown": str(selected)},
        "candidate_count": len(candidates),
        "warnings": warnings,
        "warning_count": len(warnings),
        **readability,
    }


def _semantic_summary_readability(path: Path) -> tuple[bool, str | None]:
    try:
        with path.open("rb") as handle:
            payload = handle.read(_SEMANTIC_SUMMARY_MAX_READ_BYTES + 1)
        if len(payload) > _SEMANTIC_SUMMARY_MAX_READ_BYTES:
            return False, "semantic summary readability check exceeded size limit"
        payload.decode("utf-8")
    except (OSError, UnicodeError):
        return False, "semantic summary is not readable UTF-8"
    return True, None


def _workflow_derivation_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    canonical = canonical_semantic_summary_path(podcast_id, episode_ref)
    if canonical is None:
        return {**_missing_status(), "exists": False, "path": None}
    stem = canonical.name.removesuffix(".semantic.md")
    paths = storage.workflow_derivation_paths_from_stem(podcast_id, stem)
    files = (paths.prompt_examples_path, paths.apply_path)
    existing = [path for path in files if path.is_file()]
    if not existing:
        return {**_missing_status(), "exists": False, "path": None}
    warnings: list[str] = []
    readable = True
    for path in existing:
        ok, warning = _semantic_summary_readability(path)
        if not ok:
            readable = False
            if warning:
                warnings.append(warning)
    if len(existing) < 2:
        return {
            "status": "partial",
            "exists": True,
            "path": str(paths.bundle_dir),
            "paths": {"bundle": str(paths.bundle_dir)},
            "candidate_count": len(existing),
            "warnings": warnings,
            "warning_count": len(warnings),
            "readable": readable,
        }
    if not readable:
        return {
            "status": "unreadable",
            "exists": True,
            "path": str(paths.bundle_dir),
            "paths": {"bundle": str(paths.bundle_dir)},
            "candidate_count": 2,
            "warnings": warnings,
            "warning_count": len(warnings),
            "readable": False,
        }
    return {
        "status": "available",
        "exists": True,
        "path": str(paths.bundle_dir),
        "paths": {
            "bundle": str(paths.bundle_dir),
            "05": str(paths.prompt_examples_path),
            "06": str(paths.apply_path),
        },
        "candidate_count": 2,
        "warnings": warnings,
        "warning_count": len(warnings),
        "readable": True,
    }


def _study_guide_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    canonical = canonical_semantic_summary_path(podcast_id, episode_ref)
    if canonical is None:
        return {**_missing_status(), "exists": False, "path": None}
    stem = canonical.name.removesuffix(".semantic.md")
    paths = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    bundle_dir = paths.bundle_dir
    files = (
        paths.cover_path,
        paths.summary_path,
        paths.notes_path,
        paths.guide_path,
    )
    existing = [path for path in files if path.is_file()]
    if not existing:
        return {**_missing_status(), "exists": False, "path": None}
    warnings: list[str] = []
    readable = True
    for path in existing:
        ok, warning = _semantic_summary_readability(path)
        if not ok:
            readable = False
            if warning:
                warnings.append(warning)
    if len(existing) < 4:
        return {
            "status": "partial",
            "exists": True,
            "path": str(bundle_dir),
            "paths": {"bundle": str(bundle_dir)},
            "candidate_count": len(existing),
            "warnings": warnings,
            "warning_count": len(warnings),
            "readable": readable,
        }
    if not readable:
        return {
            "status": "unreadable",
            "exists": True,
            "path": str(bundle_dir),
            "paths": {"bundle": str(bundle_dir)},
            "candidate_count": 4,
            "warnings": warnings,
            "warning_count": len(warnings),
            "readable": False,
        }
    return {
        "status": "available",
        "exists": True,
        "path": str(bundle_dir),
        "paths": {"bundle": str(bundle_dir)},
        "candidate_count": 4,
        "warnings": warnings,
        "warning_count": len(warnings),
        "readable": True,
    }


def _mentions_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    return _json_artifact_status(
        family="mentions",
        candidates=_standard_suffix_candidates(storage.MENTIONS_DIR / podcast_id, episode_ref, ".mentions.json"),
        markdown_suffix=".mentions.md",
        metadata_fields=("title", "mention_count"),
        array_count_fields=("mentions",),
        fields=lambda payload: {
            "mention_count": _safe_int(
                payload.get("mention_count"),
                default=_array_count(payload, "mentions", 0),
            )
        },
    )


def _episode_intelligence_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    return _json_artifact_status(
        family="episode_intelligence",
        candidates=_standard_suffix_candidates(storage.REPORTS_DIR / podcast_id, episode_ref, ".intelligence.json"),
        markdown_suffix=".intelligence.md",
        status_key="report_status",
        metadata_fields=("title", "report_status", "transcript_validation", "segment_count"),
        fields=lambda payload: {
            "report_status": _safe_text(payload.get("report_status"), "available"),
            "transcript_status": _nested_text(payload, ("transcript_validation", "status"), "unknown"),
            "segment_count": _safe_int(
                payload.get("segment_count"),
                default=_nested_int(payload, ("transcript_validation", "segment_count"), 0),
            ),
        },
    )


def _industry_mapping_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    return _json_artifact_status(
        family="industry_mapping",
        candidates=_standard_suffix_candidates(storage.MAPPINGS_DIR / podcast_id, episode_ref, ".industry-map.json"),
        markdown_suffix=".industry-map.md",
        status_key="mapping_status",
        metadata_fields=(
            "title",
            "mapping_status",
            "node_count",
            "candidate_count",
            "warning_count",
        ),
        array_count_fields=("industry_chain_nodes", "stock_candidates", "warnings"),
        fields=lambda payload: {
            "mapping_status": _safe_text(payload.get("mapping_status"), "available"),
            "node_count": _safe_int(
                payload.get("node_count"),
                default=_array_count(payload, "industry_chain_nodes", 0),
            ),
            "candidate_count": _safe_int(
                payload.get("candidate_count"),
                default=_array_count(payload, "stock_candidates", 0),
            ),
            "warning_count": _safe_int(
                payload.get("warning_count"),
                default=_array_count(payload, "warnings", 0),
            ),
        },
    )


def _external_boundary_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    return _json_artifact_status(
        family="external_boundary",
        candidates=_standard_suffix_candidates(
            storage.EXTERNAL_DIR / podcast_id, episode_ref, ".external-boundary.json"
        ),
        markdown_suffix=".external-boundary.md",
        status_key="boundary_status",
        metadata_fields=("title", "boundary_status", "candidate_count", "warning_count"),
        array_count_fields=("candidate_boundaries", "warnings"),
        fields=lambda payload: {
            "boundary_status": _safe_text(payload.get("boundary_status"), "available"),
            "candidate_count": _safe_int(
                payload.get("candidate_count"),
                default=_array_count(payload, "candidate_boundaries", 0),
            ),
            "warning_count": _safe_int(
                payload.get("warning_count"),
                default=_array_count(payload, "warnings", 0),
            ),
        },
    )


def _semantic_review_status(
    podcast_id: str,
    episode_ref: str,
    *,
    semantic_summary_path: Path | None = None,
) -> dict[str, Any]:
    candidates, rejected, ignored_warnings = _semantic_review_candidates(podcast_id, episode_ref)
    if not candidates and not rejected:
        return {
            **_missing_status(),
            "review_status": "missing",
            "review_json_path": None,
            "review_markdown_path": None,
            "check_count": 0,
            "failed_check_count": 0,
            "warning_count": 0,
            "blocked_check_count": 0,
            "warnings": ignored_warnings,
        }

    selected = candidates[-1] if candidates else rejected[-1]
    if semantic_summary_path is None:
        review_status = "needs_review"
        payload: dict[str, Any] | None = None
        inspection_path = selected
    else:
        inspection = inspect_semantic_review(
            podcast_id,
            episode_ref,
            semantic_summary_path=semantic_summary_path,
            review_reports_dir=SEMANTIC_REVIEW_REPORTS_DIR,
        )
        review_status = inspection.review_status
        payload = inspection.review_payload
        inspection_path = inspection.review_path or selected
    metadata, unreadable_warning = _load_json_metadata(
        inspection_path,
        fields=(
            "check_count",
            "failed_check_count",
            "warning_count",
            "blocked_check_count",
        ),
        array_count_fields=("checks",),
    )
    payload = payload if isinstance(payload, dict) else metadata if isinstance(metadata, dict) else {}
    warnings = [*ignored_warnings]
    if unreadable_warning is not None:
        warnings.append(unreadable_warning)
    return {
        "status": review_status,
        "review_status": review_status,
        "review_json_path": str(inspection_path),
        "review_markdown_path": str(inspection_path.with_suffix(".md")),
        "check_count": _safe_int(payload.get("check_count")),
        "failed_check_count": _safe_int(payload.get("failed_check_count")),
        "warning_count": _safe_int(payload.get("warning_count")),
        "blocked_check_count": _safe_int(payload.get("blocked_check_count")),
        "candidate_count": len(candidates),
        "warnings": warnings,
        "paths": {"json": str(inspection_path), "markdown": str(inspection_path.with_suffix(".md"))},
    }


def _json_artifact_status(
    *,
    family: str,
    candidates: list[Path],
    markdown_suffix: str,
    fields: Callable[[dict[str, Any]], dict[str, Any]],
    status_key: str | None = None,
    metadata_fields: tuple[str, ...] = ("title",),
    array_count_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    if not candidates:
        return _missing_status()
    selected = candidates[0]
    warnings = _duplicate_warnings(family, candidates, selected)
    markdown_path = _paired_markdown_path(selected, markdown_suffix)
    paths = {"json": str(selected), "markdown": str(markdown_path)}
    payload, unreadable_warning = _load_json_metadata(
        selected,
        fields=metadata_fields,
        array_count_fields=array_count_fields,
    )
    if unreadable_warning is not None:
        warnings.append(unreadable_warning)
        return {
            "status": "unreadable",
            "paths": paths,
            "candidate_count": len(candidates),
            "warnings": warnings,
            "warning_count": len(warnings),
        }

    assert payload is not None
    extra_fields = fields(payload)
    status = "available"
    if status_key is not None:
        status = _safe_text(payload.get(status_key), "available")
    return {
        "status": status,
        "paths": paths,
        "candidate_count": len(candidates),
        "warnings": warnings,
        "warning_count": len(warnings),
        **extra_fields,
    }


def _missing_status() -> dict[str, Any]:
    return {
        "status": "missing",
        "paths": {},
        "candidate_count": 0,
        "warnings": [],
        "warning_count": 0,
    }


def _standard_candidates(
    directory: Path,
    episode_ref: str,
    predicate: Callable[[Path], bool],
) -> list[Path]:
    if not directory.exists():
        return []
    return [
        path
        for path in sorted(directory.iterdir())
        if path.is_file() and predicate(path) and _episode_ref_from_artifact_name(path) == episode_ref
    ]


def _standard_json_candidates(directory: Path, episode_ref: str) -> list[Path]:
    return _standard_candidates(directory, episode_ref, lambda path: path.suffix == ".json")


def _standard_suffix_candidates(directory: Path, episode_ref: str, suffix: str) -> list[Path]:
    return _standard_candidates(
        directory,
        episode_ref,
        lambda path: path.name.endswith(suffix),
    )


def _semantic_review_candidates(podcast_id: str, episode_ref: str) -> tuple[list[Path], list[Path], list[str]]:
    candidates, rejected = semantic_review_candidates(SEMANTIC_REVIEW_REPORTS_DIR, podcast_id, episode_ref)
    return candidates, rejected, [f"ignored non-timestamped semantic review candidate: {path}" for path in rejected]


def _duplicate_warnings(family: str, candidates: list[Path], selected: Path) -> list[str]:
    if len(candidates) <= 1:
        return []
    return [(f"duplicate {family} candidates found; selected {selected}; candidate_count={len(candidates)}")]


def _paired_markdown_path(json_path: Path, markdown_suffix: str) -> Path:
    if json_path.name.endswith(".json"):
        return json_path.with_name(json_path.name.removesuffix(".json") + ".md")
    return json_path.with_suffix(markdown_suffix)


def _load_json_metadata(
    path: Path,
    *,
    fields: tuple[str, ...] = (),
    array_count_fields: tuple[str, ...] = (),
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = _JsonMetadataScanner(
            path,
            metadata_fields=set(fields),
            array_count_fields=set(array_count_fields),
        ).scan()
    except (OSError, ValueError) as exc:
        return None, f"unreadable JSON metadata: {path}: {exc}"
    return payload, None


def _transcript_output_problems(json_path: Path) -> list[str]:
    problems = []
    for label, path in (
        ("TXT", json_path.with_suffix(".txt")),
        ("SRT", json_path.with_suffix(".srt")),
    ):
        if not path.exists():
            problems.append(f"missing transcript {label} output")
    return problems


def _episode_title(
    episode_ref: str,
    artifact_status: dict[str, dict[str, Any]],
    source_metadata: dict[str, dict[str, Any]],
) -> str:
    for family in (
        "transcript",
        "mentions",
        "episode_intelligence",
        "industry_mapping",
        "external_boundary",
    ):
        json_path = artifact_status[family].get("paths", {}).get("json")
        if not json_path:
            continue
        payload, _ = _load_json_metadata(Path(json_path), fields=("title",))
        if payload is None:
            continue
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            return title
    seed_title = source_metadata.get("episode_seed", {}).get("title")
    if isinstance(seed_title, str) and seed_title.strip():
        return seed_title
    return episode_ref


def _artifact_family_counts(
    rows: list[CorpusEpisodeRow],
) -> dict[str, CorpusArtifactFamilyCounts]:
    counts = {family: {"available": 0, "missing": 0, "unreadable": 0} for family in SUPPORTED_ARTIFACT_FAMILIES}
    for row in rows:
        for family in SUPPORTED_ARTIFACT_FAMILIES:
            status = row.artifact_status[family]["status"]
            if status == "missing":
                bucket = "missing"
            elif status in {"unreadable", "partial"}:
                bucket = "unreadable"
            else:
                bucket = "available"
            counts[family][bucket] += 1
    return {family: CorpusArtifactFamilyCounts(**family_counts) for family, family_counts in counts.items()}


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Artifact Index - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Index mode: {payload['index_mode']}",
        f"- Source scope: {payload['source_scope']}",
        f"- Episode count: {payload['episode_count']}",
        f"- Warning count: {payload['warning_count']}",
        "",
        "## Artifact Family Counts",
        "",
        "| Family | Available | Missing | Unreadable |",
        "| --- | ---: | ---: | ---: |",
    ]
    for family in SUPPORTED_ARTIFACT_FAMILIES:
        counts = payload["artifact_family_counts"][family]
        lines.append(f"| {family} | {counts['available']} | {counts['missing']} | {counts['unreadable']} |")

    lines.extend(
        [
            "",
            "## Episode Status",
            "",
            "| Episode | Title | Transcript | Semantic Summary | Semantic Review | Mentions | Report | Mapping | External | Missing Artifacts | Warnings |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in payload["episodes"]:
        missing = ", ".join(row["missing_artifacts"]) if row["missing_artifacts"] else "none"
        status = row["artifact_status"]
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["episode_ref"]),
                    _markdown_cell(row["title"]),
                    _markdown_cell(status["transcript"].get("validation_status", status["transcript"]["status"])),
                    _markdown_cell(status["semantic_summary"]["status"]),
                    _markdown_cell(status["semantic_review"].get("review_status", status["semantic_review"]["status"])),
                    _markdown_cell(status["mentions"].get("mention_count", 0)),
                    _markdown_cell(
                        status["episode_intelligence"].get("report_status", status["episode_intelligence"]["status"])
                    ),
                    _markdown_cell(
                        status["industry_mapping"].get("mapping_status", status["industry_mapping"]["status"])
                    ),
                    _markdown_cell(
                        status["external_boundary"].get("boundary_status", status["external_boundary"]["status"])
                    ),
                    _markdown_cell(missing),
                    _markdown_cell(len(row["warnings"])),
                ]
            )
            + " |"
        )

    if payload["warning_count"]:
        lines.extend(["", "## Warnings", ""])
        for row in payload["episodes"]:
            for warning in row["warnings"]:
                lines.append(f"- {row['episode_ref']}: {warning}")

    lines.extend(
        [
            "",
            "## Boundary Notice",
            "",
            "This artifact is local corpus status metadata only.",
            "It does not call RSS, network services, SQLite cache, LLM providers, or market data APIs.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_index(
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
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
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
        raise CorpusIndexFailedError(f"Failed to write the corpus artifact index: {exc}") from exc


def _safe_int(value: Any, default: int = 0) -> int:
    return value if isinstance(value, int) else default


def _safe_float(value: Any) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _safe_text(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value.strip() else default


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _array_count(payload: dict[str, Any], key: str, default: int | None = None) -> int | None:
    counts = payload.get(_ARRAY_COUNTS_KEY)
    if not isinstance(counts, dict):
        return default
    value = counts.get(key)
    return value if isinstance(value, int) else default


def _nested_int(payload: dict[str, Any], path: tuple[str, str], default: int) -> int:
    parent = payload.get(path[0])
    if not isinstance(parent, dict):
        return default
    return _safe_int(parent.get(path[1]), default)


def _nested_text(payload: dict[str, Any], path: tuple[str, str], default: str) -> str:
    parent = payload.get(path[0])
    if not isinstance(parent, dict):
        return default
    return _safe_text(parent.get(path[1]), default)


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")


class _JsonMetadataScanner:
    """Stream top-level JSON metadata without materializing body arrays."""

    def __init__(
        self,
        path: Path,
        *,
        metadata_fields: set[str],
        array_count_fields: set[str],
    ) -> None:
        self._path = path
        self._metadata_fields = metadata_fields
        self._array_count_fields = array_count_fields
        self._handle = None
        self._pushback: list[str] = []

    def scan(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        array_counts: dict[str, int] = {}
        with self._path.open("r", encoding="utf-8") as handle:
            self._handle = handle
            if self._read_non_ws() != "{":
                raise ValueError("root is not an object")
            next_char = self._read_non_ws()
            if next_char == "}":
                self._assert_trailing_whitespace()
                metadata[_ARRAY_COUNTS_KEY] = array_counts
                return metadata
            self._unread(next_char)
            while True:
                if self._read_non_ws() != '"':
                    raise ValueError("object key must be a string")
                key = json.loads(self._read_string_raw('"', capture=True))
                if self._read_non_ws() != ":":
                    raise ValueError("object key must be followed by ':'")
                if key in self._array_count_fields:
                    array_counts[key] = self._read_array_count()
                elif key in self._metadata_fields:
                    metadata[key] = self._read_captured_value()
                else:
                    self._skip_value()
                separator = self._read_non_ws()
                if separator == ",":
                    continue
                if separator == "}":
                    break
                raise ValueError("object entries must be separated by ',' or '}'")
            self._assert_trailing_whitespace()
        metadata[_ARRAY_COUNTS_KEY] = array_counts
        return metadata

    def _read_captured_value(self) -> Any:
        first = self._read_non_ws()
        if first == '"':
            return json.loads(self._read_string_raw(first, capture=True))
        if first in "[{":
            return json.loads(self._read_compound_raw(first))
        return json.loads(self._read_primitive_raw(first))

    def _read_array_count(self) -> int:
        first = self._read_non_ws()
        if first != "[":
            self._skip_value(first)
            return 0
        count = 0
        next_char = self._read_non_ws()
        if next_char == "]":
            return count
        self._unread(next_char)
        while True:
            self._skip_value()
            count += 1
            separator = self._read_non_ws()
            if separator == ",":
                continue
            if separator == "]":
                return count
            raise ValueError("array entries must be separated by ',' or ']'")

    def _skip_value(self, first: str | None = None) -> None:
        first = first or self._read_non_ws()
        if first == '"':
            self._read_string_raw(first, capture=False)
            return
        if first == "[":
            next_char = self._read_non_ws()
            if next_char == "]":
                return
            self._unread(next_char)
            while True:
                self._skip_value()
                separator = self._read_non_ws()
                if separator == ",":
                    continue
                if separator == "]":
                    return
                raise ValueError("array entries must be separated by ',' or ']'")
        if first == "{":
            next_char = self._read_non_ws()
            if next_char == "}":
                return
            self._unread(next_char)
            while True:
                if self._read_non_ws() != '"':
                    raise ValueError("object key must be a string")
                self._read_string_raw('"', capture=False)
                if self._read_non_ws() != ":":
                    raise ValueError("object key must be followed by ':'")
                self._skip_value()
                separator = self._read_non_ws()
                if separator == ",":
                    continue
                if separator == "}":
                    return
                raise ValueError("object entries must be separated by ',' or '}'")
        json.loads(self._read_primitive_raw(first))

    def _read_compound_raw(self, first: str) -> str:
        closing = "]" if first == "[" else "}"
        stack = [closing]
        chars = [first]
        while stack:
            char = self._read()
            chars.append(char)
            if char == '"':
                chars.extend(self._read_string_raw(char, capture=True)[1:])
                continue
            if char == "[":
                stack.append("]")
            elif char == "{":
                stack.append("}")
            elif char == stack[-1]:
                stack.pop()
        return "".join(chars)

    def _read_primitive_raw(self, first: str) -> str:
        chars = [first]
        while True:
            char = self._read(allow_eof=True)
            if char == "":
                break
            if char in ",]}":
                self._unread(char)
                break
            chars.append(char)
        return "".join(chars).strip()

    def _read_string_raw(self, first: str, *, capture: bool) -> str:
        chars = [first] if capture else []
        escaped = False
        while True:
            char = self._read()
            if capture:
                chars.append(char)
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                return "".join(chars)

    def _read_non_ws(self) -> str:
        while True:
            char = self._read()
            if not char.isspace():
                return char

    def _assert_trailing_whitespace(self) -> None:
        while True:
            char = self._read(allow_eof=True)
            if char == "":
                return
            if not char.isspace():
                raise ValueError("unexpected trailing JSON content")

    def _read(self, *, allow_eof: bool = False) -> str:
        if self._pushback:
            return self._pushback.pop()
        assert self._handle is not None
        char = self._handle.read(1)
        if char == "" and not allow_eof:
            raise ValueError("unexpected end of JSON")
        return char

    def _unread(self, char: str) -> None:
        if char:
            self._pushback.append(char)
