from __future__ import annotations

import json
from pathlib import Path
import time

import pytest
import yaml


SYNCED_SKILLS = (
    "corpus-episode-completion",
    "corpus-latest-episode-processing",
    "latest-episode-verified-research-report",
    "episode-verified-research-report",
    "historical-episode-verified-report-path",
)
MCP_URL = "http://127.0.0.1:8767/mcp"


def _write_skill(root: Path, name: str, body: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test\n---\n\n{body}\n",
        encoding="utf-8",
    )
    references = skill_dir / "references"
    references.mkdir()
    (references / "contract.txt").write_text(f"{name}:{body}\n", encoding="utf-8")


def _make_request(tmp_path: Path):
    from podcast_ingest_core.hermes_integration import HermesIntegrationRequest

    config_path = tmp_path / "hermes" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text(
        yaml.safe_dump(
            {
                "model": {"api_key": "synthetic-secret-value", "provider": "custom"},
                "unknown": {"keep": [1, 2, 3]},
                "mcp_servers": {
                    "existing": {
                        "url": "http://synthetic-private-endpoint.invalid/sse",
                        "transport": "sse",
                    }
                },
                "skills": {"external_dirs": ["team-skills"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    source = tmp_path / "source-skills"
    for name in SYNCED_SKILLS:
        _write_skill(source, name, "source")

    return HermesIntegrationRequest(
        config_path=config_path,
        mcp_url=MCP_URL,
        skills_source=source,
        skills_target=tmp_path / "hermes" / "podcast-ingest-core-skills",
        local_skills_root=tmp_path / "hermes" / "skills",
        backup_root=tmp_path / "hermes" / "integration-backups",
        external_skills_dir="podcast-ingest-core-skills",
    )


def test_plan_is_zero_write_preserves_existing_config_and_redacts_values(tmp_path):
    from podcast_ingest_core.hermes_integration import plan_integration

    request = _make_request(tmp_path)
    before_bytes = request.config_path.read_bytes()
    before_mtime = request.config_path.stat().st_mtime_ns

    result = plan_integration(request)

    assert result["status"] == "planned"
    assert result["config_changed"] is True
    assert result["skills_changed"] is True
    assert result["changed_keys"] == [
        "mcp_servers.podcast-ingest-core",
        "skills.external_dirs",
    ]
    assert request.config_path.read_bytes() == before_bytes
    assert request.config_path.stat().st_mtime_ns == before_mtime
    assert not request.backup_root.exists()
    serialized = json.dumps(result, ensure_ascii=False)
    assert MCP_URL not in serialized
    assert "synthetic-secret-value" not in serialized
    assert "synthetic-private-endpoint" not in serialized


def test_apply_preserves_unmanaged_values_and_syncs_every_synced_skill(tmp_path):
    from podcast_ingest_core.hermes_integration import apply_integration, tree_digest

    request = _make_request(tmp_path)

    result = apply_integration(request)

    assert result["status"] == "changed"
    assert result["backup_path"]
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.is_file()

    payload = yaml.safe_load(request.config_path.read_text(encoding="utf-8"))
    assert payload["model"] == {
        "api_key": "synthetic-secret-value",
        "provider": "custom",
    }
    assert payload["unknown"] == {"keep": [1, 2, 3]}
    assert payload["mcp_servers"]["existing"] == {
        "url": "http://synthetic-private-endpoint.invalid/sse",
        "transport": "sse",
    }
    assert payload["mcp_servers"]["podcast-ingest-core"] == {
        "url": MCP_URL,
        "timeout": 60,
        "connect_timeout": 15,
    }
    assert payload["skills"]["external_dirs"] == [
        "team-skills",
        "podcast-ingest-core-skills",
    ]

    assert sorted(path.name for path in request.skills_target.iterdir()) == sorted(
        SYNCED_SKILLS
    )
    assert tree_digest(request.skills_target) == tree_digest(request.skills_source)
    serialized = json.dumps(result, ensure_ascii=False)
    assert MCP_URL not in serialized
    assert "synthetic-secret-value" not in serialized
    assert "synthetic-private-endpoint" not in serialized


def test_identical_apply_is_no_op_without_new_backup_or_mtime_change(tmp_path):
    from podcast_ingest_core.hermes_integration import apply_integration

    request = _make_request(tmp_path)
    first = apply_integration(request)
    first_backups = sorted(request.backup_root.iterdir())
    config_mtime = request.config_path.stat().st_mtime_ns
    target_mtime = request.skills_target.stat().st_mtime_ns
    time.sleep(0.01)

    second = apply_integration(request)

    assert first["status"] == "changed"
    assert second["status"] == "no_op"
    assert second["config_before_digest"] == second["config_after_digest"]
    assert second["backup_path"] is None
    assert sorted(request.backup_root.iterdir()) == first_backups
    assert request.config_path.stat().st_mtime_ns == config_mtime
    assert request.skills_target.stat().st_mtime_ns == target_mtime


def test_semantic_config_no_op_reports_the_unchanged_file_digest(tmp_path):
    from podcast_ingest_core.hermes_integration import apply_integration, plan_integration

    request = _make_request(tmp_path)
    apply_integration(request)
    current = request.config_path.read_text(encoding="utf-8")
    request.config_path.write_text("# operator comment\n" + current, encoding="utf-8")

    result = plan_integration(request)

    assert result["config_changed"] is False
    assert result["config_before_digest"] == result["config_after_digest"]


def test_local_skill_shadow_collision_fails_closed_without_writes(tmp_path):
    from podcast_ingest_core.hermes_integration import (
        HermesIntegrationError,
        apply_integration,
    )

    request = _make_request(tmp_path)
    collision = request.local_skills_root / SYNCED_SKILLS[0]
    collision.mkdir(parents=True)
    before = request.config_path.read_bytes()

    with pytest.raises(HermesIntegrationError, match="managed Skill is shadowed locally"):
        apply_integration(request)

    assert request.config_path.read_bytes() == before
    assert not request.skills_target.exists()
    assert not request.backup_root.exists()


def test_extra_source_skills_are_ignored_and_never_copied(tmp_path):
    from podcast_ingest_core.hermes_integration import apply_integration

    request = _make_request(tmp_path)
    _write_skill(request.skills_source, "unmanaged-repository-skill", "extra")

    result = apply_integration(request)

    assert result["status"] == "changed"
    assert not (request.skills_target / "unmanaged-repository-skill").exists()
    assert sorted(path.name for path in request.skills_target.iterdir()) == sorted(
        SYNCED_SKILLS
    )


def test_missing_managed_source_skill_fails_closed(tmp_path):
    from podcast_ingest_core.hermes_integration import (
        HermesIntegrationError,
        plan_integration,
    )

    request = _make_request(tmp_path)
    missing = request.skills_source / SYNCED_SKILLS[0]
    for path in sorted(missing.rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    missing.rmdir()

    with pytest.raises(HermesIntegrationError, match="managed Skill source set is invalid"):
        plan_integration(request)

    assert not request.backup_root.exists()


def test_manifest_bound_rollback_restores_previous_config_and_skills(tmp_path):
    from podcast_ingest_core.hermes_integration import (
        apply_integration,
        rollback_integration,
        tree_digest,
    )

    request = _make_request(tmp_path)
    request.skills_target.mkdir()
    for name in SYNCED_SKILLS:
        _write_skill(request.skills_target, name, "previous")
    original_config = request.config_path.read_bytes()
    original_skills_digest = tree_digest(request.skills_target)

    applied = apply_integration(request)
    rolled_back = rollback_integration(
        Path(applied["manifest_path"]),
        expected_config_path=request.config_path,
        expected_skills_target=request.skills_target,
    )

    assert rolled_back["status"] == "rolled_back"
    assert request.config_path.read_bytes() == original_config
    assert tree_digest(request.skills_target) == original_skills_digest


def test_repeated_rollback_fails_if_restored_surface_drifted(tmp_path):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    manifest_path = Path(applied["manifest_path"])
    hermes_integration.rollback_integration(
        manifest_path,
        expected_config_path=request.config_path,
        expected_skills_target=request.skills_target,
    )
    request.config_path.write_text("drifted: true\n", encoding="utf-8")

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration rollback verification failed",
    ):
        hermes_integration.rollback_integration(
            manifest_path,
            expected_config_path=request.config_path,
            expected_skills_target=request.skills_target,
        )


def test_apply_failure_restores_both_surfaces(tmp_path, monkeypatch):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    request.skills_target.mkdir()
    for name in SYNCED_SKILLS:
        _write_skill(request.skills_target, name, "previous")
    original_config = request.config_path.read_bytes()
    original_skills = hermes_integration.tree_digest(request.skills_target)

    def fail_config_replace(*args, **kwargs):
        del args, kwargs
        raise OSError("synthetic failure")

    monkeypatch.setattr(hermes_integration, "_replace_staged_config", fail_config_replace)

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration apply failed and was rolled back",
    ):
        hermes_integration.apply_integration(request)

    assert request.config_path.read_bytes() == original_config
    assert hermes_integration.tree_digest(request.skills_target) == original_skills


def test_apply_failure_reports_bounded_error_if_manifest_state_update_fails(
    tmp_path,
    monkeypatch,
):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    real_write_manifest = hermes_integration._write_json_atomic

    def fail_config_replace(*args, **kwargs):
        del args, kwargs
        raise OSError("synthetic config replacement failure")

    def fail_rolled_back_state(path, payload):
        if payload["rollback_state"] == "rolled_back":
            raise OSError("synthetic manifest update failure")
        return real_write_manifest(path, payload)

    monkeypatch.setattr(hermes_integration, "_replace_staged_config", fail_config_replace)
    monkeypatch.setattr(hermes_integration, "_write_json_atomic", fail_rolled_back_state)

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="surfaces were restored but the recovery manifest update failed",
    ):
        hermes_integration.apply_integration(request)


def test_apply_writes_recovery_manifest_before_live_replacement(tmp_path, monkeypatch):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)

    def fail_after_checking_manifest(*args, **kwargs):
        del args, kwargs
        bundles = list(request.backup_root.iterdir())
        assert len(bundles) == 1
        assert (bundles[0] / "manifest.json").is_file()
        raise OSError("synthetic replacement failure")

    monkeypatch.setattr(
        hermes_integration,
        "_replace_skills_target",
        fail_after_checking_manifest,
    )

    with pytest.raises(hermes_integration.HermesIntegrationError):
        hermes_integration.apply_integration(request)

    manifest_path = next(request.backup_root.iterdir()) / "manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["rollback_state"] == "rolled_back"


def test_skill_replacement_preserves_recoverable_previous_tree(tmp_path, monkeypatch):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    request.skills_target.mkdir()
    for name in SYNCED_SKILLS:
        _write_skill(request.skills_target, name, "previous")
    original_digest = hermes_integration.tree_digest(request.skills_target)
    real_replace = hermes_integration.os.replace
    observed_recovery_tree = False

    def fail_staged_install(source, target):
        nonlocal observed_recovery_tree
        source_path = Path(source)
        target_path = Path(target)
        if (
            source_path.name.startswith(f".{request.skills_target.name}.staging-")
            and target_path == request.skills_target
        ):
            observed_recovery_tree = any(
                path.is_dir()
                for path in request.skills_target.parent.glob(
                    f".{request.skills_target.name}.recovery-*"
                )
            )
            raise OSError("synthetic staged install failure")
        return real_replace(source, target)

    monkeypatch.setattr(hermes_integration.os, "replace", fail_staged_install)

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration apply failed and was rolled back",
    ):
        hermes_integration.apply_integration(request)

    assert observed_recovery_tree is True
    assert hermes_integration.tree_digest(request.skills_target) == original_digest


def test_rollback_rejects_symlink_target_alias(tmp_path):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    alias = tmp_path / "config-alias.yaml"
    try:
        alias.symlink_to(request.config_path)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="rollback config target is invalid",
    ):
        hermes_integration.rollback_integration(
            Path(applied["manifest_path"]),
            expected_config_path=alias,
            expected_skills_target=request.skills_target,
        )


def test_rollback_reports_bounded_error_if_manifest_state_update_fails(
    tmp_path,
    monkeypatch,
):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    manifest_path = Path(applied["manifest_path"])
    real_write_manifest = hermes_integration._write_json_atomic

    def fail_rolled_back_state(path, payload):
        if payload["rollback_state"] == "rolled_back":
            raise OSError("synthetic manifest update failure")
        return real_write_manifest(path, payload)

    monkeypatch.setattr(hermes_integration, "_write_json_atomic", fail_rolled_back_state)

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="surfaces were restored but the recovery manifest update failed",
    ):
        hermes_integration.rollback_integration(
            manifest_path,
            expected_config_path=request.config_path,
            expected_skills_target=request.skills_target,
        )


def test_rollback_verifies_restored_surface_digests(tmp_path, monkeypatch):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    manifest_path = Path(applied["manifest_path"])

    monkeypatch.setattr(
        hermes_integration,
        "_restore_surfaces",
        lambda **kwargs: True,
    )

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration rollback verification failed",
    ):
        hermes_integration.rollback_integration(
            manifest_path,
            expected_config_path=request.config_path,
            expected_skills_target=request.skills_target,
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["rollback_state"] == "available"


def test_rollback_rejects_tampered_config_backup(tmp_path):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    manifest_path = Path(applied["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backup_path = manifest_path.parent / manifest["config_backup"]
    backup_path.write_text("tampered-backup\n", encoding="utf-8")
    applied_config = request.config_path.read_bytes()

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration backup integrity check failed",
    ):
        hermes_integration.rollback_integration(
            manifest_path,
            expected_config_path=request.config_path,
            expected_skills_target=request.skills_target,
        )

    assert request.config_path.read_bytes() == applied_config


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("config_changed", "false"),
        ("config_before_digest", "not-a-sha256-digest"),
    ],
)
def test_rollback_rejects_manifest_invalid_field_types(tmp_path, field, value):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    manifest_path = Path(applied["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration manifest fields are invalid",
    ):
        hermes_integration.rollback_integration(
            manifest_path,
            expected_config_path=request.config_path,
            expected_skills_target=request.skills_target,
        )


def test_rollback_rejects_manifest_missing_required_config_backup(tmp_path):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    applied = hermes_integration.apply_integration(request)
    manifest_path = Path(applied["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["config_backup"] = None
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    applied_config = request.config_path.read_bytes()

    with pytest.raises(
        hermes_integration.HermesIntegrationError,
        match="integration manifest fields are incomplete",
    ):
        hermes_integration.rollback_integration(
            manifest_path,
            expected_config_path=request.config_path,
            expected_skills_target=request.skills_target,
        )

    assert request.config_path.read_bytes() == applied_config


def test_apply_failure_before_skill_backup_preserves_existing_target(tmp_path, monkeypatch):
    from podcast_ingest_core import hermes_integration

    request = _make_request(tmp_path)
    request.skills_target.mkdir()
    for name in SYNCED_SKILLS:
        _write_skill(request.skills_target, name, "previous")
    original_skills = hermes_integration.tree_digest(request.skills_target)

    def fail_config_backup(*args, **kwargs):
        del args, kwargs
        raise OSError("synthetic early backup failure")

    monkeypatch.setattr(hermes_integration.shutil, "copy2", fail_config_backup)

    with pytest.raises(hermes_integration.HermesIntegrationError):
        hermes_integration.apply_integration(request)

    assert hermes_integration.tree_digest(request.skills_target) == original_skills


def test_management_script_exposes_plan_apply_and_rollback():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "manage_hermes_integration.py"
    )
    text = script.read_text(encoding="utf-8")

    assert 'add_parser("plan"' in text
    assert 'add_parser("apply"' in text
    assert 'add_parser("rollback"' in text
    assert "print(json.dumps" in text


def test_red_synced_set_adds_the_composite_skill_without_widening_the_027_allowlist(
    tmp_path,
):
    """Spec 023's orchestrator Skill ships, but is not a Spec 027 contracted Skill.

    Spec 027 binds each contracted Skill to exactly one registry tool and rejects
    any artifact that mentions another tool.  The historical-path Skill names four
    tools by design, so it is synchronized without entering that allowlist.
    """

    from podcast_ingest_core import hermes_integration
    from podcast_ingest_core.hermes_integration import apply_integration

    historical = "historical-episode-verified-report-path"

    assert historical not in hermes_integration.MANAGED_SKILLS
    assert hermes_integration.SYNCED_SKILLS == (
        hermes_integration.MANAGED_SKILLS + (historical,)
    )

    request = _make_request(tmp_path)
    apply_integration(request)

    assert (request.skills_target / historical / "SKILL.md").is_file()
    assert sorted(path.name for path in request.skills_target.iterdir()) == sorted(
        hermes_integration.SYNCED_SKILLS
    )
