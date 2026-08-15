"""Spec032 closed command/metadata boundary tests; no Docker is run."""
from __future__ import annotations


def test_closed_definition_is_not_an_executable_docker_command_or_live_image_claim():
    from podcast_ingest_core import hermes_g2_docker_commands as commands

    command = commands.build_closed_docker_command(commands.Spec032DockerOperation.ACTIVATE_ONCE)
    assert command is not None
    assert not hasattr(commands, "render_closed_docker_argv")
    assert commands.build_closed_docker_command({"argv": "raw"}) is None
    object.__setattr__(command, "operation", object())
    assert commands.is_factory_issued_closed_docker_command(command) is False


def test_metadata_allowlist_is_bounded_and_poison_safe():
    from podcast_ingest_core import hermes_g2_docker_commands as commands
    from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES

    candidate = commands.issue_bounded_metadata_candidate(
        True, REQUIRED_TMPFS_ROLES, 0, 0, 0, True, True, True, True, True, True, 0, 0, 0
    )
    assert commands.parse_bounded_metadata(candidate).status is commands.Spec032MetadataStatus.PASS

    class Poison:
        def __hash__(self):
            raise AssertionError("hash")

        def __eq__(self, _other):
            raise AssertionError("equal")

    assert commands.parse_bounded_metadata(Poison()).status is commands.Spec032MetadataStatus.QUARANTINED


def test_mutated_factory_issued_state_with_hostile_key_fails_closed_without_raising():
    from podcast_ingest_core import hermes_g2_docker_commands as commands
    from podcast_ingest_core.hermes_runtime_controller_plan import REQUIRED_TMPFS_ROLES

    candidate = commands.issue_bounded_metadata_candidate(
        True, REQUIRED_TMPFS_ROLES, 0, 0, 0, True, True, True, True, True, True, 0, 0, 0
    )

    class HostileKey:
        def __hash__(self):
            return 1

        def __eq__(self, _other):
            raise BaseException("must not compare hostile keys")

    state = vars(candidate)
    state.pop("_factory_token")
    state[HostileKey()] = object()
    assert commands.parse_bounded_metadata(candidate).status is commands.Spec032MetadataStatus.QUARANTINED

    command = commands.build_closed_docker_command(commands.Spec032DockerOperation.ACTIVATE_ONCE)
    command_state = vars(command)
    command_state.pop("operation")
    command_state[HostileKey()] = object()
    assert commands.is_factory_issued_closed_docker_command(command) is False


def test_future_driver_source_has_no_subprocess_edge_and_every_entry_is_unavailable():
    import ast
    from pathlib import Path

    driver_path = Path(__file__).resolve().parents[1] / "src/podcast_ingest_core/hermes_g2_docker_driver.py"
    tree = ast.parse(driver_path.read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.Import) and any(alias.name == "subprocess" for alias in node.names)
        or isinstance(node, ast.ImportFrom) and node.module == "subprocess"
        or isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"run", "Popen", "system"}
        for node in ast.walk(tree)
    )
    driver = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "FutureSpec032DockerDriver")
    methods = {node.name: node for node in driver.body if isinstance(node, ast.FunctionDef)}
    assert {"__init__", "_unavailable"} <= set(methods)
    assert all(any(isinstance(node, ast.Raise) for node in ast.walk(methods[name])) for name in ("__init__", "_unavailable"))
    aliases = {
        node.targets[0].id: node.value.id
        for node in driver.body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Name)
    }
    assert {name: aliases.get(name) for name in ("inspect_metadata", "activate_once", "rollback")} == {
        "inspect_metadata": "_unavailable", "activate_once": "_unavailable", "rollback": "_unavailable"
    }
