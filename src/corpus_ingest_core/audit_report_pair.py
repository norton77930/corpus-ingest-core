"""Generation-bound, JSON-last commit pairs for fixed audit report paths.

The Markdown member is installed first and JSON is the final commit marker.  The
JSON ``audit_report_pair`` object is the commit marker readers must validate;
Markdown alone is never reusable.  A destination-derived cross-process lock
serializes both replacements and recovery, so a failed update restores the last
complete generation rather than leaving a permanent mismatched pair.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from .artifact_lock import exclusive_artifact_claim

PAIR_SCHEMA_VERSION = "audit-report-pair-v1"
_PAIR_KEY = "audit_report_pair"
_MARKER_PREFIX = "<!-- audit-report-pair: "
_MARKER_SUFFIX = " -->"


def write_atomic_audit_report_pair(
    json_path: Path,
    markdown_path: Path,
    payload: dict[str, Any],
    markdown: str,
) -> str:
    """Write a validated pair under a destination lock, restoring on failure.

    JSON is committed last.  The post-write production reader is deliberately
    part of the critical section: callers cannot reuse or report a generation
    before it passes the same complete-pair contract used by production reads.
    """

    if not isinstance(payload, dict):
        raise TypeError("audit report payload must be a mapping")
    json_path = Path(json_path)
    markdown_path = Path(markdown_path)
    generation, json_bytes, rendered_markdown = _render_pair(payload, markdown)
    claim_path = _pair_claim_path(json_path, markdown_path)
    try:
        with exclusive_artifact_claim(claim_path):
            old_pair = read_complete_audit_report_pair(json_path, markdown_path)
            old_json = json_path.read_bytes() if old_pair is not None else None
            old_markdown = markdown_path.read_bytes() if old_pair is not None else None
            token = uuid.uuid4().hex
            markdown_stage = markdown_path.with_name(f".audit-stage-{token}-{markdown_path.name}")
            json_stage = json_path.with_name(f".audit-stage-{token}-{json_path.name}")
            try:
                json_path.parent.mkdir(parents=True, exist_ok=True)
                if markdown_path.parent != json_path.parent:
                    markdown_path.parent.mkdir(parents=True, exist_ok=True)
                markdown_stage.write_text(rendered_markdown, encoding="utf-8")
                json_stage.write_bytes(json_bytes)
                markdown_stage.replace(markdown_path)
                # JSON is the only commit marker and is intentionally committed last.
                json_stage.replace(json_path)
                if read_complete_audit_report_pair(json_path, markdown_path) is None:
                    raise OSError("audit report pair production validation failed")
            except Exception as exc:
                _restore_complete_pair(
                    json_path,
                    markdown_path,
                    old_json=old_json,
                    old_markdown=old_markdown,
                )
                raise OSError("audit report pair commit failed") from exc
            finally:
                _remove_if_present(markdown_stage)
                _remove_if_present(json_stage)
            return generation
    except TimeoutError as exc:
        raise OSError("audit report pair lock timed out") from exc


def is_complete_audit_report_pair(json_path: Path, markdown_path: Path) -> bool:
    """Return true only for a same-generation mutually verified fixed-path pair."""

    return read_complete_audit_report_pair(json_path, markdown_path) is not None


def read_complete_audit_report_pair(
    json_path: Path,
    markdown_path: Path,
) -> dict[str, Any] | None:
    """Read only a complete pair; malformed, partial, and mismatched pairs fail closed."""

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        markdown = markdown_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    pair = payload.get(_PAIR_KEY)
    if not isinstance(pair, dict) or set(pair) != {"schema_version", "generation", "markdown_sha256"}:
        return None
    generation = pair.get("generation")
    markdown_sha256 = pair.get("markdown_sha256")
    if (
        pair.get("schema_version") != PAIR_SCHEMA_VERSION
        or not isinstance(generation, str)
        or len(generation) != 32
        or not isinstance(markdown_sha256, str)
        or not _is_sha256(markdown_sha256)
        or _sha256(markdown.encode("utf-8")) != markdown_sha256
    ):
        return None
    marker = _parse_markdown_marker(markdown)
    if marker is None or marker.get("generation") != generation:
        return None
    payload_body = dict(payload)
    payload_body.pop(_PAIR_KEY, None)
    expected_body_sha256 = _sha256(_canonical_json_bytes(payload_body))
    if marker.get("json_payload_sha256") != expected_body_sha256:
        return None
    return payload


def _render_pair(payload: dict[str, Any], markdown: str) -> tuple[str, bytes, str]:
    generation = uuid.uuid4().hex
    payload_body = dict(payload)
    payload_body.pop(_PAIR_KEY, None)
    body_sha256 = _sha256(_canonical_json_bytes(payload_body))
    marker = _markdown_marker(generation, body_sha256)
    rendered_markdown = markdown.rstrip("\n") + "\n\n" + marker + "\n"
    markdown_sha256 = _sha256(rendered_markdown.encode("utf-8"))
    committed_payload = {
        **payload_body,
        _PAIR_KEY: {
            "schema_version": PAIR_SCHEMA_VERSION,
            "generation": generation,
            "markdown_sha256": markdown_sha256,
        },
    }
    json_bytes = json.dumps(committed_payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    return generation, json_bytes, rendered_markdown


def _pair_claim_path(json_path: Path, markdown_path: Path) -> Path:
    """Address a stable podcast-level lock from both fixed pair destinations."""

    key = "\x00".join(
        sorted(
            (
                json_path.resolve(strict=False).as_posix(),
                markdown_path.resolve(strict=False).as_posix(),
            )
        )
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return json_path.parent / f".audit-report-pair-{digest}.claim"


def _restore_complete_pair(
    json_path: Path,
    markdown_path: Path,
    *,
    old_json: bytes | None,
    old_markdown: bytes | None,
) -> None:
    """Restore a known complete pair, or remove both members when none existed."""

    try:
        if old_json is None or old_markdown is None:
            _remove_if_present(json_path)
            _remove_if_present(markdown_path)
            return
        _replace_bytes(markdown_path, old_markdown, "audit-rollback-markdown")
        _replace_bytes(json_path, old_json, "audit-rollback-json")
        if read_complete_audit_report_pair(json_path, markdown_path) is None:
            raise OSError("audit report pair rollback validation failed")
    except Exception as exc:
        raise OSError("audit report pair recovery failed") from exc


def _replace_bytes(destination: Path, raw: bytes, prefix: str) -> None:
    stage = destination.with_name(f".{prefix}-{uuid.uuid4().hex}-{destination.name}")
    try:
        stage.write_bytes(raw)
        stage.replace(destination)
    finally:
        _remove_if_present(stage)


def _remove_if_present(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _markdown_marker(generation: str, payload_sha256: str) -> str:
    return (
        _MARKER_PREFIX
        + json.dumps(
            {"generation": generation, "json_payload_sha256": payload_sha256},
            sort_keys=True,
            separators=(",", ":"),
        )
        + _MARKER_SUFFIX
    )


def _parse_markdown_marker(markdown: str) -> dict[str, str] | None:
    lines = markdown.rstrip("\n").splitlines()
    if not lines:
        return None
    line = lines[-1]
    if not line.startswith(_MARKER_PREFIX) or not line.endswith(_MARKER_SUFFIX):
        return None
    try:
        value = json.loads(line[len(_MARKER_PREFIX) : -len(_MARKER_SUFFIX)])
    except json.JSONDecodeError:
        return None
    if (
        not isinstance(value, dict)
        or set(value) != {"generation", "json_payload_sha256"}
        or not isinstance(value.get("generation"), str)
        or len(value["generation"]) != 32
        or not isinstance(value.get("json_payload_sha256"), str)
        or not _is_sha256(value["json_payload_sha256"])
    ):
        return None
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
