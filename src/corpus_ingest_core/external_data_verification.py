from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from . import storage
from .canonical_transcript import current_canonical_transcript_identity
from .episode_claim import episode_writer_claimed
from .errors import (
    ExternalDataVerificationFailedError,
    ExternalDataVerificationInputError,
)
from .models import ExternalDataVerificationAsset
from .storage import external_data_boundary_asset_paths

VERIFICATION_MODE = "fixture-external-data-v1"
SUPPORTED_BOUNDARY_MODE = "external-data-boundary-v1"
SUPPORTED_PROVIDER = "fixture"
DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH = Path("config/external_market_data_fixtures.yaml")
PREVERIFICATION_BOUNDARIES_DIR = storage.CORPUS_DIR


@episode_writer_claimed
def verify_external_data_boundary(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    provider: str = SUPPORTED_PROVIDER,
    fixture_path: Path = DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
) -> ExternalDataVerificationAsset:
    """Apply local fixture external data to an existing Phase 6D boundary artifact."""

    fixture_path = Path(fixture_path)
    if provider != SUPPORTED_PROVIDER:
        raise ExternalDataVerificationInputError(f"unsupported external data provider: {provider}")

    transcript_identity = current_canonical_transcript_identity(podcast_id, episode_ref)
    paths = (
        None
        if transcript_identity is None
        else external_data_boundary_asset_paths(podcast_id, episode_ref, transcript_identity.title)
    )
    if paths is None or not paths.json_path.exists():
        raise ExternalDataVerificationInputError(f"找不到 external boundary：{podcast_id}/{episode_ref}")

    try:
        boundary_input_raw = paths.json_path.read_bytes()
    except OSError as exc:
        raise ExternalDataVerificationInputError("external boundary is unreadable") from exc
    payload = _load_boundary_payload(paths.json_path)
    _validate_boundary_identity(payload, podcast_id, episode_ref)
    boundary_mode = _required_text(payload, "boundary_mode")
    if boundary_mode != SUPPORTED_BOUNDARY_MODE:
        raise ExternalDataVerificationInputError(f"external boundary mode 不支援：{boundary_mode}")

    boundary_status = _required_text(payload, "boundary_status")
    if boundary_status == "partial-draft" and not allow_partial:
        raise ExternalDataVerificationInputError("external boundary status is partial-draft；請使用 --allow-partial。")
    if boundary_status not in {"final", "partial-draft"}:
        raise ExternalDataVerificationInputError(f"external boundary status 不支援：{boundary_status}")

    title = _required_text(payload, "title")
    candidates = _candidate_boundaries(payload)
    planned_reads = [str(paths.json_path), str(fixture_path)]
    planned_writes = [str(paths.json_path), str(paths.markdown_path)]
    fixture_candidates, fixture_warnings = _load_fixture_candidates(fixture_path)

    if not confirm:
        return ExternalDataVerificationAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            boundary_json_path=paths.json_path,
            boundary_markdown_path=paths.markdown_path,
            verification_status=boundary_status,
            candidate_count=len(candidates),
            verified_candidate_count=0,
            warning_count=len(fixture_warnings),
            dry_run=True,
            requires_confirmation=True,
            provider=provider,
            fixture_path=fixture_path,
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            generated=False,
            already_exists=False,
            not_investment_advice=True,
        )

    if _is_verified(payload, fixture_path=fixture_path) and not force:
        verified_count = _verified_candidate_count(candidates)
        return ExternalDataVerificationAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            boundary_json_path=paths.json_path,
            boundary_markdown_path=paths.markdown_path,
            verification_status=boundary_status,
            candidate_count=len(candidates),
            verified_candidate_count=verified_count,
            warning_count=len(_warnings(payload)),
            dry_run=False,
            requires_confirmation=False,
            provider=provider,
            fixture_path=fixture_path,
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            generated=False,
            already_exists=True,
            not_investment_advice=True,
        )

    fixture_index = _fixture_index(fixture_candidates)
    warnings = [*_warnings(payload), *fixture_warnings]
    verified_count = 0
    updated_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        updated = dict(candidate)
        fixture = _match_fixture(candidate, fixture_index)
        if fixture is None:
            warnings.append(f"no fixture match for {str(candidate.get('company_name', '')).strip()}")
        else:
            updated.update(
                {
                    "external_verification_status": "verified",
                    "source_status": str(fixture.get("source_status", "fixture_available")),
                    "data_date": fixture.get("data_date"),
                    "external_data": fixture.get("external_data", {}),
                    "external_data_source": {
                        "provider": provider,
                        "fixture_path": str(fixture_path),
                        "source_name": str(fixture.get("source_name", "local fixture")),
                        "matched_company_name": str(fixture.get("company_name", "")),
                        "matched_tickers": _string_list(fixture.get("tickers")),
                    },
                }
            )
            verified_count += 1
        updated_candidates.append(updated)

    snapshot_path = _write_preverification_boundary_snapshot(podcast_id, episode_ref, boundary_input_raw)
    payload["candidate_boundaries"] = updated_candidates
    payload["warnings"] = _unique(warnings)
    payload["external_data_verification"] = {
        "verification_mode": VERIFICATION_MODE,
        "provider": provider,
        "fixture_path": fixture_path.resolve(strict=False).as_posix(),
        "fixture_sha256": _fixture_sha256(fixture_path),
        "boundary_input_path": paths.json_path.resolve(strict=False).as_posix(),
        "boundary_input_sha256": hashlib.sha256(boundary_input_raw).hexdigest(),
        "preverification_snapshot_path": snapshot_path.resolve(strict=False).as_posix(),
        "preverification_snapshot_sha256": hashlib.sha256(boundary_input_raw).hexdigest(),
        "candidate_count": len(updated_candidates),
        "verified_candidate_count": verified_count,
        "not_investment_advice": True,
    }
    payload["not_investment_advice"] = True
    markdown = _render_markdown(payload)
    _write_boundary(paths.json_path, paths.markdown_path, payload, markdown)

    return ExternalDataVerificationAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        boundary_json_path=paths.json_path,
        boundary_markdown_path=paths.markdown_path,
        verification_status=boundary_status,
        candidate_count=len(updated_candidates),
        verified_candidate_count=verified_count,
        warning_count=len(payload["warnings"]),
        dry_run=False,
        requires_confirmation=False,
        provider=provider,
        fixture_path=fixture_path,
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        generated=True,
        already_exists=False,
        not_investment_advice=True,
    )


def _load_boundary_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExternalDataVerificationInputError(f"external boundary JSON 格式錯誤：{json_path}") from exc
    except OSError as exc:
        raise ExternalDataVerificationInputError(f"無法讀取 external boundary：{exc}") from exc
    if not isinstance(payload, dict):
        raise ExternalDataVerificationInputError("external boundary JSON 必須是 object。")
    return payload


def _validate_boundary_identity(payload: dict[str, Any], podcast_id: str, episode_ref: str) -> None:
    if payload.get("podcast_id") != podcast_id or payload.get("episode_ref") != episode_ref:
        raise ExternalDataVerificationInputError("external boundary 的 podcast_id 或 episode_ref 不符合請求。")


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ExternalDataVerificationInputError(f"external boundary 缺少有效欄位：{key}")
    return value


def _candidate_boundaries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("candidate_boundaries")
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _warnings(payload: dict[str, Any]) -> list[str]:
    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        return []
    return [str(warning) for warning in warnings]


def _load_fixture_candidates(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"fixture config missing: {path}"]
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [], [f"fixture config unreadable: {exc}"]
    if not isinstance(payload, dict):
        return [], ["fixture config must be a mapping"]
    candidates = payload.get("candidates")
    if candidates is None:
        return [], []
    if not isinstance(candidates, list):
        return [], ["fixture config candidates must be a list"]
    return [candidate for candidate in candidates if isinstance(candidate, dict)], []


def _fixture_index(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        keys = [
            _normalize_key(str(candidate.get("company_name", ""))),
            *[_normalize_key(ticker) for ticker in _string_list(candidate.get("tickers"))],
        ]
        for key in keys:
            if key and key not in index:
                index[key] = candidate
    return index


def _match_fixture(candidate: dict[str, Any], fixture_index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    keys = [
        _normalize_key(str(candidate.get("company_name", ""))),
        *[_normalize_key(ticker) for ticker in _string_list(candidate.get("tickers"))],
    ]
    for key in keys:
        if key in fixture_index:
            return fixture_index[key]
    return None


def _is_verified(payload: dict[str, Any], *, fixture_path: Path | None = None) -> bool:
    """Recognize only a marker bound to the current fixture bytes when supplied."""

    verification = payload.get("external_data_verification")
    if not isinstance(verification, dict) or verification.get("verification_mode") != VERIFICATION_MODE:
        return False
    if fixture_path is None:
        return True
    current_sha = _fixture_sha256(fixture_path)
    return (
        current_sha is not None
        and verification.get("fixture_path") == fixture_path.resolve(strict=False).as_posix()
        and verification.get("fixture_sha256") == current_sha
        and isinstance(verification.get("boundary_input_path"), str)
        and isinstance(verification.get("boundary_input_sha256"), str)
    )


def _fixture_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _verified_candidate_count(candidates: list[dict[str, Any]]) -> int:
    return sum(1 for candidate in candidates if candidate.get("external_verification_status") == "verified")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _normalize_key(value: str) -> str:
    stripped = value.strip()
    return stripped.lower() if stripped.isascii() else stripped


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _render_markdown(payload: dict[str, Any]) -> str:
    verification = payload["external_data_verification"]
    lines = [
        f"# {payload['episode_ref']} External data verification",
        "",
        "## Metadata",
        "",
        f"- Podcast ID: {payload['podcast_id']}",
        f"- Episode: {payload['episode_ref']}",
        f"- Title: {payload['title']}",
        f"- Boundary status: {payload['boundary_status']}",
        f"- Provider: {verification['provider']}",
        f"- Verified candidates: {verification['verified_candidate_count']} / {verification['candidate_count']}",
        "",
        "## Candidate status",
        "",
    ]
    for candidate in payload["candidate_boundaries"]:
        tickers = ", ".join(candidate.get("tickers", [])) or "unverified"
        lines.extend(
            [
                f"### {candidate.get('company_name', '')} [{tickers}]",
                "",
                f"- Relation type: {candidate.get('relation_type', '')}",
                f"- Evidence status: {candidate.get('evidence_status', '')}",
                f"- Mapping verification status: {candidate.get('verification_status', '')}",
                f"- External verification status: {candidate.get('external_verification_status', '')}",
                f"- Source status: {candidate.get('source_status', '')}",
                f"- Data date: {candidate.get('data_date') or 'unavailable'}",
                "",
            ]
        )
    lines.extend(["## Warnings", ""])
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- No warnings.")
    lines.extend(
        [
            "",
            "## Notice",
            "",
            "This file is not investment advice.",
            "Fixture data is external evidence only and does not change podcast evidence.",
            "No live market API was called.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_preverification_boundary_snapshot(podcast_id: str, episode_ref: str, boundary_raw: bytes) -> Path:
    """Preserve the exact boundary bytes before fixture verification mutates it."""

    digest = hashlib.sha256(boundary_raw).hexdigest()
    directory = PREVERIFICATION_BOUNDARIES_DIR / podcast_id / "verified-research" / "preverification-boundaries"
    path = directory / f"{storage.title_slug(episode_ref, 'episode')}-{digest}.json"
    stage_path = path.with_name(f".{path.name}.part")
    try:
        directory.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != boundary_raw:
                raise ExternalDataVerificationFailedError("preverification boundary snapshot identity collision")
            return path
        stage_path.write_bytes(boundary_raw)
        stage_path.replace(path)
        return path
    except ExternalDataVerificationFailedError:
        raise
    except OSError as exc:
        raise ExternalDataVerificationFailedError(f"寫入 preverification boundary snapshot 失敗：{exc}") from exc
    finally:
        try:
            stage_path.unlink(missing_ok=True)
        except OSError:
            pass


def _write_boundary(json_path: Path, markdown_path: Path, payload: dict[str, Any], markdown: str) -> None:
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
        raise ExternalDataVerificationFailedError(f"寫入 external data verification 失敗：{exc}") from exc
