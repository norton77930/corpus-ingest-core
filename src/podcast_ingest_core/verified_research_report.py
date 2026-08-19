"""Deterministic assembler and atomic publisher for SPEC 018 report bundles."""

from __future__ import annotations

from dataclasses import dataclass
import errno
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid
from typing import Any

from . import storage
from .artifact_lock import exclusive_artifact_claim
from .errors import VerifiedResearchReportInputError
from .report_safety import (
    OMITTED_VALUE,
    contains_sensitive_text,
    matched_investment_advice_guard,
    safe_text,
    strip_safety_disclaimers,
)
from .semantic_review_artifact import (
    SemanticReviewInspection,
    inspect_semantic_review as _inspect_semantic_review_artifact,
)
from .semantic_summary_identity import canonical_semantic_summary_path_for_title
from .secure_local_snapshot import secure_read_bytes
from .canonical_transcript import (
    CanonicalTranscriptResolutionError,
    resolve_canonical_transcript_asset_paths,
)
from .verified_research_lineage import (
    LINEAGE_QUALITY_GATE,
    LINEAGE_SCHEMA_VERSION,
    _current_verified_research_lineage_evidence,
    validate_current_verified_research_lineage,
)


REPORT_SCHEMA_VERSION = "latest-episode-verified-research-report-v1"
REPORT_VERSION_PREFIX = "v1"
_TIMESTAMP_PATTERN = re.compile(r"^\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]$")
_SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]+", re.IGNORECASE)
_FORBIDDEN_TEXT = (
    "traceback",
    "raw transcript",
    "api_key",
    "authorization",
    "private_key",
    "client_secret",
    "password=",
    "token=",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)


@dataclass(frozen=True)
class VerifiedResearchSourceArtifact:
    """One source artifact hashed at assembly time."""

    role: str
    path: Path
    sha256: str
    size_bytes: int
    identity_valid: bool
    raw_bytes: bytes = b""


@dataclass(frozen=True)
class _CurrentVerifiedResearchSourceSnapshot:
    """Current canonical lineage and one immutable byte snapshot per source."""

    lineage_manifest: dict[str, Any]
    source_artifacts: list[VerifiedResearchSourceArtifact]


@dataclass(frozen=True)
class VerifiedResearchReportAssembly:
    """A deterministic report payload with immutable source snapshots."""

    podcast_id: str
    episode_ref: str
    stock_query: str | None
    include_fixture_verification: bool
    source_digest: str
    report_version: str
    report_payload: dict[str, Any]
    report_markdown: str
    source_artifacts: list[VerifiedResearchSourceArtifact]
    lineage_manifest: dict[str, Any]


@dataclass(frozen=True)
class VerifiedResearchReportBundle:
    """Published or reused report bundle metadata."""

    bundle_dir: Path
    report_json_path: Path
    report_markdown_path: Path
    manifest_path: Path
    source_digest: str
    report_version: str
    reused: bool


def _current_verified_research_source_snapshot(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool,
    summary_options: dict[str, Any] | None = None,
) -> _CurrentVerifiedResearchSourceSnapshot:
    """Read canonical current sources once after trusted lineage validation.

    This seam never assembles, renders, publishes, claims, or writes a report.
    Every pathname used for a read came from the lineage validator's canonical
    current-artifact calculation, not from a published bundle manifest.
    """

    lineage_evidence = _current_verified_research_lineage_evidence(
        podcast_id,
        episode_ref,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
        summary_options=summary_options,
        require_generation_proofs=True,
    )
    lineage_manifest = lineage_evidence.publisher_manifest
    expected_roles = [
        "transcript", "semantic_summary", "semantic_review", "mentions",
        "intelligence", "industry_mapping", "external_boundary",
    ]
    if include_fixture_verification:
        expected_roles.append("fixture")
    if stock_query is not None:
        expected_roles.append("stock_lens")
    artifacts = lineage_evidence.current_artifacts
    if not isinstance(artifacts, dict) or set(artifacts) != set(expected_roles):
        raise VerifiedResearchReportInputError("verified report current lineage role set is invalid")
    snapshots: list[VerifiedResearchSourceArtifact] = []
    for role in expected_roles:
        entry = artifacts.get(role)
        path = entry.get("path") if isinstance(entry, dict) else None
        expected_sha = entry.get("sha256") if isinstance(entry, dict) else None
        if not isinstance(path, str) or not _is_sha256(expected_sha):
            raise VerifiedResearchReportInputError("verified report current lineage source metadata is invalid")
        source = _source_artifact(role, Path(path), True)
        if source.sha256 != expected_sha:
            raise VerifiedResearchReportInputError("verified report current source changed during snapshot")
        snapshots.append(source)
    return _CurrentVerifiedResearchSourceSnapshot(lineage_manifest, snapshots)


def assemble_verified_research_report(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None,
    include_fixture_verification: bool = False,
    summary_options: dict[str, Any] | None = None,
) -> VerifiedResearchReportAssembly:
    """Assemble a report from one immutable byte snapshot per report source."""

    _validate_identifier(podcast_id, "podcast_id", lower_slug=True)
    _validate_identifier(episode_ref, "episode_ref")
    normalized_stock_query = _normalize_stock_query(stock_query)
    if not isinstance(include_fixture_verification, bool):
        raise VerifiedResearchReportInputError("include_fixture_verification is invalid")

    try:
        transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    except CanonicalTranscriptResolutionError as exc:
        raise VerifiedResearchReportInputError("verified report canonical transcript is ambiguous") from exc
    if transcript_paths is None or not all(
        path.is_file()
        for path in (transcript_paths.json_path, transcript_paths.text_path, transcript_paths.srt_path)
    ):
        raise VerifiedResearchReportInputError("verified report transcript artifact contract is invalid")
    snapshot = _current_verified_research_source_snapshot(
        podcast_id,
        episode_ref,
        stock_query=normalized_stock_query,
        include_fixture_verification=include_fixture_verification,
        summary_options=summary_options,
    )
    lineage_manifest = snapshot.lineage_manifest
    sources_by_role = {source.role: source for source in snapshot.source_artifacts}
    transcript_source = sources_by_role["transcript"]
    summary_source = sources_by_role["semantic_summary"]
    review_source = sources_by_role["semantic_review"]
    mentions_source = sources_by_role["mentions"]
    intelligence_source = sources_by_role["intelligence"]
    mapping_source = sources_by_role["industry_mapping"]
    boundary_source = sources_by_role["external_boundary"]
    transcript = _json_from_source(transcript_source, "transcript")
    title = _identity_title(transcript, podcast_id, episode_ref, "transcript")
    _assert_safe_source_bytes(transcript_source, "transcript")
    _validate_transcript_snapshot(transcript)
    semantic_summary = _text_from_source(summary_source, "semantic summary")
    _assert_safe_source_bytes(summary_source, "semantic summary")
    _assert_safe_source_bytes(review_source, "semantic review")
    mentions = _identified_json_from_source(mentions_source, podcast_id, episode_ref, "mentions")
    intelligence = _identified_json_from_source(intelligence_source, podcast_id, episode_ref, "intelligence")
    mapping = _identified_json_from_source(mapping_source, podcast_id, episode_ref, "industry mapping")
    boundary = _identified_json_from_source(boundary_source, podcast_id, episode_ref, "external boundary")
    _require_exact_status(intelligence, "report_status", "final", "intelligence")
    _require_exact_status(mapping, "mapping_status", "final", "industry mapping")
    _require_exact_status(boundary, "boundary_status", "final", "external boundary")
    for source, role in ((mentions_source, "mentions"), (intelligence_source, "intelligence"), (mapping_source, "industry mapping"), (boundary_source, "external boundary")):
        _assert_safe_source_bytes(source, role)
    source_artifacts = snapshot.source_artifacts
    if include_fixture_verification:
        _assert_safe_source_bytes(sources_by_role["fixture"], "fixture")
    stock_lens: dict[str, Any] | None = None
    if normalized_stock_query is not None:
        stock_source = sources_by_role["stock_lens"]
        stock_lens = _json_from_source(stock_source, "stock lens")
        if stock_lens.get("podcast_id") != podcast_id or stock_lens.get("stock_query") != normalized_stock_query:
            raise VerifiedResearchReportInputError("stock lens identity is invalid")
        _assert_safe_source_bytes(stock_source, "stock lens")

    source_digest = _source_digest(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        stock_query=normalized_stock_query,
        include_fixture_verification=include_fixture_verification,
        sources=source_artifacts,
    )
    report_version = f"{REPORT_VERSION_PREFIX}-{source_digest}"
    report_payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_version": report_version,
        "source_digest": source_digest,
        "assembly_options": {
            "stock_query": normalized_stock_query,
            "include_fixture_verification": include_fixture_verification,
            "verification_scope": "local_artifact_and_fixture",
        },
        "episode_identity": {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": _safe_text(title),
            "completion_status": "completed",
        },
        "reviewed_executive_summary": {
            "classification": "reviewed_narrative",
            "llm_generated": True,
            "review_status": "passed",
            "content": _safe_summary(semantic_summary),
        },
        "podcast_evidence_timeline": _verified_timeline(intelligence),
        "explicit_mentions": _explicit_mentions(mentions),
        "industry_macro_clues": _safe_clues(intelligence),
        "deterministic_inference": _safe_mapping_inference(mapping),
        "external_verification_boundary": _safe_boundary(boundary),
        "stock_query_appendix": _stock_appendix(normalized_stock_query, stock_lens),
        "limitations": [
            "Podcast evidence is verified only where timestamp and segment provenance are present.",
            "Reviewed narrative is LLM-generated and remains distinct from verified podcast facts.",
            "External verification is limited to local artifact and fixture status; no live market or news source was used.",
        ],
        "not_investment_advice": True,
    }
    return VerifiedResearchReportAssembly(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        stock_query=normalized_stock_query,
        include_fixture_verification=include_fixture_verification,
        source_digest=source_digest,
        report_version=report_version,
        report_payload=report_payload,
        report_markdown=_render_markdown(report_payload),
        source_artifacts=source_artifacts,
        lineage_manifest=lineage_manifest,
    )

def publish_verified_research_report_bundle(
    assembly: VerifiedResearchReportAssembly,
) -> VerifiedResearchReportBundle:
    """Atomically publish an assembled bundle, reuse identical content, or fail closed."""

    paths = storage.latest_episode_verified_research_report_paths(
        assembly.podcast_id, assembly.episode_ref, assembly.source_digest
    )
    # The claim covers comparison through the final validated return.  A process
    # cannot observe a matching final bundle then return it after another workflow
    # writer has replaced one of its files.
    claim_path = paths.bundle_dir.parent / f".{paths.bundle_dir.name}.publish.claim"
    try:
        with exclusive_artifact_claim(claim_path):
            _verify_assembly_sources(assembly)
            if paths.bundle_dir.exists():
                if _existing_bundle_matches(paths, assembly):
                    return _validated_bundle_return(paths, assembly, reused=True)
                raise VerifiedResearchReportInputError(
                    "existing verified report bundle conflicts with source digest"
                )

            # Keep staging paths below Windows MAX_PATH even when test/workspace roots are long.
            staging_dir = paths.bundle_dir.parent / f".stage-{uuid.uuid4().hex[:12]}"
            try:
                staging_dir.mkdir(parents=True, exist_ok=False)
                report_json_path = staging_dir / "report.json"
                report_markdown_path = staging_dir / "report.md"
                manifest_path = staging_dir / "manifest.json"
                report_json_path.write_bytes(_canonical_report_json_bytes(assembly))
                report_markdown_path.write_bytes(assembly.report_markdown.encode("utf-8"))
                manifest = _manifest_payload(assembly, report_json_path, report_markdown_path)
                manifest_path.write_bytes(
                    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
                )
                _verify_staged_bundle(staging_dir, assembly)
                _verify_assembly_sources(assembly)
                try:
                    staging_dir.replace(paths.bundle_dir)
                except OSError as exc:
                    if not _destination_exists_error(exc) or not paths.bundle_dir.exists():
                        raise
                    _remove_owned_staging_dir(staging_dir)
                    if _existing_bundle_matches(paths, assembly):
                        return _validated_bundle_return(paths, assembly, reused=True)
                    raise VerifiedResearchReportInputError(
                        "destination verified report bundle conflicts after publish race"
                    ) from exc
            except OSError as exc:
                _remove_owned_staging_dir(staging_dir)
                raise VerifiedResearchReportInputError(
                    f"verified report bundle publish failed: {type(exc).__name__}"
                ) from exc
            except Exception:
                _remove_owned_staging_dir(staging_dir)
                raise
            return _validated_bundle_return(paths, assembly, reused=False)
    except TimeoutError as exc:
        raise VerifiedResearchReportInputError("verified report bundle claim timed out") from exc


def _validated_bundle_return(
    paths: storage.LatestEpisodeVerifiedResearchReportPaths,
    assembly: VerifiedResearchReportAssembly,
    *,
    reused: bool,
) -> VerifiedResearchReportBundle:
    """Re-read bundle and sources after comparison/rename before a success result."""

    # Recheck in alternating order to close both normal reuse and destination-race
    # windows.  The filesystem claim serializes workflow writers; these reads also
    # fail closed for out-of-band mutation.
    _verify_assembly_sources(assembly)
    if not _existing_bundle_matches(paths, assembly):
        raise VerifiedResearchReportInputError("verified report bundle changed before return")
    _verify_assembly_sources(assembly)
    if not _existing_bundle_matches(paths, assembly):
        raise VerifiedResearchReportInputError("verified report bundle changed before return")
    return _bundle_from_paths(paths, assembly, reused=reused)


def inspect_semantic_review(
    podcast_id: str,
    episode_ref: str,
    *,
    semantic_summary_path: Path,
    review_reports_dir: Path | None = None,
    semantic_summary_bytes: bytes | None = None,
) -> SemanticReviewInspection:
    """Compatibility wrapper around the neutral semantic-review artifact inspector."""

    if review_reports_dir is None:
        # Kept local to avoid making the neutral artifact domain depend on the writer.
        from .semantic_summary_smoke_review import REPORTS_DIR

        review_reports_dir = REPORTS_DIR
    return _inspect_semantic_review_artifact(
        podcast_id,
        episode_ref,
        semantic_summary_path=semantic_summary_path,
        review_reports_dir=review_reports_dir,
        semantic_summary_bytes=semantic_summary_bytes,
    )


def _json_from_source(source: VerifiedResearchSourceArtifact, role: str) -> dict[str, Any]:
    try:
        payload = json.loads(source.raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifiedResearchReportInputError(
            f"verified report {role} artifact is unreadable"
        ) from exc
    if not isinstance(payload, dict):
        raise VerifiedResearchReportInputError(f"verified report {role} artifact is invalid")
    return payload


def _text_from_source(source: VerifiedResearchSourceArtifact, role: str) -> str:
    try:
        text = source.raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerifiedResearchReportInputError(
            f"verified report {role} artifact is unreadable"
        ) from exc
    if not text.strip():
        raise VerifiedResearchReportInputError(f"verified report {role} artifact is empty")
    return text


def _identified_json_from_source(
    source: VerifiedResearchSourceArtifact,
    podcast_id: str,
    episode_ref: str,
    role: str,
) -> dict[str, Any]:
    payload = _json_from_source(source, role)
    _identity_title(payload, podcast_id, episode_ref, role, title_required=False)
    return payload


def _read_identified_json(
    path: Path, podcast_id: str, episode_ref: str, role: str
) -> dict[str, Any]:
    return _identified_json_from_source(_source_artifact(role, path, True), podcast_id, episode_ref, role)


def _read_json(path: Path, role: str) -> dict[str, Any]:
    return _json_from_source(_source_artifact(role, path, True), role)


def _read_text(path: Path, role: str) -> str:
    return _text_from_source(_source_artifact(role, path, True), role)


def _assert_safe_source_bytes(source: VerifiedResearchSourceArtifact, role: str) -> None:
    """Reject an unsafe immutable source snapshot rather than a scrubbed report."""

    try:
        text = source.raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerifiedResearchReportInputError(
            f"verified report {role} artifact is unreadable"
        ) from exc
    safety_text = text
    if role == "semantic review":
        # The deterministic check identifier is metadata, not a captured stack trace.
        safety_text = safety_text.replace(
            '"name": "traceback_leak"', '"name": "stack_trace_leak"'
        )
    if role == "stock lens":
        # Production lens policy wording (for example, "Do not produce target
        # prices") is declarative metadata, not advice.  Scan every actual report
        # field while excluding only that fixed policy guidance subtree.
        safety_text = _stock_lens_safety_text(safety_text)
    safety_text = strip_safety_disclaimers(safety_text)
    if (
        contains_sensitive_text(safety_text, reject_any_uri=False)
        or _matched_source_advice_guard(safety_text) is not None
    ):
        raise VerifiedResearchReportInputError(
            f"verified report {role} artifact violates safety boundary"
        )


def _matched_source_advice_guard(text: str) -> str | None:
    """Scan source text values without treating JSON syntax as quoted evidence."""

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return matched_investment_advice_guard(text)
    return _matched_json_value_advice_guard(payload)


def _matched_json_value_advice_guard(value: Any) -> str | None:
    if isinstance(value, str):
        return matched_investment_advice_guard(value)
    if isinstance(value, list):
        for item in value:
            matched_guard = _matched_json_value_advice_guard(item)
            if matched_guard is not None:
                return matched_guard
    if isinstance(value, dict):
        for item in value.values():
            matched_guard = _matched_json_value_advice_guard(item)
            if matched_guard is not None:
                return matched_guard
    return None


def _stock_lens_safety_text(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if not isinstance(payload, dict):
        return text
    lens = payload.get("gooaye_lens")
    if not isinstance(lens, dict):
        return text
    sanitized = dict(payload)
    safe_lens = dict(lens)
    safe_lens.pop("safety_rules", None)
    dimensions = safe_lens.get("dimensions")
    if isinstance(dimensions, list):
        safe_lens["dimensions"] = [
            {key: value for key, value in item.items() if key != "output_guidance"}
            if isinstance(item, dict)
            else item
            for item in dimensions
        ]
    sanitized["gooaye_lens"] = safe_lens
    return json.dumps(sanitized, ensure_ascii=False)


def _assert_safe_source_text(path: Path, role: str) -> None:
    """Compatibility helper for callers outside the assembler."""

    _assert_safe_source_bytes(_source_artifact(role, path, True), role)


def _identity_title(
    payload: dict[str, Any], podcast_id: str, episode_ref: str, role: str, *, title_required: bool = True
) -> str:
    if payload.get("podcast_id") != podcast_id or payload.get("episode_ref") != episode_ref:
        raise VerifiedResearchReportInputError(f"verified report {role} identity is invalid")
    title = payload.get("title")
    if title_required:
        if not isinstance(title, str) or not title.strip():
            raise VerifiedResearchReportInputError(f"verified report {role} title is invalid")
        return title
    return title if isinstance(title, str) else ""


def _validate_transcript_snapshot(payload: dict[str, Any]) -> None:
    """Keep the valid transcript contract without rereading the transcript JSON."""

    segments = payload.get("segments")
    if (
        not isinstance(segments, list)
        or not segments
        or payload.get("completed") is False
        or payload.get("segment_count") != len(segments)
    ):
        raise VerifiedResearchReportInputError("verified report transcript artifact contract is invalid")
    previous_start = -1.0
    for segment in segments:
        if not isinstance(segment, dict):
            raise VerifiedResearchReportInputError("verified report transcript artifact contract is invalid")
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise VerifiedResearchReportInputError(
                "verified report transcript artifact contract is invalid"
            ) from exc
        if start < 0 or end < start or start < previous_start:
            raise VerifiedResearchReportInputError("verified report transcript artifact contract is invalid")
        previous_start = start


def _require_exact_status(
    payload: dict[str, Any], key: str, expected: str, role: str
) -> None:
    if payload.get(key) != expected:
        raise VerifiedResearchReportInputError(
            f"verified report {role} status is not {expected}"
        )


def _core_source_root(path: Path) -> Path:
    """Return the Core-owned storage root containing an expected source path."""

    from .external_data_verification import DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH
    from .semantic_summary_smoke_review import REPORTS_DIR as semantic_review_reports_dir

    roots = (
        storage.TRANSCRIPTS_DIR,
        storage.SUMMARIES_DIR,
        storage.MENTIONS_DIR,
        storage.REPORTS_DIR,
        storage.MAPPINGS_DIR,
        storage.EXTERNAL_DIR,
        storage.STOCK_LENS_DIR,
        storage.CORPUS_DIR,
        semantic_review_reports_dir,
        Path(DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH).parent,
    )
    candidate = Path(path).absolute()
    for root in roots:
        checked_root = Path(root).absolute()
        try:
            candidate.relative_to(checked_root)
        except ValueError:
            continue
        return checked_root
    # This is fail-closed at secure_read_bytes's lexical containment check.  It
    # cannot grant a persisted or out-of-policy source an ambient storage root.
    return storage.CORPUS_DIR


def _source_artifact(
    role: str, path: Path, identity_valid: bool
) -> VerifiedResearchSourceArtifact:
    """Capture a report source through the Core-owned snapshot boundary."""

    raw = secure_read_bytes(_core_source_root(path), path, max_bytes=64 * 1024 * 1024)
    if raw is None:
        raise VerifiedResearchReportInputError(
            f"verified report {role} artifact is unreadable"
        )
    return _source_artifact_from_bytes(role, path, raw, identity_valid)


def _source_artifact_from_bytes(
    role: str, path: Path, raw: bytes, identity_valid: bool
) -> VerifiedResearchSourceArtifact:
    return VerifiedResearchSourceArtifact(
        role=role,
        path=path,
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        identity_valid=identity_valid,
        raw_bytes=raw,
    )


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _source_digest(
    *,
    podcast_id: str,
    episode_ref: str,
    stock_query: str | None,
    include_fixture_verification: bool,
    sources: list[VerifiedResearchSourceArtifact],
) -> str:
    canonical = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "options": {
            "stock_query": stock_query,
            "include_fixture_verification": include_fixture_verification,
            "verification_scope": "local_artifact_and_fixture",
        },
        "sources": [
            {
                "role": source.role,
                "path": _canonical_source_path(source.path),
                "sha256": source.sha256,
                "size_bytes": source.size_bytes,
            }
            for source in sources
        ],
    }
    return hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _verified_timeline(intelligence: dict[str, Any]) -> list[dict[str, Any]]:
    timeline = intelligence.get("timeline")
    if not isinstance(timeline, list):
        raise VerifiedResearchReportInputError("intelligence timeline is invalid")
    verified: list[dict[str, Any]] = []
    for window in timeline:
        if not isinstance(window, dict):
            continue
        evidence_items = window.get("evidence")
        if not isinstance(evidence_items, list):
            continue
        for evidence in evidence_items:
            if not isinstance(evidence, dict):
                continue
            timestamp = evidence.get("timestamp")
            segment_id = evidence.get("segment_id")
            if not isinstance(timestamp, str) or not _TIMESTAMP_PATTERN.fullmatch(timestamp):
                raise VerifiedResearchReportInputError("verified podcast evidence lacks timestamp provenance")
            if segment_id is None or isinstance(segment_id, (dict, list)):
                raise VerifiedResearchReportInputError("verified podcast evidence lacks segment provenance")
            evidence_text = _safe_text(
                str(evidence.get("statement", evidence.get("text", "")))
            )
            if not evidence_text or evidence_text == OMITTED_VALUE:
                continue
            verified.append(
                {
                    "classification": "verified_podcast_fact",
                    "timestamp": timestamp,
                    "segment_id": segment_id,
                    "start_seconds": evidence.get("start"),
                    "end_seconds": evidence.get("end"),
                    "evidence": evidence_text,
                }
            )
    return verified


def _explicit_mentions(mentions: dict[str, Any]) -> list[dict[str, Any]]:
    raw_mentions = mentions.get("mentions")
    if not isinstance(raw_mentions, list):
        return []
    results: list[dict[str, Any]] = []
    for mention in raw_mentions:
        if not isinstance(mention, dict):
            continue
        evidence = mention.get("evidence")
        provenance: list[dict[str, Any]] = []
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, dict):
                    continue
                timestamp = item.get("timestamp")
                segment_id = item.get("segment_id")
                if isinstance(timestamp, str) and _TIMESTAMP_PATTERN.fullmatch(timestamp) and segment_id is not None:
                    provenance.append({"timestamp": timestamp, "segment_id": segment_id})
        if not provenance:
            continue
        text = _safe_text(str(mention.get("text", "")))
        if text == "value omitted by safety boundary" or not text:
            continue
        results.append(
            {
                "classification": "verified_podcast_fact",
                "mention_type": _safe_text(str(mention.get("type", "unknown"))),
                "text": text,
                "count": mention.get("count") if isinstance(mention.get("count"), int) else 0,
                "provenance": provenance,
            }
        )
    return results


def _safe_clues(intelligence: dict[str, Any]) -> dict[str, list[str]]:
    def collect(key: str) -> list[str]:
        items = intelligence.get(key)
        if not isinstance(items, list):
            return []
        values: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            value = _safe_text(str(item.get("text", "")))
            if value and value != "value omitted by safety boundary":
                values.append(value)
        return values

    return {"industry": collect("industry_clues"), "macro": collect("macro_variables")}


def _safe_mapping_inference(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = mapping.get("stock_candidates")
    if not isinstance(candidates, list):
        return []
    return [
        {
            "classification": "deterministic_inference",
            "company_name": _safe_text(str(candidate.get("company_name", ""))),
            "relation_type": _safe_text(str(candidate.get("relation_type", ""))),
            "verification_status": _safe_text(str(candidate.get("verification_status", ""))),
        }
        for candidate in candidates
        if isinstance(candidate, dict)
    ]


def _safe_boundary(boundary: dict[str, Any]) -> dict[str, Any]:
    candidates = boundary.get("candidate_boundaries")
    statuses: list[dict[str, Any]] = []
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            statuses.append(
                {
                    "classification": "external_status",
                    "company_name": _safe_text(str(candidate.get("company_name", ""))),
                    "external_verification_status": _safe_text(str(candidate.get("external_verification_status", "not_requested"))),
                    "source_status": _safe_text(str(candidate.get("source_status", "not_fetched"))),
                    "data_date": candidate.get("data_date") if candidate.get("data_date") is None else _safe_text(str(candidate.get("data_date"))),
                }
            )
    return {"verification_scope": "local_artifact_and_fixture_only", "candidates": statuses}


def _stock_appendix(stock_query: str | None, stock_lens: dict[str, Any] | None) -> dict[str, Any] | None:
    if stock_query is None or stock_lens is None:
        return None
    direct = _stock_direct_evidence(stock_lens.get("direct_podcast_evidence"))
    leads = _stock_inferred_leads(stock_lens.get("inferred_research_leads"))
    details = _stock_verification_details(stock_lens.get("external_verification_needs"))
    return {
        "scope": "podcast_wide",
        "stock_query": _safe_text(stock_query),
        "report_status": _safe_text(str(stock_lens.get("report_status", "unknown"))),
        "note": "This appendix aggregates podcast-wide local artifacts and is not a selected-episode direct fact.",
        "direct_podcast_evidence": direct,
        "inferred_research_leads": leads,
        "verification_details": details,
    }


def _stock_direct_evidence(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    results: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        provenance: list[dict[str, Any]] = []
        for evidence in item.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            timestamp = evidence.get("timestamp")
            segment_id = evidence.get("segment_id")
            text = _safe_text(str(evidence.get("statement", evidence.get("text", ""))))
            if (
                isinstance(timestamp, str)
                and _TIMESTAMP_PATTERN.fullmatch(timestamp)
                and segment_id is not None
                and text != OMITTED_VALUE
                and text
            ):
                provenance.append(
                    {"timestamp": timestamp, "segment_id": segment_id, "evidence": text}
                )
        if not provenance:
            continue
        results.append(
            {
                "classification": "verified_podcast_fact",
                "company_name": _safe_text(str(item.get("company_name", ""))),
                "tickers": _safe_strings(item.get("tickers")),
                "episode_ref": _safe_text(str(item.get("episode_ref", ""))),
                "relation": _safe_text(str(item.get("relation", ""))),
                "relation_type": _safe_text(str(item.get("relation_type", ""))),
                "evidence_status": _safe_text(str(item.get("evidence_status", "podcast_explicit"))),
                "verification_status": _safe_text(str(item.get("verification_status", "podcast_evidence"))),
                "external_verification": _safe_external_verification(item.get("external_boundary")),
                "provenance": provenance,
            }
        )
    return results


def _stock_inferred_leads(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    results: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "classification": "deterministic_inference",
                "company_name": _safe_text(str(item.get("company_name", ""))),
                "tickers": _safe_strings(item.get("tickers")),
                "episode_ref": _safe_text(str(item.get("episode_ref", ""))),
                "relation": _safe_text(str(item.get("relation", ""))),
                "relation_type": _safe_text(str(item.get("relation_type", ""))),
                "evidence_status": _safe_text(str(item.get("evidence_status", "inferred_from_industry"))),
                "verification_status": _safe_text(str(item.get("verification_status", "needs_verification"))),
                "external_verification": _safe_external_verification(item.get("external_boundary")),
            }
        )
    return results


def _stock_verification_details(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    results: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "classification": "external_status",
                "company_name": _safe_text(str(item.get("company_name", ""))),
                "external_verification_status": _safe_text(str(item.get("external_verification_status", "not_requested"))),
                "source_status": _safe_text(str(item.get("source_status", "not_fetched"))),
                "data_date": None if item.get("data_date") is None else _safe_text(str(item.get("data_date"))),
                "required_external_checks": _safe_required_external_checks(item.get("required_external_checks")),
            }
        )
    return results


def _safe_external_verification(value: object) -> dict[str, Any]:
    payload = value if isinstance(value, dict) else {}
    return {
        "external_verification_status": _safe_text(
            str(payload.get("external_verification_status", "not_requested"))
        ),
        "source_status": _safe_text(str(payload.get("source_status", "not_fetched"))),
        "data_date": (
            None if payload.get("data_date") is None else _safe_text(str(payload.get("data_date")))
        ),
        "required_external_checks": _safe_required_external_checks(
            payload.get("required_external_checks")
        ),
    }


def _safe_required_external_checks(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    checks: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        data_type = _safe_text(str(item.get("data_type", "")))
        label = _safe_text(str(item.get("label", "")))
        if data_type == OMITTED_VALUE and label == OMITTED_VALUE:
            continue
        checks.append(
            {
                "data_type": "" if data_type == OMITTED_VALUE else data_type,
                "label": "" if label == OMITTED_VALUE else label,
                "requires_source_status": item.get("requires_source_status") is True,
                "requires_data_date": item.get("requires_data_date") is True,
            }
        )
    return checks


def _render_external_check_labels(checks: list[dict[str, Any]]) -> str:
    labels = [
        check["label"] or check["data_type"]
        for check in checks
        if check.get("label") or check.get("data_type")
    ]
    return ", ".join(labels) or "none"


def _safe_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in (_safe_text(str(candidate)) for candidate in value)
        if item and item != OMITTED_VALUE
    ]


def _safe_summary(summary: str) -> str:
    accepted = [
        _safe_text(line.strip())
        for line in summary.splitlines()
        if line.strip() and not line.startswith("#")
    ]
    accepted = [line for line in accepted if line != "value omitted by safety boundary"]
    return "\n".join(accepted[:80])


def _safe_text(value: str) -> str:
    return safe_text(value, maximum_length=4000)


def _render_markdown(payload: dict[str, Any]) -> str:
    identity = payload["episode_identity"]
    lines = [
        "# Verified Research Report",
        "",
        "## Episode Identity And Completion Status",
        "",
        f"- Podcast: {identity['podcast_id']}",
        f"- Episode: {identity['episode_ref']}",
        f"- Title: {identity['title']}",
        f"- Completion status: {identity['completion_status']}",
        "",
        "## Reviewed Executive Summary",
        "",
        "LLM-generated reviewed narrative; deterministic review status: passed.",
        "",
        payload["reviewed_executive_summary"]["content"] or "No safe reviewed narrative was available.",
        "",
        "## Podcast Evidence Timeline",
        "",
    ]
    for item in payload["podcast_evidence_timeline"]:
        lines.append(
            f"- [{item['classification']}] {item['timestamp']} (segment {item['segment_id']}): {item['evidence']}"
        )
    if not payload["podcast_evidence_timeline"]:
        lines.append("- No verified podcast facts were emitted.")
    lines.extend(["", "## Explicit Mentions", ""])
    for item in payload["explicit_mentions"]:
        timestamps = ", ".join(evidence["timestamp"] for evidence in item["provenance"])
        lines.append(f"- {item['text']}: {timestamps}")
    if not payload["explicit_mentions"]:
        lines.append("- No verified explicit mentions were emitted.")
    lines.extend(["", "## Industry And Macro Clues", ""])
    for kind, values in payload["industry_macro_clues"].items():
        lines.append(f"- {kind}: {', '.join(values) if values else 'none'}")
    lines.extend(["", "## Deterministic Inference", ""])
    for item in payload["deterministic_inference"]:
        lines.append(f"- {item['company_name']}: {item['relation_type']} / {item['verification_status']}")
    if not payload["deterministic_inference"]:
        lines.append("- No deterministic inference entries.")
    lines.extend(["", "## External Verification Boundary And Local Fixture Status", ""])
    lines.append("- Scope: local artifact and fixture status only; no live market or news source.")
    for item in payload["external_verification_boundary"]["candidates"]:
        lines.append(f"- {item['company_name']}: {item['external_verification_status']} / {item['source_status']}")
    if payload["stock_query_appendix"] is not None:
        appendix = payload["stock_query_appendix"]
        lines.extend(
            [
                "",
                "## Stock Query Appendix",
                "",
                f"- Scope: {appendix['scope']}",
                f"- Query: {appendix['stock_query']}",
                f"- Status: {appendix['report_status']}",
                f"- {appendix['note']}",
                "- Direct podcast evidence:",
            ]
        )
        if appendix["direct_podcast_evidence"]:
            for item in appendix["direct_podcast_evidence"]:
                for evidence in item["provenance"]:
                    lines.append(
                        f"  - [{item['classification']}] {item['company_name']} "
                        f"{evidence['timestamp']} (segment {evidence['segment_id']}): {evidence['evidence']} "
                        f"/ checks={_render_external_check_labels(item['external_verification']['required_external_checks'])}"
                    )
        else:
            lines.append("  - none")
        lines.append("- Inferred research leads:")
        if appendix["inferred_research_leads"]:
            for item in appendix["inferred_research_leads"]:
                lines.append(
                    f"  - [{item['classification']}] {item['company_name']}: "
                    f"{item['relation_type']} / {item['verification_status']} / "
                    f"checks={_render_external_check_labels(item['external_verification']['required_external_checks'])}"
                )
        else:
            lines.append("  - none")
        lines.append("- Verification details:")
        if appendix["verification_details"]:
            for item in appendix["verification_details"]:
                checks = _render_external_check_labels(item["required_external_checks"])
                lines.append(
                    f"  - [{item['classification']}] {item['company_name']}: "
                    f"{item['external_verification_status']} / {item['source_status']} / checks={checks}"
                )
        else:
            lines.append("  - none")
    lines.extend(["", "## Limitations, Warnings, And Provenance", ""])
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.extend(["- This report is not investment advice.", ""])
    return "\n".join(lines)


def _manifest_payload(
    assembly: VerifiedResearchReportAssembly, report_json_path: Path, report_markdown_path: Path
) -> dict[str, Any]:
    return _manifest_payload_from_metadata(
        assembly,
        report_json_metadata=_file_metadata(report_json_path),
        report_markdown_metadata=_file_metadata(report_markdown_path),
    )


def _expected_manifest_payload(assembly: VerifiedResearchReportAssembly) -> dict[str, Any]:
    return _manifest_payload_from_metadata(
        assembly,
        report_json_metadata=_bytes_metadata(_canonical_report_json_bytes(assembly)),
        report_markdown_metadata=_bytes_metadata(assembly.report_markdown.encode("utf-8")),
    )


def _manifest_payload_from_metadata(
    assembly: VerifiedResearchReportAssembly,
    *,
    report_json_metadata: dict[str, Any],
    report_markdown_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_version": assembly.report_version,
        "source_digest": assembly.source_digest,
        "episode_identity": {"podcast_id": assembly.podcast_id, "episode_ref": assembly.episode_ref},
        "assembly_options": {
            "stock_query": assembly.stock_query,
            "include_fixture_verification": assembly.include_fixture_verification,
            "verification_scope": "local_artifact_and_fixture",
        },
        "verification_scope": "podcast timestamp and segment evidence, local artifact provenance, semantic review, and local fixture status only",
        "quality_gates": {
            "semantic_review_status": "passed",
            "semantic_summary_sha256": next(
                source.sha256 for source in assembly.source_artifacts if source.role == "semantic_summary"
            ),
            "timestamp_provenance": "validated",
            "lineage_quality_gate": LINEAGE_QUALITY_GATE,
            "lineage_schema_version": LINEAGE_SCHEMA_VERSION,
            "not_investment_advice": True,
        },
        "lineage": assembly.lineage_manifest,
        "source_artifacts": [
            {"role": source.role, "path": _safe_path(source.path), "sha256": source.sha256, "size_bytes": source.size_bytes, "identity_valid": source.identity_valid}
            for source in assembly.source_artifacts
        ],
        "bundle_files": {
            "report.json": report_json_metadata,
            "report.md": report_markdown_metadata,
        },
    }


def _canonical_report_json_bytes(assembly: VerifiedResearchReportAssembly) -> bytes:
    return json.dumps(
        assembly.report_payload, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8")


def _bytes_metadata(raw: bytes) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def _file_metadata(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def _verify_assembly_sources(assembly: VerifiedResearchReportAssembly) -> None:
    """Require every final success to still match its assembled immutable bytes."""

    for source in assembly.source_artifacts:
        try:
            current_raw = source.path.read_bytes()
        except OSError as exc:
            raise VerifiedResearchReportInputError(
                "verified report source artifact changed during assembly"
            ) from exc
        if (
            current_raw != source.raw_bytes
            or hashlib.sha256(current_raw).hexdigest() != source.sha256
            or len(current_raw) != source.size_bytes
        ):
            raise VerifiedResearchReportInputError(
                "verified report source artifact changed during assembly"
            )
    artifacts = assembly.lineage_manifest.get("artifacts")
    summary = artifacts.get("semantic_summary") if isinstance(artifacts, dict) else None
    summary_options = summary.get("options") if isinstance(summary, dict) else None
    validate_current_verified_research_lineage(
        assembly.podcast_id,
        assembly.episode_ref,
        stock_query=assembly.stock_query,
        include_fixture_verification=assembly.include_fixture_verification,
        summary_options=summary_options,
        require_generation_proofs=True,
    )


def _verify_staged_bundle(staging_dir: Path, assembly: VerifiedResearchReportAssembly) -> None:
    paths = storage.LatestEpisodeVerifiedResearchReportPaths(
        bundle_dir=staging_dir,
        report_json_path=staging_dir / "report.json",
        report_markdown_path=staging_dir / "report.md",
        manifest_path=staging_dir / "manifest.json",
        checkpoint_path=Path("unused"),
    )
    if not _bundle_matches_expected(paths, assembly):
        raise VerifiedResearchReportInputError("staged report bundle validation failed")


def _existing_bundle_matches(
    paths: storage.LatestEpisodeVerifiedResearchReportPaths,
    assembly: VerifiedResearchReportAssembly,
) -> bool:
    """Reuse only a byte-for-byte canonical, exactly three-file final bundle."""

    return _bundle_matches_expected(paths, assembly)


def _bundle_matches_expected(
    paths: storage.LatestEpisodeVerifiedResearchReportPaths,
    assembly: VerifiedResearchReportAssembly,
) -> bool:
    expected_names = {"report.json", "report.md", "manifest.json"}
    try:
        entries = list(paths.bundle_dir.iterdir())
        if {entry.name for entry in entries} != expected_names or not all(entry.is_file() for entry in entries):
            return False
        report_bytes = paths.report_json_path.read_bytes()
        markdown_bytes = paths.report_markdown_path.read_bytes()
        manifest_bytes = paths.manifest_path.read_bytes()
        if report_bytes != _canonical_report_json_bytes(assembly):
            return False
        if markdown_bytes != assembly.report_markdown.encode("utf-8"):
            return False
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        expected_manifest = _expected_manifest_payload(assembly)
        if manifest != expected_manifest and not _legacy_source_paths_match(
            manifest, expected_manifest, assembly
        ):
            return False
        # A legacy path representation may be equivalent, but the persisted
        # manifest still must be its own canonical byte encoding.  Reuse never
        # rewrites that historical identity.
        return manifest_bytes == json.dumps(
            manifest, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def _legacy_source_paths_match(
    manifest: object,
    expected_manifest: dict[str, Any],
    assembly: VerifiedResearchReportAssembly,
) -> bool:
    """Accept only Core-derived safe or canonical representations of current sources.

    Persisted paths remain opaque comparison metadata: this function never
    parses, resolves, opens, or otherwise uses their text as a path authority.
    A matching legacy manifest is not rewritten during reuse.
    """

    if not isinstance(manifest, dict):
        return False
    expected_sources = expected_manifest.get("source_artifacts")
    actual_sources = manifest.get("source_artifacts")
    if (
        not isinstance(expected_sources, list)
        or not isinstance(actual_sources, list)
        or not (
            len(actual_sources)
            == len(expected_sources)
            == len(assembly.source_artifacts)
        )
    ):
        return False
    if (
        {key: value for key, value in manifest.items() if key != "source_artifacts"}
        != {key: value for key, value in expected_manifest.items() if key != "source_artifacts"}
    ):
        return False
    for actual, expected, source in zip(
        actual_sources, expected_sources, assembly.source_artifacts, strict=True
    ):
        if not isinstance(actual, dict) or not isinstance(expected, dict):
            return False
        if (
            {key: value for key, value in actual.items() if key != "path"}
            != {key: value for key, value in expected.items() if key != "path"}
        ):
            return False
        raw_path = actual.get("path")
        if not isinstance(raw_path, str):
            return False
        try:
            accepted_paths = {
                _safe_path(source.path),
                _canonical_source_path(source.path),
            }
        except OSError:
            return False
        if raw_path not in accepted_paths:
            return False
    return True


def _bundle_from_paths(
    paths: storage.LatestEpisodeVerifiedResearchReportPaths,
    assembly: VerifiedResearchReportAssembly,
    *,
    reused: bool,
) -> VerifiedResearchReportBundle:
    return VerifiedResearchReportBundle(
        bundle_dir=paths.bundle_dir,
        report_json_path=paths.report_json_path,
        report_markdown_path=paths.report_markdown_path,
        manifest_path=paths.manifest_path,
        source_digest=assembly.source_digest,
        report_version=assembly.report_version,
        reused=reused,
    )


def _destination_exists_error(exc: OSError) -> bool:
    return exc.errno == errno.EEXIST or getattr(exc, "winerror", None) == 183 or isinstance(exc, FileExistsError)


def _remove_owned_staging_dir(path: Path) -> None:
    if not path.name.startswith(".stage-") or not path.exists():
        return
    try:
        shutil.rmtree(path)
    except OSError:
        pass


def _normalize_stock_query(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise VerifiedResearchReportInputError("stock_query is invalid")
    normalized = value.strip()
    if not normalized or len(normalized) > 128 or _safe_text(normalized) == "value omitted by safety boundary":
        raise VerifiedResearchReportInputError("stock_query is invalid")
    return normalized


def _validate_identifier(value: str, field: str, *, lower_slug: bool = False) -> None:
    if not isinstance(value, str):
        raise VerifiedResearchReportInputError(f"{field} is invalid")
    if lower_slug:
        if re.fullmatch(r"[a-z0-9][a-z0-9-]*", value) is None:
            raise VerifiedResearchReportInputError(f"{field} is invalid")
        return
    if not storage.is_safe_episode_ref(value, max_length=128):
        raise VerifiedResearchReportInputError(f"{field} is invalid")


def _canonical_source_path(path: Path) -> str:
    """Normalize source provenance before binding it into the immutable digest."""

    return path.resolve(strict=False).as_posix()


def _safe_path(path: Path) -> str:
    """Return a safe local path without misclassifying a Windows drive as a URI."""

    value = path.as_posix()
    lowered = value.lower()
    if (
        not value
        or "?" in value
        or "#" in value
        or _SECRET_PATTERN.search(value)
        or any(fragment in lowered for fragment in _FORBIDDEN_TEXT)
        or any(ord(character) < 32 for character in value)
    ):
        return "value omitted by safety boundary"
    if re.fullmatch(r"[A-Za-z]:/.*", value) or value.startswith("/"):
        return value
    return value if _safe_text(value) == value else "value omitted by safety boundary"
