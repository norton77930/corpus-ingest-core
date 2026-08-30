class PodcastIngestCoreError(Exception):
    """Base error for Corpus Ingestion Core."""


class EpisodeNotFoundError(PodcastIngestCoreError):
    """The requested episode does not exist."""


class AudioUrlMissingError(PodcastIngestCoreError):
    """The episode carries no downloadable audio URL."""


class DownloadFailedError(PodcastIngestCoreError):
    """Audio download failed."""


class AudioFileMissingError(PodcastIngestCoreError):
    """The local audio file is missing at transcription time."""


class TranscriptionDependencyError(PodcastIngestCoreError):
    """A transcription dependency is unavailable."""


class TranscriptionFailedError(PodcastIngestCoreError):
    """Transcription or its output write failed."""


class TranscriptMissingError(PodcastIngestCoreError):
    """The transcript output that summarization needs is missing."""


class TranscriptParseError(PodcastIngestCoreError):
    """The transcript JSON does not match what summarization requires."""


class SummaryFailedError(PodcastIngestCoreError):
    """Summary generation or its output write failed."""


class SemanticSummaryFailedError(PodcastIngestCoreError):
    """Semantic summary generation or its output write failed."""


class StudyGuideBundleError(PodcastIngestCoreError):
    """Study-guide bundle selection, generation, or write failed."""


class WorkflowDerivationError(PodcastIngestCoreError):
    """Workflow derivation selection, generation, or write failed."""


class CorpusIndexFailedError(PodcastIngestCoreError):
    """Corpus artifact index generation or its output write failed."""


class CorpusRemediationPlanFailedError(PodcastIngestCoreError):
    """Corpus remediation plan generation or its output write failed."""


class CorpusRemediationRunnerFailedError(PodcastIngestCoreError):
    """Corpus remediation runner selection, execution, or report write failed."""


class CorpusLocalTranscriptionRunnerFailedError(PodcastIngestCoreError):
    """Corpus local transcription runner selection, execution, or report write failed."""


class CorpusAudioDownloadRunnerFailedError(PodcastIngestCoreError):
    """Corpus audio download runner selection, execution, or report write failed."""


class CorpusEpisodeIntakeFailedError(PodcastIngestCoreError):
    """Corpus episode intake bootstrap selection or report writing failed."""


class CorpusEpisodeWorkflowRunnerFailedError(PodcastIngestCoreError):
    """Corpus episode workflow runner selection, execution, or reporting failed."""


class CorpusSemanticRemediationRunnerFailedError(PodcastIngestCoreError):
    """Corpus semantic remediation runner validation, execution, or reporting failed."""


class CorpusEpisodeCompletionWorkflowRunnerFailedError(PodcastIngestCoreError):
    """Corpus episode completion workflow validation or execution failed."""


class CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError(PodcastIngestCoreError):
    """Latest deterministic episode workflow validation or execution failed."""


class LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(PodcastIngestCoreError):
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
    """The LLM provider configuration is incomplete or invalid."""


class LLMProviderRequestError(PodcastIngestCoreError):
    """An LLM provider request or its response failed."""


class MentionExtractionInputError(PodcastIngestCoreError):
    """Mention extraction received invalid input arguments."""


class MentionExtractionFailedError(PodcastIngestCoreError):
    """Mention extraction or its output write failed."""


class EpisodeIntelligenceReportFailedError(PodcastIngestCoreError):
    """Episode intelligence report generation or its output write failed."""


class IndustryMappingInputError(PodcastIngestCoreError):
    """An industry chain mapping input artifact is unavailable or does not meet requirements."""


class IndustryMappingFailedError(PodcastIngestCoreError):
    """Industry chain mapping generation or its output write failed."""


class ExternalDataBoundaryInputError(PodcastIngestCoreError):
    """An external data boundary input artifact is unavailable or does not meet requirements."""


class ExternalDataBoundaryFailedError(PodcastIngestCoreError):
    """External data boundary generation or its output write failed."""


class ExternalDataVerificationInputError(PodcastIngestCoreError):
    """An external data verification input artifact or provider configuration is invalid."""


class ExternalDataVerificationFailedError(PodcastIngestCoreError):
    """External data verification generation or its output write failed."""


class GooayeLensConfigError(PodcastIngestCoreError):
    """The Gooaye Lens config is missing, corrupt, or does not match the schema."""


class StockLensReportInputError(PodcastIngestCoreError):
    """A stock lens report input artifact is unavailable or does not meet requirements."""


class StockLensReportFailedError(PodcastIngestCoreError):
    """Stock lens report generation or its output write failed."""


class StockLensSynthesisInputError(PodcastIngestCoreError):
    """A stock lens LLM synthesis input artifact or acknowledgement is invalid."""


class StockLensSynthesisFailedError(PodcastIngestCoreError):
    """Stock lens LLM synthesis generation or its output write failed."""


class ResearchWorkflowInputError(PodcastIngestCoreError):
    """A research workflow input artifact is unavailable or does not meet requirements."""


class ResearchWorkflowFailedError(PodcastIngestCoreError):
    """Research workflow execution failed."""


class CacheInitializationError(PodcastIngestCoreError):
    """SQLite cache initialization failed."""


class EpisodeIndexError(PodcastIngestCoreError):
    """Writing one episode's artifacts into the SQLite cache failed."""


class SearchError(PodcastIngestCoreError):
    """SQLite cache search failed."""


class UnsupportedSourceTypeError(PodcastIngestCoreError):
    """An entry point was called for a podcast source_type it does not apply to."""


class XVideoIngestDependencyError(PodcastIngestCoreError):
    """A package required to acquire X videos is missing."""


class XVideoIngestFailedError(PodcastIngestCoreError):
    """The X video acquisition flow failed."""


class VideoAcquireDependencyError(PodcastIngestCoreError):
    """A package required by the shared video acquisition path is missing."""


class VideoAcquireFailedError(PodcastIngestCoreError):
    """Shared video acquisition (metadata / download / audio extraction) failed."""


class YoutubeVideoIngestDependencyError(PodcastIngestCoreError):
    """A package required to acquire YouTube videos is missing."""


class YoutubeVideoIngestFailedError(PodcastIngestCoreError):
    """The YouTube video acquisition flow failed."""


class UnknownSummaryProfileError(PodcastIngestCoreError):
    """The config names a summary_profile that does not exist."""
