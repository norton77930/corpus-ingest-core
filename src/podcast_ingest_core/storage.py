from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import unicodedata
import re


DATA_DIR = Path(os.environ.get("PODCAST_INGEST_DATA_DIR") or "data")
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
SUMMARIES_DIR = DATA_DIR / "summaries"
MENTIONS_DIR = DATA_DIR / "mentions"
REPORTS_DIR = DATA_DIR / "reports"
MAPPINGS_DIR = DATA_DIR / "mappings"
EXTERNAL_DIR = DATA_DIR / "external"
STOCK_LENS_DIR = DATA_DIR / "stock-lens"
CACHE_DIR = DATA_DIR / "cache"
CORPUS_DIR = DATA_DIR / "corpus"
RESEARCH_REPORTS_DIR = DATA_DIR / "research-reports"
STUDY_GUIDES_DIR = DATA_DIR / "study-guides"
# Repo-root-relative evals path (independent of DATA_DIR); the single defining
# site — smoke-review and index modules re-export it under their local names.
EVALS_RESEARCH_SMOKE_REPORTS_DIR = Path("evals") / "research-llm-smoke" / "reports"
_SAFE_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SAFE_EPISODE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_WINDOWS_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')
_WHITESPACE_PATTERN = re.compile(r"\s+")
_MAX_TITLE_SLUG_LENGTH = 80


@dataclass(frozen=True)
class TranscriptAssetPaths:
    text_path: Path
    srt_path: Path
    json_path: Path


@dataclass(frozen=True)
class MentionAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class EpisodeIntelligenceReportAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class IndustryChainMappingAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class ExternalDataBoundaryAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class StockLensReportAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class StockLensSynthesisAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusIndexAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class StudyGuideBundlePaths:
    bundle_dir: Path
    cover_path: Path
    summary_path: Path
    notes_path: Path
    guide_path: Path


@dataclass(frozen=True)
class StudyGuideRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusRemediationPlanAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusRemediationRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusLocalTranscriptionRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusAudioDownloadRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusEpisodeIntakeRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusEpisodeWorkflowRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusSemanticRemediationRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusEpisodeCompletionWorkflowRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class CorpusLatestEpisodeDeterministicWorkflowRunAssetPaths:
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True)
class LatestEpisodeVerifiedResearchReportPaths:
    """Pure, deterministic paths for one versioned verified report bundle."""

    bundle_dir: Path
    report_json_path: Path
    report_markdown_path: Path
    manifest_path: Path
    checkpoint_path: Path


def audio_path(podcast_id: str, episode_ref: str) -> Path:
    """回傳音檔輸出路徑。"""

    return (
        AUDIO_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_slug(episode_ref, 'episode_ref')}.mp3"
    )


def audio_asset_path(
    podcast_id: str, episode_ref: str, title: str, extension: str
) -> Path:
    """回傳 Phase 1B 音檔輸出路徑。"""

    normalized_extension = _normalize_extension(extension)
    return (
        AUDIO_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}{normalized_extension}"
    )


def transcript_asset_paths(
    podcast_id: str, episode_ref: str, title: str
) -> TranscriptAssetPaths:
    """回傳逐字稿 TXT、SRT、JSON 三種輸出路徑。"""

    base_path = (
        TRANSCRIPTS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}"
    )
    return TranscriptAssetPaths(
        text_path=base_path.with_suffix(".txt"),
        srt_path=base_path.with_suffix(".srt"),
        json_path=base_path.with_suffix(".json"),
    )


def find_transcript_asset_paths(
    podcast_id: str, episode_ref: str
) -> TranscriptAssetPaths | None:
    """依 episode_ref 尋找既有逐字稿輸出路徑。"""

    transcript_dir = TRANSCRIPTS_DIR / _safe_slug(podcast_id, "podcast_id")
    safe_ref = _safe_episode_ref(episode_ref)
    matches = sorted(transcript_dir.glob(f"{safe_ref}__*.json"))
    if not matches:
        return None
    json_path = matches[0]
    return TranscriptAssetPaths(
        text_path=json_path.with_suffix(".txt"),
        srt_path=json_path.with_suffix(".srt"),
        json_path=json_path,
    )


def title_slug(title: str, fallback: str) -> str:
    """將 episode title 轉成適合 Windows 檔名的短 slug。"""

    cleaned = _WINDOWS_ILLEGAL_FILENAME_CHARS.sub("", title)
    cleaned = "".join(character for character in cleaned if _is_safe_filename_character(character))
    cleaned = cleaned.strip()
    cleaned = _WHITESPACE_PATTERN.sub("_", cleaned)
    if not cleaned:
        cleaned = fallback
    return cleaned[:_MAX_TITLE_SLUG_LENGTH]


def transcript_path(podcast_id: str, episode_ref: str) -> Path:
    """回傳逐字稿輸出路徑。"""

    return (
        TRANSCRIPTS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_slug(episode_ref, 'episode_ref')}.json"
    )


def summary_path(podcast_id: str, episode_ref: str) -> Path:
    """回傳摘要輸出路徑。"""

    return (
        SUMMARIES_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_slug(episode_ref, 'episode_ref')}.md"
    )


def summary_asset_path(podcast_id: str, episode_ref: str, title: str) -> Path:
    """回傳 Phase 1D Markdown 摘要輸出路徑。"""

    return (
        SUMMARIES_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}.md"
    )


def semantic_summary_asset_path(podcast_id: str, episode_ref: str, title: str) -> Path:
    """回傳 Phase 2A LLM 語意摘要輸出路徑。"""

    return (
        SUMMARIES_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}.semantic.md"
    )


def mention_asset_paths(podcast_id: str, episode_ref: str, title: str) -> MentionAssetPaths:
    """回傳 deterministic mention extraction 的 JSON 與 Markdown 輸出路徑。"""

    base_path = (
        MENTIONS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}"
    )
    return MentionAssetPaths(
        json_path=base_path.with_suffix(".mentions.json"),
        markdown_path=base_path.with_suffix(".mentions.md"),
    )


def episode_intelligence_report_asset_paths(
    podcast_id: str, episode_ref: str, title: str
) -> EpisodeIntelligenceReportAssetPaths:
    """回傳 episode intelligence report 的 JSON 與 Markdown 輸出路徑。"""

    base_path = (
        REPORTS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}"
    )
    return EpisodeIntelligenceReportAssetPaths(
        json_path=base_path.with_suffix(".intelligence.json"),
        markdown_path=base_path.with_suffix(".intelligence.md"),
    )


def find_episode_intelligence_report_asset_paths(
    podcast_id: str, episode_ref: str
) -> EpisodeIntelligenceReportAssetPaths | None:
    """依 episode_ref 尋找既有 episode intelligence report 輸出路徑。"""

    report_dir = REPORTS_DIR / _safe_slug(podcast_id, "podcast_id")
    safe_ref = _safe_episode_ref(episode_ref)
    matches = sorted(report_dir.glob(f"{safe_ref}__*.intelligence.json"))
    if not matches:
        return None
    json_path = matches[0]
    markdown_path = json_path.with_name(
        json_path.name.removesuffix(".intelligence.json") + ".intelligence.md"
    )
    return EpisodeIntelligenceReportAssetPaths(
        json_path=json_path,
        markdown_path=markdown_path,
    )


def industry_chain_mapping_asset_paths(
    podcast_id: str, episode_ref: str, title: str
) -> IndustryChainMappingAssetPaths:
    """回傳 industry chain mapping 的 JSON 與 Markdown 輸出路徑。"""

    base_path = (
        MAPPINGS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}"
    )
    return IndustryChainMappingAssetPaths(
        json_path=base_path.with_suffix(".industry-map.json"),
        markdown_path=base_path.with_suffix(".industry-map.md"),
    )


def find_industry_chain_mapping_asset_paths(
    podcast_id: str, episode_ref: str
) -> IndustryChainMappingAssetPaths | None:
    """依 episode_ref 尋找既有 industry chain mapping 輸出路徑。"""

    mapping_dir = MAPPINGS_DIR / _safe_slug(podcast_id, "podcast_id")
    safe_ref = _safe_episode_ref(episode_ref)
    matches = sorted(mapping_dir.glob(f"{safe_ref}__*.industry-map.json"))
    if not matches:
        return None
    json_path = matches[0]
    markdown_path = json_path.with_name(
        json_path.name.removesuffix(".industry-map.json") + ".industry-map.md"
    )
    return IndustryChainMappingAssetPaths(
        json_path=json_path,
        markdown_path=markdown_path,
    )


def external_data_boundary_asset_paths(
    podcast_id: str, episode_ref: str, title: str
) -> ExternalDataBoundaryAssetPaths:
    """回傳 external data boundary 的 JSON 與 Markdown 輸出路徑。"""

    base_path = (
        EXTERNAL_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}"
    )
    return ExternalDataBoundaryAssetPaths(
        json_path=base_path.with_suffix(".external-boundary.json"),
        markdown_path=base_path.with_suffix(".external-boundary.md"),
    )


def find_external_data_boundary_asset_paths(
    podcast_id: str, episode_ref: str
) -> ExternalDataBoundaryAssetPaths | None:
    """依 episode_ref 尋找既有 external data boundary 輸出路徑。"""

    boundary_dir = EXTERNAL_DIR / _safe_slug(podcast_id, "podcast_id")
    safe_ref = _safe_episode_ref(episode_ref)
    matches = sorted(boundary_dir.glob(f"{safe_ref}__*.external-boundary.json"))
    if not matches:
        return None
    json_path = matches[0]
    markdown_path = json_path.with_name(
        json_path.name.removesuffix(".external-boundary.json") + ".external-boundary.md"
    )
    return ExternalDataBoundaryAssetPaths(
        json_path=json_path,
        markdown_path=markdown_path,
    )


def stock_lens_report_asset_paths(
    podcast_id: str, stock_query: str
) -> StockLensReportAssetPaths:
    """回傳 stock lens report 的 JSON 與 Markdown 輸出路徑。"""

    base_path = (
        STOCK_LENS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / title_slug(stock_query, "stock")
    )
    return StockLensReportAssetPaths(
        json_path=base_path.with_suffix(".stock-lens.json"),
        markdown_path=base_path.with_suffix(".stock-lens.md"),
    )


def stock_lens_synthesis_asset_paths(
    podcast_id: str, stock_query: str
) -> StockLensSynthesisAssetPaths:
    """回傳 stock lens LLM synthesis 的 JSON 與 Markdown 輸出路徑。"""

    base_path = (
        STOCK_LENS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / title_slug(stock_query, "stock")
    )
    return StockLensSynthesisAssetPaths(
        json_path=base_path.with_suffix(".stock-lens-synthesis.json"),
        markdown_path=base_path.with_suffix(".stock-lens-synthesis.md"),
    )


def corpus_index_asset_paths(podcast_id: str) -> CorpusIndexAssetPaths:
    """回傳 corpus artifact index 的 JSON 與 Markdown 輸出路徑。"""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusIndexAssetPaths(
        json_path=base_dir / "corpus-index.json",
        markdown_path=base_dir / "corpus-index.md",
    )


def corpus_remediation_plan_asset_paths(
    podcast_id: str,
) -> CorpusRemediationPlanAssetPaths:
    """回傳 corpus remediation plan 的 JSON 與 Markdown 輸出路徑。"""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusRemediationPlanAssetPaths(
        json_path=base_dir / "corpus-remediation-plan.json",
        markdown_path=base_dir / "corpus-remediation-plan.md",
    )


def corpus_remediation_run_asset_paths(
    podcast_id: str,
) -> CorpusRemediationRunAssetPaths:
    """回傳 corpus remediation runner report 的 JSON 與 Markdown 輸出路徑。"""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusRemediationRunAssetPaths(
        json_path=base_dir / "corpus-remediation-run.json",
        markdown_path=base_dir / "corpus-remediation-run.md",
    )


def corpus_local_transcription_run_asset_paths(
    podcast_id: str,
) -> CorpusLocalTranscriptionRunAssetPaths:
    """回傳 corpus local transcription runner report 的 JSON 與 Markdown 輸出路徑。"""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusLocalTranscriptionRunAssetPaths(
        json_path=base_dir / "corpus-local-transcription-run.json",
        markdown_path=base_dir / "corpus-local-transcription-run.md",
    )


def corpus_audio_download_run_asset_paths(
    podcast_id: str,
) -> CorpusAudioDownloadRunAssetPaths:
    """回傳 corpus audio download runner report 的 JSON 與 Markdown 輸出路徑。"""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusAudioDownloadRunAssetPaths(
        json_path=base_dir / "corpus-audio-download-run.json",
        markdown_path=base_dir / "corpus-audio-download-run.md",
    )


def corpus_episode_seed_asset_path(podcast_id: str, episode_ref: str) -> Path:
    """Return deterministic corpus episode seed metadata path."""

    return (
        CORPUS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / "episode-seeds"
        / f"{_safe_episode_ref(episode_ref)}.episode-seed.json"
    )


def corpus_episode_intake_run_asset_paths(
    podcast_id: str,
) -> CorpusEpisodeIntakeRunAssetPaths:
    """Return corpus episode intake latest JSON and Markdown report paths."""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusEpisodeIntakeRunAssetPaths(
        json_path=base_dir / "corpus-episode-intake-run.json",
        markdown_path=base_dir / "corpus-episode-intake-run.md",
    )


def corpus_episode_workflow_run_asset_paths(
    podcast_id: str,
) -> CorpusEpisodeWorkflowRunAssetPaths:
    """Return corpus episode workflow latest JSON and Markdown report paths."""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusEpisodeWorkflowRunAssetPaths(
        json_path=base_dir / "corpus-episode-workflow-run.json",
        markdown_path=base_dir / "corpus-episode-workflow-run.md",
    )


def corpus_semantic_remediation_run_asset_paths(
    podcast_id: str,
) -> CorpusSemanticRemediationRunAssetPaths:
    """Return semantic remediation latest JSON and Markdown report paths."""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusSemanticRemediationRunAssetPaths(
        json_path=base_dir / "corpus-semantic-remediation-run.json",
        markdown_path=base_dir / "corpus-semantic-remediation-run.md",
    )


def corpus_episode_completion_workflow_run_asset_paths(
    podcast_id: str,
) -> CorpusEpisodeCompletionWorkflowRunAssetPaths:
    """Return completion workflow latest JSON and Markdown report paths."""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusEpisodeCompletionWorkflowRunAssetPaths(
        json_path=base_dir / "corpus-episode-completion-workflow-run.json",
        markdown_path=base_dir / "corpus-episode-completion-workflow-run.md",
    )


def corpus_latest_episode_deterministic_workflow_run_asset_paths(
    podcast_id: str,
) -> CorpusLatestEpisodeDeterministicWorkflowRunAssetPaths:
    """Return latest deterministic workflow JSON and Markdown report paths."""

    base_dir = CORPUS_DIR / _safe_slug(podcast_id, "podcast_id")
    return CorpusLatestEpisodeDeterministicWorkflowRunAssetPaths(
        json_path=base_dir / "corpus-latest-episode-deterministic-workflow-run.json",
        markdown_path=base_dir / "corpus-latest-episode-deterministic-workflow-run.md",
    )


def study_guide_bundle_paths(
    podcast_id: str, episode_ref: str, title: str
) -> StudyGuideBundlePaths:
    """Return the four canonical study-guide Markdown paths for one episode."""

    return study_guide_bundle_paths_from_stem(
        podcast_id,
        f"{_safe_episode_ref(episode_ref)}__{title_slug(title, episode_ref)}",
    )


def study_guide_bundle_paths_from_stem(
    podcast_id: str, identity_stem: str
) -> StudyGuideBundlePaths:
    """Return bundle paths for a canonical ``{episode_ref}__{title_slug}`` stem."""

    if (
        not identity_stem
        or "/" in identity_stem
        or "\\" in identity_stem
        or ".." in identity_stem
    ):
        raise ValueError("study-guide identity stem is not a safe filename")
    bundle_dir = (
        STUDY_GUIDES_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / identity_stem
    )
    return StudyGuideBundlePaths(
        bundle_dir=bundle_dir,
        cover_path=bundle_dir / "00_video_info.md",
        summary_path=bundle_dir / "03_full_summary.md",
        notes_path=bundle_dir / "04_learning_notes.md",
        guide_path=bundle_dir / "07_final_study_guide.md",
    )


def study_guide_run_asset_paths(
    podcast_id: str, episode_ref: str
) -> StudyGuideRunAssetPaths:
    """Return metadata-only study-guide run report paths."""

    run_dir = (
        CORPUS_DIR
        / _safe_slug(podcast_id, "podcast_id")
        / "study-guide-runs"
    )
    ref = _safe_episode_ref(episode_ref)
    return StudyGuideRunAssetPaths(
        json_path=run_dir / f"{ref}.study-guide-run.json",
        markdown_path=run_dir / f"{ref}.study-guide-run.md",
    )


def latest_episode_verified_research_report_paths(
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> LatestEpisodeVerifiedResearchReportPaths:
    """Return SPEC 018 report and checkpoint paths without creating directories."""

    if not isinstance(source_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", source_digest):
        raise ValueError("source_digest must be a lowercase SHA-256 hex digest.")
    safe_podcast_id = _safe_slug(podcast_id, "podcast_id")
    safe_episode_ref = _safe_episode_ref(episode_ref)
    bundle_dir = (
        RESEARCH_REPORTS_DIR
        / safe_podcast_id
        / safe_episode_ref
        / f"v1-{source_digest}"
    )
    checkpoint_path = (
        CORPUS_DIR
        / safe_podcast_id
        / "verified-research"
        / f"{safe_episode_ref}.checkpoint.json"
    )
    return LatestEpisodeVerifiedResearchReportPaths(
        bundle_dir=bundle_dir,
        report_json_path=bundle_dir / "report.json",
        report_markdown_path=bundle_dir / "report.md",
        manifest_path=bundle_dir / "manifest.json",
        checkpoint_path=checkpoint_path,
    )


def cache_path(podcast_id: str) -> Path:
    """回傳 episode cache 路徑。"""

    return CACHE_DIR / _safe_slug(podcast_id, "podcast_id") / "episodes.json"


def cache_db_path() -> Path:
    """回傳 SQLite metadata cache 路徑。"""

    return CACHE_DIR / "podcast_ingest.sqlite3"


def ensure_data_directories() -> None:
    """建立 Phase 0 規定的 data 子目錄。"""

    for directory in (
        AUDIO_DIR,
        TRANSCRIPTS_DIR,
        SUMMARIES_DIR,
        MENTIONS_DIR,
        REPORTS_DIR,
        MAPPINGS_DIR,
        EXTERNAL_DIR,
        STOCK_LENS_DIR,
        CACHE_DIR,
        CORPUS_DIR,
        STUDY_GUIDES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def _safe_slug(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _SAFE_SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} 必須是小寫 slug，只允許 a-z、0-9 與 -。")
    return value


def is_safe_episode_ref(value: object, *, max_length: int | None = None) -> bool:
    """Return whether ``value`` is a legal corpus episode_ref.

    The alphabet is A-Z, a-z, 0-9, hyphen, and underscore. Underscore is
    required for YouTube video ids. It is not a path separator.
    """

    if not isinstance(value, str) or not _SAFE_EPISODE_REF_PATTERN.fullmatch(value):
        return False
    if max_length is not None and len(value) > max_length:
        return False
    return True


def _safe_episode_ref(value: str) -> str:
    if not is_safe_episode_ref(value):
        raise ValueError("episode_ref 必須只包含 A-Z、a-z、0-9、- 與 _。")
    return value


def _normalize_extension(extension: str) -> str:
    normalized = extension.strip().lower()
    if not normalized:
        return ".mp3"
    if not normalized.startswith("."):
        normalized = f".{normalized}"
    return normalized


def _is_safe_filename_character(character: str) -> bool:
    if character in {"_", "-"} or character.isspace():
        return True
    if character.isascii() and character.isalnum():
        return True
    if "\u4e00" <= character <= "\u9fff":
        return True
    category = unicodedata.category(character)
    if category.startswith("C") or category.startswith("S"):
        return False
    return False
