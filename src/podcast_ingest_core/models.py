from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PodcastProfile:
    """Podcast 設定檔中的單一 profile。"""

    podcast_id: str
    display_name: str
    rss_url: str
    language: str
    default_episode_prefix: str


@dataclass(frozen=True)
class Episode:
    """Podcast episode 的核心資料模型。"""

    podcast_id: str
    episode_ref: str
    title: str
    audio_url: str | None = None
    published_at: str | None = None
    description: str | None = None
    source_url: str | None = None
    duration: str | None = None
    guid: str | None = None
    link: str | None = None


@dataclass(frozen=True)
class AudioAsset:
    """下載後音檔的位置與來源 metadata。"""

    podcast_id: str
    episode_ref: str
    title: str
    source_url: str
    local_path: Path
    content_type: str | None = None
    size_bytes: int | None = None
    downloaded: bool = False
    already_exists: bool = False


@dataclass(frozen=True)
class TranscriptResult:
    """轉錄結果的位置與基本 metadata。"""

    podcast_id: str
    episode_ref: str
    transcript_path: Path
    language: str


@dataclass(frozen=True)
class TranscriptAsset:
    """逐字稿輸出的三種檔案與轉錄 metadata。"""

    podcast_id: str
    episode_ref: str
    title: str
    audio_path: Path
    text_path: Path
    srt_path: Path
    json_path: Path
    model: str
    language: str
    segment_count: int
    device: str = "cpu"
    compute_type: str = "int8"
    vad_filter: bool = False
    transcribed: bool = False
    already_exists: bool = False


@dataclass(frozen=True)
class TranscriptValidationResult:
    """逐字稿輸出完整性檢查結果。"""

    podcast_id: str
    episode_ref: str
    valid: bool
    status: str
    segment_count: int
    last_segment_end_seconds: float | None
    transcript_text_length: int
    problems: list[str]
    warnings: list[str]
    paths: dict[str, str]


@dataclass(frozen=True)
class SummaryResult:
    """摘要結果的位置與基本 metadata。"""

    podcast_id: str
    episode_ref: str
    summary_path: Path


@dataclass(frozen=True)
class SummaryAsset:
    """Markdown 摘要輸出的位置與來源逐字稿 metadata。"""

    podcast_id: str
    episode_ref: str
    title: str
    summary_path: Path
    transcript_json_path: Path
    transcript_text_path: Path
    segment_count: int
    summary_mode: str
    generated: bool = False
    already_exists: bool = False
    provider: str | None = None
    model: str | None = None
    chunk_count: int | None = None
    evidence_count: int | None = None


@dataclass(frozen=True)
class MentionEvidence:
    """Mention 在 transcript segment 中的 timestamp evidence。"""

    segment_id: int | str
    start: float | None
    end: float | None
    timestamp: str
    text: str


@dataclass(frozen=True)
class Mention:
    """Deterministic rule 擷取出的 mention。"""

    type: str
    text: str
    normalized_text: str
    evidence: list[MentionEvidence]
    count: int
    confidence: str


@dataclass(frozen=True)
class MentionExtractionAsset:
    """Mention extraction 輸出的位置與來源 transcript metadata。"""

    podcast_id: str
    episode_ref: str
    title: str
    source_transcript_json_path: Path
    mentions_json_path: Path
    mentions_markdown_path: Path
    mention_count: int
    segment_count: int
    extraction_mode: str
    generated: bool
    already_exists: bool


@dataclass(frozen=True)
class EpisodeIntelligenceReportAsset:
    """Episode intelligence report 的 JSON 與 Markdown 輸出位置。"""

    podcast_id: str
    episode_ref: str
    title: str
    report_json_path: Path
    report_markdown_path: Path
    transcript_status: str
    segment_count: int
    generated: bool
    already_exists: bool
    source_status_warnings: list[str]


@dataclass(frozen=True)
class MappingEvidence:
    """Industry mapping 中可追溯的 podcast evidence。"""

    segment_id: int | str
    start: float | None
    end: float | None
    timestamp: str
    text: str


@dataclass(frozen=True)
class StockCandidate:
    """產業鏈 mapping 產生的股票或公司候選。"""

    company_name: str
    tickers: list[str]
    relation: str
    relation_type: str
    evidence_status: str
    verification_status: str
    source_terms: list[str]
    evidence: list[MappingEvidence]


@dataclass(frozen=True)
class IndustryChainNode:
    """Podcast 線索對應的產業鏈節點。"""

    node_id: str
    label: str
    source_terms: list[str]
    evidence: list[MappingEvidence]
    stock_candidates: list[StockCandidate]


@dataclass(frozen=True)
class IndustryChainMappingAsset:
    """Industry chain mapping 的 JSON 與 Markdown 輸出位置。"""

    podcast_id: str
    episode_ref: str
    title: str
    mapping_json_path: Path
    mapping_markdown_path: Path
    mapping_status: str
    node_count: int
    candidate_count: int
    warning_count: int
    generated: bool
    already_exists: bool


@dataclass(frozen=True)
class ExternalDataBoundaryAsset:
    """External data boundary 的 JSON 與 Markdown 輸出位置。"""

    podcast_id: str
    episode_ref: str
    title: str
    boundary_json_path: Path
    boundary_markdown_path: Path
    boundary_status: str
    candidate_count: int
    warning_count: int
    generated: bool
    already_exists: bool


@dataclass(frozen=True)
class ExternalDataVerificationAsset:
    """External data fixture verification 的 dry-run plan 或輸出位置。"""

    podcast_id: str
    episode_ref: str
    title: str
    boundary_json_path: Path
    boundary_markdown_path: Path
    verification_status: str
    candidate_count: int
    verified_candidate_count: int
    warning_count: int
    dry_run: bool
    requires_confirmation: bool
    provider: str
    fixture_path: Path
    planned_reads: list[str]
    planned_writes: list[str]
    generated: bool
    already_exists: bool
    not_investment_advice: bool


@dataclass(frozen=True)
class GooayeLensDimension:
    """Gooaye Lens 中單一分析維度。"""

    id: str
    label: str
    description: str
    analysis_questions: list[str]
    expected_evidence_sources: list[str]
    output_guidance: str


@dataclass(frozen=True)
class GooayeLensModel:
    """可重用的 Gooaye-style research lens model。"""

    version: int
    name: str
    description: str
    dimensions: list[GooayeLensDimension]
    safety_rules: list[str]


@dataclass(frozen=True)
class LLMProfile:
    """本機 LLM profile 設定，不包含 API key 值。"""

    profile_id: str
    provider: str
    model: str
    base_url: str | None
    api_key_env: str


@dataclass(frozen=True)
class StockLensReportAsset:
    """Stock lens report 的 JSON 與 Markdown 輸出位置。"""

    podcast_id: str
    stock_query: str
    report_json_path: Path
    report_markdown_path: Path
    report_status: str
    match_count: int
    warning_count: int
    generated: bool
    already_exists: bool


@dataclass(frozen=True)
class StockLensSynthesisResult:
    """Stock lens LLM synthesis 的 dry-run plan 或輸出位置。"""

    podcast_id: str
    stock_query: str
    synthesis_json_path: Path
    synthesis_markdown_path: Path
    source_stock_lens_json_path: Path
    synthesis_status: str
    source_report_status: str
    dry_run: bool
    requires_confirmation: bool
    requires_api_cost_ack: bool
    required_acknowledgement: str | None
    planned_reads: list[str]
    planned_writes: list[str]
    risks: list[str]
    generated: bool
    already_exists: bool
    provider: str | None
    model: str | None
    prompt_char_count: int | None
    warning_count: int
    not_investment_advice: bool


@dataclass(frozen=True)
class ResearchLLMSmokeReviewResult:
    """Research LLM smoke review gate 的報告輸出位置與彙總狀態。"""

    podcast_id: str
    episode_ref: str
    stock_query: str
    review_status: str
    review_json_path: Path
    review_markdown_path: Path
    synthesis_json_path: Path
    synthesis_markdown_path: Path
    workflow_stdout_path: Path | None
    raw_output_path: Path | None
    check_count: int
    failed_check_count: int
    warning_count: int
    blocked_check_count: int


@dataclass(frozen=True)
class SemanticSummarySmokeReviewResult:
    """Semantic summary smoke review gate 的報告輸出位置與彙總狀態。"""

    podcast_id: str
    episode_ref: str
    review_status: str
    review_json_path: Path
    review_markdown_path: Path
    semantic_summary_path: Path | None
    workflow_stdout_path: Path | None
    check_count: int
    failed_check_count: int
    warning_count: int
    blocked_check_count: int


@dataclass(frozen=True)
class ResearchWorkflowStep:
    """Research workflow 中單一步驟的計畫或執行結果。"""

    name: str
    status: str
    action: str
    planned_reads: list[str]
    planned_writes: list[str]
    risks: list[str]
    generated_artifacts: list[str]
    reused_artifacts: list[str]


@dataclass(frozen=True)
class ResearchWorkflowResult:
    """Research workflow dry-run action plan 或 confirm 執行結果。"""

    podcast_id: str
    episode_ref: str
    stock_query: str | None
    workflow_status: str
    dry_run: bool
    requires_confirmation: bool
    requires_api_cost_ack: bool
    required_acknowledgement: str | None
    transcript_status: str
    steps: list[ResearchWorkflowStep]
    planned_reads: list[str]
    planned_writes: list[str]
    written_artifacts: list[str]
    generated_artifacts: list[str]
    reused_artifacts: list[str]
    external_api_steps: list[str]
    warnings: list[str]
    not_investment_advice: bool


@dataclass(frozen=True)
class EpisodeIndexResult:
    """單集 artifact 寫入 SQLite cache 的結果。"""

    podcast_id: str
    episode_ref: str
    indexed: bool
    transcript_segment_count: int
    mention_count: int
    problems: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class CacheRebuildResult:
    """重建 SQLite cache 的彙總結果。"""

    db_path: str
    indexed_episode_count: int
    skipped_episode_count: int
    problems: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class TranscriptSearchResult:
    """SQLite cache 中的逐字稿搜尋結果。"""

    podcast_id: str
    episode_ref: str
    title: str
    segment_id: int | str
    start: float | None
    end: float | None
    timestamp: str
    text: str
    matched_text: str | None = None
    highlighted_text: str | None = None
    context_before: list[str] | None = None
    context_after: list[str] | None = None
    search_mode: str | None = None
    score: float | None = None


@dataclass(frozen=True)
class MentionSearchResult:
    """SQLite cache 中的 mention 搜尋結果。"""

    podcast_id: str
    episode_ref: str
    title: str
    mention_type: str
    text: str
    normalized_text: str
    count: int
    evidence_timestamp: str
    evidence_text: str
    highlighted_text: str | None = None
    search_mode: str | None = None
