class PodcastIngestCoreError(Exception):
    """Podcast Ingestion Core 的基礎錯誤。"""


class EpisodeNotFoundError(PodcastIngestCoreError):
    """找不到指定 episode。"""


class AudioUrlMissingError(PodcastIngestCoreError):
    """Episode 沒有可下載的音檔 URL。"""


class DownloadFailedError(PodcastIngestCoreError):
    """音檔下載失敗。"""


class AudioFileMissingError(PodcastIngestCoreError):
    """轉錄時找不到本機音檔。"""


class TranscriptionDependencyError(PodcastIngestCoreError):
    """轉錄依賴套件不可用。"""


class TranscriptionFailedError(PodcastIngestCoreError):
    """轉錄過程或輸出寫入失敗。"""


class TranscriptMissingError(PodcastIngestCoreError):
    """找不到摘要需要的逐字稿輸出。"""


class TranscriptParseError(PodcastIngestCoreError):
    """逐字稿 JSON 格式不符合摘要需求。"""


class SummaryFailedError(PodcastIngestCoreError):
    """摘要產生或輸出寫入失敗。"""


class SemanticSummaryFailedError(PodcastIngestCoreError):
    """語意摘要產生或輸出寫入失敗。"""


class StudyGuideBundleError(PodcastIngestCoreError):
    """Study-guide bundle selection, generation, or write failed."""


class CorpusIndexFailedError(PodcastIngestCoreError):
    """Corpus artifact index 產生或輸出寫入失敗。"""


class CorpusRemediationPlanFailedError(PodcastIngestCoreError):
    """Corpus remediation plan 產生或輸出寫入失敗。"""


class CorpusRemediationRunnerFailedError(PodcastIngestCoreError):
    """Corpus remediation runner 選取、執行或報告寫入失敗。"""


class CorpusLocalTranscriptionRunnerFailedError(PodcastIngestCoreError):
    """Corpus local transcription runner 選取、執行或報告寫入失敗。"""


class CorpusAudioDownloadRunnerFailedError(PodcastIngestCoreError):
    """Corpus audio download runner 選取、執行或報告寫入失敗。"""


class CorpusEpisodeIntakeFailedError(PodcastIngestCoreError):
    """Corpus episode intake bootstrap selection or report writing failed."""


class CorpusEpisodeWorkflowRunnerFailedError(PodcastIngestCoreError):
    """Corpus episode workflow runner selection, execution, or reporting failed."""


class CorpusSemanticRemediationRunnerFailedError(PodcastIngestCoreError):
    """Corpus semantic remediation runner validation, execution, or reporting failed."""


class CorpusEpisodeCompletionWorkflowRunnerFailedError(PodcastIngestCoreError):
    """Corpus episode completion workflow validation or execution failed."""


class CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError(
    PodcastIngestCoreError
):
    """Latest deterministic episode workflow validation or execution failed."""


class LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
    PodcastIngestCoreError
):
    """Latest verified research report workflow validation or execution failed."""


class EpisodeVerifiedResearchReportWorkflowRunnerFailedError(PodcastIngestCoreError):
    """Explicit-episode verified research report workflow validation failed."""


class VerifiedResearchReportInputError(PodcastIngestCoreError):
    """Verified research source artifacts or report publication are invalid."""


class VerifiedResearchReportCatalogInputError(PodcastIngestCoreError):
    """Verified research report catalog input is invalid."""


class VerifiedResearchReportSourceRevalidationInputError(PodcastIngestCoreError):
    """Verified research report source revalidation input is invalid."""


class VerifiedResearchReportCoverageInputError(PodcastIngestCoreError):
    """Verified research report coverage index input is invalid."""


class HistoricalVerifiedReportPathInputError(PodcastIngestCoreError):
    """Historical verified-report path suggestion input is invalid."""


class VerifiedReportGapBacklogInputError(PodcastIngestCoreError):
    """Verified report gap backlog input is invalid."""


class LLMProviderConfigError(PodcastIngestCoreError):
    """LLM provider 設定不完整或不合法。"""


class LLMProviderRequestError(PodcastIngestCoreError):
    """LLM provider 請求或回應失敗。"""


class MentionExtractionInputError(PodcastIngestCoreError):
    """Mention extraction 輸入參數不合法。"""


class MentionExtractionFailedError(PodcastIngestCoreError):
    """Mention extraction 產生或輸出寫入失敗。"""


class EpisodeIntelligenceReportFailedError(PodcastIngestCoreError):
    """Episode intelligence report 產生或輸出寫入失敗。"""


class IndustryMappingInputError(PodcastIngestCoreError):
    """Industry chain mapping 的輸入 artifact 不可用或不符合需求。"""


class IndustryMappingFailedError(PodcastIngestCoreError):
    """Industry chain mapping 產生或輸出寫入失敗。"""


class ExternalDataBoundaryInputError(PodcastIngestCoreError):
    """External data boundary 的輸入 artifact 不可用或不符合需求。"""


class ExternalDataBoundaryFailedError(PodcastIngestCoreError):
    """External data boundary 產生或輸出寫入失敗。"""


class ExternalDataVerificationInputError(PodcastIngestCoreError):
    """External data verification 的輸入 artifact 或 provider 設定不合法。"""


class ExternalDataVerificationFailedError(PodcastIngestCoreError):
    """External data verification 產生或輸出寫入失敗。"""


class GooayeLensConfigError(PodcastIngestCoreError):
    """Gooaye Lens config 缺失、損壞或不符合 schema。"""


class StockLensReportInputError(PodcastIngestCoreError):
    """Stock lens report 的輸入 artifact 不可用或不符合需求。"""


class StockLensReportFailedError(PodcastIngestCoreError):
    """Stock lens report 產生或輸出寫入失敗。"""


class StockLensSynthesisInputError(PodcastIngestCoreError):
    """Stock lens LLM synthesis 的輸入 artifact 或確認資訊不合法。"""


class StockLensSynthesisFailedError(PodcastIngestCoreError):
    """Stock lens LLM synthesis 產生或輸出寫入失敗。"""


class ResearchWorkflowInputError(PodcastIngestCoreError):
    """Research workflow 的輸入 artifact 不可用或不符合需求。"""


class ResearchWorkflowFailedError(PodcastIngestCoreError):
    """Research workflow 執行失敗。"""


class CacheInitializationError(PodcastIngestCoreError):
    """SQLite cache 初始化失敗。"""


class EpisodeIndexError(PodcastIngestCoreError):
    """單集 artifact 寫入 SQLite cache 失敗。"""


class SearchError(PodcastIngestCoreError):
    """SQLite cache 搜尋失敗。"""


class UnsupportedSourceTypeError(PodcastIngestCoreError):
    """對某個 podcast 來源型別呼叫了不適用的入口。"""


class XVideoIngestDependencyError(PodcastIngestCoreError):
    """缺少取得 X 影片所需的套件。"""


class XVideoIngestFailedError(PodcastIngestCoreError):
    """X 影片取得流程失敗。"""


class VideoAcquireDependencyError(PodcastIngestCoreError):
    """缺少共用影片取得所需的套件。"""


class VideoAcquireFailedError(PodcastIngestCoreError):
    """共用影片取得（metadata / 下載 / 抽音）失敗。"""


class YoutubeVideoIngestDependencyError(PodcastIngestCoreError):
    """缺少取得 YouTube 影片所需的套件。"""


class YoutubeVideoIngestFailedError(PodcastIngestCoreError):
    """YouTube 影片取得流程失敗。"""


class UnknownSummaryProfileError(PodcastIngestCoreError):
    """設定檔指定了不存在的 summary_profile。"""
