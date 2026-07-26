from __future__ import annotations

from dataclasses import dataclass, field
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
class CorpusArtifactFamilyCounts:
    """Corpus index 中單一 artifact family 的可用性彙總。"""

    available: int
    missing: int
    unreadable: int


@dataclass(frozen=True)
class CorpusEpisodeRow:
    """Corpus index 中單一 episode 的 artifact 狀態列。"""

    podcast_id: str
    episode_ref: str
    title: str
    artifact_status: dict[str, dict]
    missing_artifacts: list[str]
    warnings: list[str]
    source_metadata: dict[str, dict] = field(default_factory=dict)


@dataclass(frozen=True)
class CorpusIndexResult:
    """Corpus artifact index 的輸出位置與彙總 metadata。"""

    podcast_id: str
    index_json_path: Path
    index_markdown_path: Path
    episode_count: int
    warning_count: int
    artifact_family_counts: dict[str, CorpusArtifactFamilyCounts]


@dataclass(frozen=True)
class CorpusRemediationActionCounts:
    """Corpus remediation plan 的 action 彙總。"""

    action_count: int
    blocked_action_count: int
    optional_action_count: int
    gated_action_count: int


@dataclass(frozen=True)
class CorpusRemediationBlocker:
    """單一 remediation action 的上游阻擋原因。"""

    blocked_artifact: str
    blocking_artifact: str
    blocking_status: str
    message: str


@dataclass(frozen=True)
class CorpusRemediationWarning:
    """Corpus remediation plan 中可歸屬的警告。"""

    scope: str
    episode_ref: str | None
    artifact_family: str | None
    message: str


@dataclass(frozen=True)
class CorpusRemediationAction:
    """單一 episode artifact 的建議 remediation action。"""

    action_id: str
    artifact_family: str
    action_type: str
    status: str
    order: int
    reason: str
    blocking_artifacts: list[str]
    suggested_command: str | None
    manual_only: bool
    optional: bool
    gated: bool
    requires_api_cost_ack: bool


@dataclass(frozen=True)
class CorpusRemediationEpisodeRow:
    """Corpus remediation plan 中單一 episode 的 action 與 blocker 狀態列。"""

    podcast_id: str
    episode_ref: str
    title: str
    artifact_status: dict[str, dict]
    missing_artifacts: list[str]
    blockers: list[CorpusRemediationBlocker]
    warnings: list[CorpusRemediationWarning]
    actions: list[CorpusRemediationAction]


@dataclass(frozen=True)
class CorpusRemediationPlanResult:
    """Corpus remediation plan 的輸出位置與彙總 metadata。"""

    podcast_id: str
    plan_json_path: Path
    plan_markdown_path: Path
    source_corpus_index_json_path: Path
    source_corpus_index_markdown_path: Path
    episode_count: int
    warning_count: int
    action_counts: CorpusRemediationActionCounts


@dataclass(frozen=True)
class CorpusRemediationRunFilter:
    """Corpus remediation runner 的選取篩選條件。"""

    episode_ref: str | None
    action_family: str | None
    max_actions: int | None


@dataclass(frozen=True)
class CorpusRemediationRunCounts:
    """Corpus remediation runner 的 outcome 彙總。"""

    row_count: int
    selected_count: int
    executed_count: int
    reused_count: int
    failed_count: int
    skipped_count: int
    blocked_count: int
    excluded_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusRemediationRunWarning:
    """Corpus remediation runner 的非致命警告。"""

    scope: str
    episode_ref: str | None
    artifact_family: str | None
    message: str


@dataclass(frozen=True)
class CorpusRemediationRunRow:
    """Corpus remediation runner 中單一 action 的 outcome 列。"""

    action_id: str
    podcast_id: str
    episode_ref: str
    title: str
    artifact_family: str
    source_status: str
    outcome_status: str
    reason: str
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class CorpusRemediationRunResult:
    """Corpus remediation runner 的 dry-run 或 confirmed 結果。"""

    podcast_id: str
    run_mode: str
    confirm: bool
    source_remediation_plan_json_path: Path
    source_remediation_plan_markdown_path: Path
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusRemediationRunFilter
    counts: CorpusRemediationRunCounts
    rows: list[CorpusRemediationRunRow]
    warnings: list[CorpusRemediationRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusLocalTranscriptionRunFilter:
    """Corpus local transcription runner 的單集篩選條件。"""

    episode_ref: str | None


@dataclass(frozen=True)
class CorpusLocalTranscriptionOutcomeCounts:
    """Corpus local transcription runner 的 outcome 彙總。"""

    row_count: int
    selected_count: int
    executed_count: int
    reused_count: int
    failed_count: int
    skipped_count: int
    rejected_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusLocalTranscriptionRunWarning:
    """Corpus local transcription runner 的非致命警告。"""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusLocalTranscriptionRunRow:
    """Corpus local transcription runner 中單一 transcript action 的 outcome 列。"""

    action_id: str
    podcast_id: str
    episode_ref: str
    title: str
    transcript_status: str
    audio_status: str
    audio_path: str | None
    outcome_status: str
    reason: str
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class CorpusLocalTranscriptionRunResult:
    """Corpus local transcription runner 的 dry-run 或 confirmed 結果。"""

    podcast_id: str
    run_mode: str
    confirm: bool
    source_remediation_plan_json_path: Path
    source_remediation_plan_markdown_path: Path
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusLocalTranscriptionRunFilter
    counts: CorpusLocalTranscriptionOutcomeCounts
    rows: list[CorpusLocalTranscriptionRunRow]
    warnings: list[CorpusLocalTranscriptionRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusAudioDownloadRunFilter:
    """Corpus audio download runner 的單集篩選條件。"""

    episode_ref: str | None


@dataclass(frozen=True)
class CorpusAudioDownloadOutcomeCounts:
    """Corpus audio download runner 的 outcome 彙總。"""

    row_count: int
    selected_count: int
    downloaded_count: int
    reused_count: int
    failed_count: int
    skipped_count: int
    rejected_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusAudioDownloadRunWarning:
    """Corpus audio download runner 的非致命警告。"""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusAudioDownloadRunRow:
    """Corpus audio download runner 中單一 audio action 的 outcome 列。"""

    action_id: str
    podcast_id: str
    episode_ref: str
    audio_status: str
    outcome_status: str
    reason: str
    planned_reads: list[str]
    planned_writes: list[str]
    local_audio_path: str | None
    content_type: str | None
    size_bytes: int | None
    warnings: list[str]


@dataclass(frozen=True)
class CorpusAudioDownloadRunResult:
    """Corpus audio download runner 的 dry-run 或 confirmed 結果。"""

    podcast_id: str
    run_mode: str
    confirm: bool
    source_remediation_plan_json_path: Path
    source_remediation_plan_markdown_path: Path
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusAudioDownloadRunFilter
    counts: CorpusAudioDownloadOutcomeCounts
    rows: list[CorpusAudioDownloadRunRow]
    warnings: list[CorpusAudioDownloadRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusEpisodeIntakeFilter:
    """Corpus episode intake bootstrap 的 selector 篩選條件。"""

    episode_ref: str


@dataclass(frozen=True)
class CorpusEpisodeIntakeOutcomeCounts:
    """Corpus episode intake bootstrap 的 outcome 彙總。"""

    row_count: int
    selected_count: int
    seeded_count: int
    reused_count: int
    failed_count: int
    skipped_count: int
    rejected_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusEpisodeIntakeRunWarning:
    """Corpus episode intake bootstrap 的非致命警告。"""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusEpisodeSeed:
    """讓 RSS episode 進入離線 corpus 的安全 seed metadata。"""

    podcast_id: str
    episode_ref: str
    title: str
    published_at: str | None
    duration: str | None
    guid_status: str
    has_audio_url: bool
    seed_source: str
    selector: str
    warning_count: int
    warnings: list[str]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusEpisodeIntakeRunRow:
    """Corpus episode intake bootstrap 中單一 selector 的 outcome 列。"""

    podcast_id: str
    selector: str
    episode_ref: str | None
    title: str | None
    published_at: str | None
    duration: str | None
    guid_status: str
    has_audio_url: bool
    outcome_status: str
    reason: str
    planned_reads: list[str]
    planned_writes: list[str]
    seed_json_path: str | None
    warnings: list[str]


@dataclass(frozen=True)
class CorpusEpisodeIntakeRunResult:
    """Corpus episode intake bootstrap 的 dry-run 或 confirmed 結果。"""

    podcast_id: str
    run_mode: str
    confirm: bool
    selector: str
    resolved_episode_ref: str | None
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusEpisodeIntakeFilter
    counts: CorpusEpisodeIntakeOutcomeCounts
    rows: list[CorpusEpisodeIntakeRunRow]
    warnings: list[CorpusEpisodeIntakeRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusEpisodeWorkflowRunFilter:
    """Corpus fresh episode workflow runner selector options."""

    episode_ref: str
    stage: str
    max_actions: int | None


@dataclass(frozen=True)
class CorpusEpisodeWorkflowRunCounts:
    """Corpus fresh episode workflow runner outcome counts."""

    row_count: int
    selected_count: int
    executed_count: int
    reused_count: int
    failed_count: int
    skipped_count: int
    blocked_count: int
    rejected_count: int
    manual_only_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusEpisodeWorkflowRunWarning:
    """Corpus fresh episode workflow runner non-fatal warning."""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusEpisodeWorkflowRunRow:
    """One selected, executed, skipped, blocked, or manual-only workflow stage."""

    stage: str
    status: str
    reason: str
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    source_report_paths: list[str]
    stage_counts: dict[str, int]
    warnings: list[str]


@dataclass(frozen=True)
class CorpusEpisodeWorkflowRunResult:
    """Corpus fresh episode workflow runner dry-run or confirmed result."""

    podcast_id: str
    run_mode: str
    confirm: bool
    selector: str
    episode_ref: str | None
    stage: str
    selected_stage: str
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusEpisodeWorkflowRunFilter
    counts: CorpusEpisodeWorkflowRunCounts
    rows: list[CorpusEpisodeWorkflowRunRow]
    warnings: list[CorpusEpisodeWorkflowRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusSemanticRemediationRunFilter:
    """Corpus semantic remediation runner normalized request metadata."""

    episode_ref: str
    action: str
    provider: str | None
    model: str | None
    chunk_seconds: int
    max_segments_per_chunk: int


@dataclass(frozen=True)
class CorpusSemanticRemediationRunCounts:
    """Corpus semantic remediation runner outcome counts."""

    row_count: int
    selected_count: int
    executed_count: int
    reused_count: int
    completed_count: int
    failed_count: int
    blocked_count: int
    rejected_count: int
    manual_only_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusSemanticRemediationRunWarning:
    """Corpus semantic remediation runner bounded warning."""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusSemanticRemediationRunRow:
    """One semantic remediation decision or confirmed attempt outcome."""

    episode_ref: str
    action: str
    status: str
    reason: str
    requires_api_cost_ack: bool
    transcript_transfer_risk: bool
    may_incur_api_cost: bool
    manual_only: bool
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    source_report_paths: list[str]
    provider: str | None
    model: str | None
    failure_category: str | None
    warnings: list[str]


@dataclass(frozen=True)
class CorpusSemanticRemediationRunResult:
    """Corpus semantic remediation runner dry-run or confirmed result."""

    podcast_id: str
    run_mode: str
    confirm: bool
    episode_ref: str
    requested_action: str
    selected_action: str
    executed_action: str | None
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusSemanticRemediationRunFilter
    counts: CorpusSemanticRemediationRunCounts
    rows: list[CorpusSemanticRemediationRunRow]
    warnings: list[CorpusSemanticRemediationRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusEpisodeCompletionWorkflowRunFilter:
    """Normalized non-secret completion workflow request metadata."""

    episode_ref: str
    action: str
    transcription_model: str | None
    transcription_device: str
    transcription_compute_type: str
    transcription_vad_filter: bool
    semantic_provider: str | None
    semantic_model: str | None
    semantic_chunk_seconds: int
    semantic_max_segments_per_chunk: int


@dataclass(frozen=True)
class CorpusEpisodeCompletionWorkflowRunCounts:
    """Completion workflow outcome counts."""

    row_count: int
    selected_count: int
    executed_count: int
    reused_count: int
    completed_count: int
    failed_count: int
    blocked_count: int
    rejected_count: int
    manual_only_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusEpisodeCompletionWorkflowRunWarning:
    """Bounded completion workflow warning."""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusEpisodeCompletionWorkflowRunRow:
    """One completion workflow decision or stage attempt."""

    episode_ref: str | None
    action: str
    status: str
    reason: str
    requires_confirmation: bool
    requires_api_cost_ack: bool
    network_risk: bool
    local_compute_risk: bool
    transcript_transfer_risk: bool
    may_incur_api_cost: bool
    manual_only: bool
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    source_report_paths: list[str]
    stage_counts: dict[str, int]
    provider: str | None
    model: str | None
    failure_category: str | None
    warnings: list[str]


@dataclass(frozen=True)
class CorpusEpisodeCompletionWorkflowRunResult:
    """Dry-run or confirmed single-action completion workflow result."""

    podcast_id: str
    run_mode: str
    confirm: bool
    selector: str
    episode_ref: str | None
    requested_action: str
    selected_action: str
    executed_action: str | None
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusEpisodeCompletionWorkflowRunFilter
    counts: CorpusEpisodeCompletionWorkflowRunCounts
    rows: list[CorpusEpisodeCompletionWorkflowRunRow]
    warnings: list[CorpusEpisodeCompletionWorkflowRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class CorpusLatestEpisodeDeterministicWorkflowRunFilter:
    """Normalized non-secret latest deterministic workflow request metadata."""

    transcription_model: str | None
    transcription_device: str
    transcription_compute_type: str
    transcription_vad_filter: bool


@dataclass(frozen=True)
class CorpusLatestEpisodeDeterministicWorkflowRunCounts:
    """Latest deterministic workflow outcome counts."""

    row_count: int
    selected_count: int
    executed_count: int
    reused_count: int
    ready_count: int
    failed_count: int
    blocked_count: int
    rejected_count: int
    warning_count: int


@dataclass(frozen=True)
class CorpusLatestEpisodeDeterministicWorkflowRunWarning:
    """Bounded latest deterministic workflow warning."""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class CorpusLatestEpisodeDeterministicWorkflowRunRow:
    """One latest deterministic workflow decision or action attempt."""

    episode_ref: str | None
    stage: str
    action_id: str | None
    status: str
    reason: str
    requires_confirmation: bool
    network_risk: bool
    local_compute_risk: bool
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    source_report_paths: list[str]
    failure_category: str | None
    warnings: list[str]


@dataclass(frozen=True)
class CorpusLatestEpisodeDeterministicWorkflowRunResult:
    """Dry-run or confirmed latest deterministic workflow result."""

    podcast_id: str
    run_mode: str
    confirm: bool
    selector: str
    episode_ref: str | None
    outcome: str
    report_json_path: Path | None
    report_markdown_path: Path | None
    filters: CorpusLatestEpisodeDeterministicWorkflowRunFilter
    counts: CorpusLatestEpisodeDeterministicWorkflowRunCounts
    rows: list[CorpusLatestEpisodeDeterministicWorkflowRunRow]
    warnings: list[CorpusLatestEpisodeDeterministicWorkflowRunWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class LatestEpisodeVerifiedResearchReportWorkflowRunFilter:
    """Normalized bounded inputs for the SPEC 018 report workflow."""

    expected_episode_ref: str | None
    stock_query: str | None
    include_fixture_verification: bool
    transcription_model: str | None
    transcription_device: str
    transcription_compute_type: str
    transcription_vad_filter: bool
    semantic_provider: str | None
    semantic_model: str | None
    semantic_base_url_identity_sha256: str | None
    semantic_chunk_seconds: int
    semantic_max_segments_per_chunk: int


@dataclass(frozen=True)
class LatestEpisodeVerifiedResearchReportWorkflowStep:
    """A planned or completed bounded SPEC 018 workflow stage."""

    stage: str
    status: str
    reason: str
    requires_confirmation: bool
    requires_api_cost_ack: bool
    network_risk: bool
    local_compute_risk: bool
    transcript_transfer_risk: bool
    may_incur_api_cost: bool
    planned_reads: list[str]
    planned_writes: list[str]
    output_paths: list[str]
    failure_category: str | None


@dataclass(frozen=True)
class LatestEpisodeVerifiedResearchReportWorkflowWarning:
    """A bounded non-fatal SPEC 018 workflow warning."""

    scope: str
    episode_ref: str | None
    message: str


@dataclass(frozen=True)
class LatestEpisodeVerifiedResearchReportWorkflowRunResult:
    """Dry-run or confirmed latest verified research report result."""

    podcast_id: str
    run_mode: str
    confirm: bool
    selector: str
    episode_ref: str | None
    expected_episode_ref: str | None
    outcome: str
    required_api_cost_ack: str
    report_version: str | None
    source_digest: str | None
    bundle_dir: Path | None
    report_json_path: Path | None
    report_markdown_path: Path | None
    manifest_path: Path | None
    checkpoint_path: Path | None
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter
    stage_plan: list[LatestEpisodeVerifiedResearchReportWorkflowStep]
    warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning]
    not_investment_advice: bool


@dataclass(frozen=True)
class EpisodeVerifiedResearchReportWorkflowRunResult:
    """Dry-run or confirmed explicit-episode verified research report result."""

    podcast_id: str
    episode_ref: str
    confirm: bool
    outcome: str
    ready: bool
    missing_roles: list[str]
    stale_roles: list[str]
    failed_gates: list[str]
    report_version: str | None
    source_digest: str | None
    bundle_dir: Path | None
    report_json_path: Path | None
    report_markdown_path: Path | None
    manifest_path: Path | None
    stock_query: str | None
    include_fixture_verification: bool
    warnings: list[str]
    not_investment_advice: bool


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
class VerifiedResearchReportCatalogItem:
    """Sanitized manifest-derived summary for one canonical report bundle."""

    podcast_id: str
    episode_ref: str
    report_version: str
    source_digest: str
    schema_version: str
    include_fixture_verification: bool
    stock_query_present: bool
    semantic_review_status: str
    not_investment_advice: bool


@dataclass(frozen=True)
class VerifiedResearchReportCatalogPage:
    """A bounded page of sanitized verified research report summaries."""

    items: list[VerifiedResearchReportCatalogItem]
    limit: int
    returned_count: int
    catalog_root_status: str
    traversal_status: str


@dataclass(frozen=True)
class VerifiedResearchReportCatalogInspection:
    """Bounded self-consistency verdict for one exact report bundle."""

    locator: dict[str, str]
    bundle_self_consistency_status: str
    checks: dict[str, bool | str]
    source_currentness_status: str
    safe_metadata: VerifiedResearchReportCatalogItem | None
    not_investment_advice: bool | None


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
