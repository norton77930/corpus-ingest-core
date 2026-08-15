"""Recoverable Hermes MCP configuration and managed portable Skill sync.

The module deliberately accepts explicit paths and emits only bounded metadata.
It never reads Hermes credential files or session data, and it never includes
configuration values in a result or exception message.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Any
from uuid import uuid4

import yaml


MANIFEST_SCHEMA_VERSION = "hermes-integration-manifest-v1"
MANAGED_MCP_NAME = "podcast-ingest-core"
MANAGED_MCP_URL = "http://127.0.0.1:8767/mcp"
MANAGED_EXTERNAL_SKILLS_DIR = "podcast-ingest-core-skills"
# Spec 027 binds each contracted Skill to exactly one registry tool and rejects
# an artifact that names any other tool, so this allowlist stays the four
# single-tool Skills and remains the drift anchor for that contract layer.
MANAGED_SKILLS = (
    "corpus-episode-completion",
    "corpus-latest-episode-processing",
    "latest-episode-verified-research-report",
    "episode-verified-research-report",
)
# What actually ships to a Hermes install.  Spec 023's historical-path Skill is
# an orchestrator that names four tools by design; it cannot satisfy the Spec 027
# single-tool contract, and it carries its own Spec 023 Skill contract tests, so
# it is synchronized without widening the contracted allowlist above.
SYNCED_SKILLS = MANAGED_SKILLS + ("historical-episode-verified-report-path",)


class HermesIntegrationError(ValueError):
    """Bounded integration error whose message contains no config values."""


@dataclass(frozen=True)
class HermesIntegrationRequest:
    config_path: Path
    mcp_url: str
    skills_source: Path
    skills_target: Path
    local_skills_root: Path
    backup_root: Path
    external_skills_dir: str = MANAGED_EXTERNAL_SKILLS_DIR


@dataclass(frozen=True)
class _PreparedIntegration:
    request: HermesIntegrationRequest
    current_config: dict[str, Any]
    desired_config: dict[str, Any]
    desired_config_bytes: bytes
    config_before_digest: str
    config_after_digest: str
    source_skills_digest: str
    target_skills_digest: str | None
    config_changed: bool
    skills_changed: bool


def plan_integration(request: HermesIntegrationRequest) -> dict[str, Any]:
    """Return a redacted zero-write integration plan."""

    prepared = _prepare_integration(request)
    return _safe_result(prepared, status="planned")


def apply_integration(request: HermesIntegrationRequest) -> dict[str, Any]:
    """Apply config and Skill changes with one manifest-bound backup bundle."""

    prepared = _prepare_integration(request)
    if not prepared.config_changed and not prepared.skills_changed:
        return _safe_result(prepared, status="no_op")

    bundle = _new_backup_bundle(request.backup_root)
    manifest_path = bundle / "manifest.json"
    config_backup = bundle / "config.yaml"
    skills_backup = bundle / "managed-skills"
    staged_config: Path | None = None
    staged_skills: Path | None = None
    manifest: dict[str, Any] | None = None
    config_existed = request.config_path.exists()
    skills_existed = request.skills_target.exists()
    config_replaced = False
    skills_replaced = False

    try:
        if prepared.config_changed:
            shutil.copy2(request.config_path, config_backup)
            staged_config = _stage_config(
                request.config_path,
                prepared.desired_config_bytes,
            )
        if prepared.skills_changed:
            if skills_existed:
                _copy_tree(request.skills_target, skills_backup)
            staged_skills = _stage_skills(request.skills_source, request.skills_target)

        manifest = _manifest_payload(
            prepared,
            config_backup=config_backup if prepared.config_changed else None,
            skills_backup=skills_backup if skills_existed and prepared.skills_changed else None,
            config_existed=config_existed,
            skills_existed=skills_existed,
            rollback_state="applying",
        )
        _write_json_atomic(manifest_path, manifest)

        if prepared.skills_changed:
            assert staged_skills is not None
            _replace_skills_target(staged_skills, request.skills_target)
            skills_replaced = True
            staged_skills = None
        if prepared.config_changed:
            assert staged_config is not None
            _replace_staged_config(staged_config, request.config_path)
            config_replaced = True
            staged_config = None

        manifest["rollback_state"] = "available"
        _write_json_atomic(manifest_path, manifest)
    except Exception as exc:
        rollback_ok = _restore_surfaces(
            config_path=request.config_path,
            config_backup=config_backup if prepared.config_changed else None,
            config_existed=config_existed,
            restore_config=config_replaced,
            skills_target=request.skills_target,
            skills_backup=skills_backup if skills_existed and prepared.skills_changed else None,
            skills_existed=skills_existed,
            restore_skills=skills_replaced,
        )
        _remove_path(staged_config)
        _remove_path(staged_skills)
        if rollback_ok and manifest is not None:
            rollback_ok = _surfaces_match_manifest_before(
                manifest,
                config_path=request.config_path,
                skills_target=request.skills_target,
            )
        if rollback_ok:
            if manifest is not None:
                manifest["rollback_state"] = "rolled_back"
                try:
                    _write_json_atomic(manifest_path, manifest)
                except Exception as manifest_exc:
                    raise HermesIntegrationError(
                        "integration apply failed; surfaces were restored but the "
                        "recovery manifest update failed"
                    ) from manifest_exc
            raise HermesIntegrationError(
                "integration apply failed and was rolled back"
            ) from exc
        raise HermesIntegrationError(
            "integration apply failed and automatic rollback failed"
        ) from exc

    result = _safe_result(prepared, status="changed")
    result["backup_path"] = str(bundle)
    result["manifest_path"] = str(manifest_path)
    return result


def rollback_integration(
    manifest_path: Path,
    *,
    expected_config_path: Path,
    expected_skills_target: Path,
) -> dict[str, Any]:
    """Restore only the paths bound into a generated integration manifest."""

    manifest = _read_manifest(manifest_path)
    if expected_config_path.is_symlink():
        raise HermesIntegrationError("rollback config target is invalid")
    if expected_skills_target.is_symlink():
        raise HermesIntegrationError("rollback Skill target is invalid")
    manifest_config_path = Path(manifest["config_path"]).resolve()
    manifest_skills_target = Path(manifest["skills_target"]).resolve()
    if manifest_config_path != expected_config_path.resolve():
        raise HermesIntegrationError("rollback config target does not match manifest")
    if manifest_skills_target != expected_skills_target.resolve():
        raise HermesIntegrationError("rollback Skill target does not match manifest")
    if manifest.get("rollback_state") == "rolled_back":
        if not _surfaces_match_manifest_before(
            manifest,
            config_path=manifest_config_path,
            skills_target=manifest_skills_target,
        ):
            raise HermesIntegrationError("integration rollback verification failed")
        return {
            "status": "no_op",
            "backup_path": str(manifest_path.parent),
            "manifest_path": str(manifest_path),
        }

    config_backup = _manifest_backup_path(manifest_path, manifest.get("config_backup"))
    skills_backup = _manifest_backup_path(manifest_path, manifest.get("skills_backup"))
    if not _rollback_backups_match_manifest(
        manifest,
        config_backup=config_backup,
        skills_backup=skills_backup,
    ):
        raise HermesIntegrationError("integration backup integrity check failed")
    ok = _restore_surfaces(
        config_path=manifest_config_path,
        config_backup=config_backup,
        config_existed=bool(manifest["config_existed"]),
        restore_config=bool(manifest["config_changed"]),
        skills_target=manifest_skills_target,
        skills_backup=skills_backup,
        skills_existed=bool(manifest["skills_existed"]),
        restore_skills=bool(manifest["skills_changed"]),
    )
    if not ok:
        raise HermesIntegrationError("integration rollback failed")
    if not _surfaces_match_manifest_before(
        manifest,
        config_path=manifest_config_path,
        skills_target=manifest_skills_target,
    ):
        raise HermesIntegrationError("integration rollback verification failed")

    manifest["rollback_state"] = "rolled_back"
    try:
        _write_json_atomic(manifest_path, manifest)
    except Exception as exc:
        raise HermesIntegrationError(
            "integration rollback succeeded; surfaces were restored but the "
            "recovery manifest update failed"
        ) from exc
    return {
        "status": "rolled_back",
        "backup_path": str(manifest_path.parent),
        "manifest_path": str(manifest_path),
    }


def tree_digest(root: Path) -> str:
    """Return a deterministic digest of one non-symlink directory tree."""

    return _tree_digest(root)


def _managed_source_digest(root: Path) -> str:
    return _tree_digest(root, allowed_top_level=frozenset(SYNCED_SKILLS))


def _tree_digest(
    root: Path,
    *,
    allowed_top_level: frozenset[str] | None = None,
) -> str:
    if not root.is_dir() or root.is_symlink():
        raise HermesIntegrationError("managed Skill tree is missing or invalid")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative_path = path.relative_to(root)
        if allowed_top_level is not None and relative_path.parts[0] not in allowed_top_level:
            continue
        if path.is_symlink():
            raise HermesIntegrationError("managed Skill tree contains a symlink")
        relative = relative_path.as_posix().encode("utf-8")
        if path.is_dir():
            digest.update(b"D\0" + relative + b"\0")
        elif path.is_file():
            digest.update(b"F\0" + relative + b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        else:
            raise HermesIntegrationError("managed Skill tree contains an invalid entry")
    return digest.hexdigest()


def _prepare_integration(request: HermesIntegrationRequest) -> _PreparedIntegration:
    _validate_request(request)
    current_config = _load_config(request.config_path)
    desired_config = _merge_managed_config(
        current_config,
        mcp_url=request.mcp_url,
        external_skills_dir=request.external_skills_dir,
    )
    desired_config_bytes = yaml.safe_dump(
        desired_config,
        allow_unicode=True,
        sort_keys=False,
    ).encode("utf-8")
    source_digest = _managed_source_digest(request.skills_source)
    target_digest = tree_digest(request.skills_target) if request.skills_target.exists() else None
    config_changed = current_config != desired_config
    config_before_digest = _file_digest(request.config_path)
    config_after_digest = (
        hashlib.sha256(desired_config_bytes).hexdigest()
        if config_changed
        else config_before_digest
    )
    return _PreparedIntegration(
        request=request,
        current_config=current_config,
        desired_config=desired_config,
        desired_config_bytes=desired_config_bytes,
        config_before_digest=config_before_digest,
        config_after_digest=config_after_digest,
        source_skills_digest=source_digest,
        target_skills_digest=target_digest,
        config_changed=config_changed,
        skills_changed=target_digest != source_digest,
    )


def _validate_request(request: HermesIntegrationRequest) -> None:
    if request.mcp_url != MANAGED_MCP_URL:
        raise HermesIntegrationError("managed MCP URL is outside the approved boundary")
    if request.external_skills_dir != MANAGED_EXTERNAL_SKILLS_DIR:
        raise HermesIntegrationError("external Skill directory is outside the approved boundary")
    if not request.config_path.is_file() or request.config_path.is_symlink():
        raise HermesIntegrationError("Hermes config path is missing or invalid")
    if not request.skills_source.is_dir() or request.skills_source.is_symlink():
        raise HermesIntegrationError("managed Skill source root is missing or invalid")

    for name in SYNCED_SKILLS:
        skill_dir = request.skills_source / name
        if (
            not skill_dir.is_dir()
            or skill_dir.is_symlink()
            or not (skill_dir / "SKILL.md").is_file()
        ):
            raise HermesIntegrationError("managed Skill source set is invalid")
        if (request.local_skills_root / name).exists():
            raise HermesIntegrationError("managed Skill is shadowed locally")

    target_parent = request.skills_target.parent.resolve()
    backup_root = request.backup_root.resolve()
    if target_parent == backup_root or backup_root.is_relative_to(request.skills_target.resolve()):
        raise HermesIntegrationError("backup root overlaps the managed Skill target")


def _load_config(path: Path) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise HermesIntegrationError("Hermes config could not be parsed") from exc
    if not isinstance(parsed, dict):
        raise HermesIntegrationError("Hermes config root must be a mapping")
    return parsed


def _merge_managed_config(
    current: dict[str, Any],
    *,
    mcp_url: str,
    external_skills_dir: str,
) -> dict[str, Any]:
    desired = deepcopy(current)
    servers = desired.setdefault("mcp_servers", {})
    if not isinstance(servers, dict):
        raise HermesIntegrationError("Hermes mcp_servers must be a mapping")
    servers[MANAGED_MCP_NAME] = {
        "url": mcp_url,
        "timeout": 60,
        "connect_timeout": 15,
    }

    skills = desired.setdefault("skills", {})
    if not isinstance(skills, dict):
        raise HermesIntegrationError("Hermes skills must be a mapping")
    raw_dirs = skills.get("external_dirs")
    if raw_dirs is None:
        external_dirs: list[str] = []
    elif isinstance(raw_dirs, str):
        external_dirs = [raw_dirs]
    elif isinstance(raw_dirs, list) and all(isinstance(item, str) for item in raw_dirs):
        external_dirs = list(raw_dirs)
    else:
        raise HermesIntegrationError("Hermes external Skill directories are invalid")
    if external_skills_dir not in external_dirs:
        external_dirs.append(external_skills_dir)
    skills["external_dirs"] = external_dirs
    return desired


def _safe_result(prepared: _PreparedIntegration, *, status: str) -> dict[str, Any]:
    changed_keys = []
    if prepared.config_changed:
        changed_keys = [
            f"mcp_servers.{MANAGED_MCP_NAME}",
            "skills.external_dirs",
        ]
    return {
        "status": status,
        "config_changed": prepared.config_changed,
        "skills_changed": prepared.skills_changed,
        "changed_keys": changed_keys,
        "config_before_digest": prepared.config_before_digest,
        "config_after_digest": prepared.config_after_digest,
        "source_skills_digest": prepared.source_skills_digest,
        "target_skills_digest": prepared.target_skills_digest,
        "managed_skill_digests": {
            name: tree_digest(prepared.request.skills_source / name)
            for name in SYNCED_SKILLS
        },
        "backup_path": None,
        "manifest_path": None,
    }


def _new_backup_bundle(backup_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = backup_root / f"{timestamp}-{uuid4().hex[:8]}"
    bundle.mkdir(parents=True, exist_ok=False)
    return bundle


def _stage_config(config_path: Path, content: bytes) -> Path:
    staged = config_path.with_name(f".{config_path.name}.staging-{uuid4().hex}")
    staged.write_bytes(content)
    os.chmod(staged, stat.S_IMODE(config_path.stat().st_mode))
    _load_config(staged)
    return staged


def _stage_skills(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_name(f".{target.name}.staging-{uuid4().hex}")
    staged.mkdir()
    try:
        for name in SYNCED_SKILLS:
            _copy_tree(source / name, staged / name)
        if tree_digest(staged) != _managed_source_digest(source):
            raise HermesIntegrationError("staged managed Skills failed validation")
    except Exception:
        _remove_path(staged)
        raise
    return staged


def _replace_skills_target(staged: Path, target: Path) -> None:
    if not target.exists():
        os.replace(staged, target)
        return

    recovery = target.with_name(f".{target.name}.recovery-{uuid4().hex}")
    os.replace(target, recovery)
    try:
        os.replace(staged, target)
    except BaseException:
        if not target.exists() and recovery.exists():
            os.replace(recovery, target)
        raise
    _remove_path(recovery)


def _replace_staged_config(staged: Path, target: Path) -> None:
    os.replace(staged, target)


def _copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        raise HermesIntegrationError("managed Skill staging target already exists")
    shutil.copytree(source, target, symlinks=False)


def _restore_surfaces(
    *,
    config_path: Path,
    config_backup: Path | None,
    config_existed: bool,
    restore_config: bool,
    skills_target: Path,
    skills_backup: Path | None,
    skills_existed: bool,
    restore_skills: bool,
) -> bool:
    try:
        if restore_skills and skills_existed:
            if skills_backup is None or not skills_backup.is_dir():
                return False
        if restore_config and config_existed:
            if config_backup is None or not config_backup.is_file():
                return False

        if restore_skills:
            _remove_path(skills_target)
            if skills_existed:
                assert skills_backup is not None
                staged_skills = skills_target.with_name(
                    f".{skills_target.name}.rollback-{uuid4().hex}"
                )
                _copy_tree(skills_backup, staged_skills)
                os.replace(staged_skills, skills_target)
        if restore_config:
            if config_existed:
                assert config_backup is not None
                staged_config = config_path.with_name(
                    f".{config_path.name}.rollback-{uuid4().hex}"
                )
                shutil.copy2(config_backup, staged_config)
                os.replace(staged_config, config_path)
            else:
                config_path.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _manifest_payload(
    prepared: _PreparedIntegration,
    *,
    config_backup: Path | None,
    skills_backup: Path | None,
    config_existed: bool,
    skills_existed: bool,
    rollback_state: str,
) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(prepared.request.config_path.resolve()),
        "skills_target": str(prepared.request.skills_target.resolve()),
        "config_backup": config_backup.name if config_backup is not None else None,
        "skills_backup": skills_backup.name if skills_backup is not None else None,
        "config_existed": config_existed,
        "skills_existed": skills_existed,
        "config_changed": prepared.config_changed,
        "skills_changed": prepared.skills_changed,
        "config_before_digest": prepared.config_before_digest,
        "config_after_digest": prepared.config_after_digest,
        "skills_before_digest": prepared.target_skills_digest,
        "skills_after_digest": prepared.source_skills_digest,
        "rollback_state": rollback_state,
    }


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HermesIntegrationError("integration manifest could not be parsed") from exc
    required = {
        "schema_version",
        "created_at",
        "config_path",
        "skills_target",
        "config_backup",
        "skills_backup",
        "config_existed",
        "skills_existed",
        "config_changed",
        "skills_changed",
        "config_before_digest",
        "config_after_digest",
        "skills_before_digest",
        "skills_after_digest",
        "rollback_state",
    }
    if not isinstance(payload, dict) or payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise HermesIntegrationError("integration manifest schema is invalid")
    if not required <= payload.keys():
        raise HermesIntegrationError("integration manifest fields are incomplete")
    if not _manifest_fields_are_valid(payload):
        raise HermesIntegrationError("integration manifest fields are invalid")
    if payload["config_changed"] and payload["config_existed"] and not payload["config_backup"]:
        raise HermesIntegrationError("integration manifest fields are incomplete")
    if payload["skills_changed"] and payload["skills_existed"] and not payload["skills_backup"]:
        raise HermesIntegrationError("integration manifest fields are incomplete")
    if payload["rollback_state"] not in {"available", "applying", "rolled_back"}:
        raise HermesIntegrationError("integration manifest fields are incomplete")
    return payload


def _manifest_fields_are_valid(payload: dict[str, Any]) -> bool:
    boolean_fields = (
        "config_existed",
        "skills_existed",
        "config_changed",
        "skills_changed",
    )
    if any(type(payload[field]) is not bool for field in boolean_fields):
        return False

    string_fields = ("created_at", "config_path", "skills_target")
    if any(not isinstance(payload[field], str) or not payload[field] for field in string_fields):
        return False

    optional_backup_fields = ("config_backup", "skills_backup")
    if any(
        value is not None and (not isinstance(value, str) or not value)
        for value in (payload[field] for field in optional_backup_fields)
    ):
        return False

    required_digests = (
        "config_before_digest",
        "config_after_digest",
        "skills_after_digest",
    )
    if any(not _is_sha256_digest(payload[field]) for field in required_digests):
        return False

    skills_before_digest = payload["skills_before_digest"]
    if payload["skills_existed"]:
        if not _is_sha256_digest(skills_before_digest):
            return False
    elif skills_before_digest is not None:
        return False

    return payload["rollback_state"] in {"available", "applying", "rolled_back"}


def _is_sha256_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _manifest_backup_path(manifest_path: Path, name: Any) -> Path | None:
    if name is None:
        return None
    if not isinstance(name, str) or Path(name).name != name:
        raise HermesIntegrationError("integration manifest backup path is invalid")
    return manifest_path.parent / name


def _rollback_backups_match_manifest(
    manifest: dict[str, Any],
    *,
    config_backup: Path | None,
    skills_backup: Path | None,
) -> bool:
    try:
        if manifest["config_changed"] and manifest["config_existed"]:
            if config_backup is None or not config_backup.is_file():
                return False
            if _file_digest(config_backup) != manifest["config_before_digest"]:
                return False
        if manifest["skills_changed"] and manifest["skills_existed"]:
            if skills_backup is None or not skills_backup.is_dir():
                return False
            if tree_digest(skills_backup) != manifest["skills_before_digest"]:
                return False
        return True
    except (OSError, HermesIntegrationError):
        return False


def _surfaces_match_manifest_before(
    manifest: dict[str, Any],
    *,
    config_path: Path,
    skills_target: Path,
) -> bool:
    try:
        if manifest["config_changed"]:
            if manifest["config_existed"]:
                if not config_path.is_file() or config_path.is_symlink():
                    return False
                if _file_digest(config_path) != manifest["config_before_digest"]:
                    return False
            elif config_path.exists():
                return False

        if manifest["skills_changed"]:
            if manifest["skills_existed"]:
                if not skills_target.is_dir() or skills_target.is_symlink():
                    return False
                if tree_digest(skills_target) != manifest["skills_before_digest"]:
                    return False
            elif skills_target.exists():
                return False

        return True
    except (OSError, HermesIntegrationError):
        return False


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    staged = path.with_name(f".{path.name}.staging-{uuid4().hex}")
    try:
        staged.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        json.loads(staged.read_text(encoding="utf-8"))
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _remove_path(path: Path | None) -> None:
    if path is None or not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
