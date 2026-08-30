from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import LLMProviderConfigError

DEFAULT_LOCAL_ENV_PATH = Path(".env")
_ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class LocalEnvLoadResult:
    """Metadata about local .env loading without secret values."""

    path: Path
    loaded: bool
    loaded_env_var_names: list[str]
    skipped_env_var_names: list[str]


def load_local_env(path: str | Path = DEFAULT_LOCAL_ENV_PATH, *, override: bool = False) -> LocalEnvLoadResult:
    """Load a simple local .env file into os.environ without exposing values."""

    env_path = Path(path)
    if not env_path.exists():
        return LocalEnvLoadResult(
            path=env_path,
            loaded=False,
            loaded_env_var_names=[],
            skipped_env_var_names=[],
        )

    loaded_names: list[str] = []
    skipped_names: list[str] = []
    for line_number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), start=1):
        parsed = _parse_env_line(raw_line, line_number=line_number, path=env_path)
        if parsed is None:
            continue
        name, value = parsed
        if not override and name in os.environ:
            skipped_names.append(name)
            continue
        os.environ[name] = value
        loaded_names.append(name)

    return LocalEnvLoadResult(
        path=env_path,
        loaded=True,
        loaded_env_var_names=loaded_names,
        skipped_env_var_names=skipped_names,
    )


def local_env_metadata(result: LocalEnvLoadResult) -> dict[str, object]:
    """Return JSON-safe .env metadata without secret values."""

    return {
        "env_file_loaded": result.loaded,
        "env_file_path": str(result.path),
        "loaded_env_var_names": result.loaded_env_var_names,
        "skipped_env_var_names": result.skipped_env_var_names,
    }


def empty_local_env_result(path: str | Path = DEFAULT_LOCAL_ENV_PATH) -> LocalEnvLoadResult:
    """Build metadata for --no-env-file without touching the filesystem."""

    return LocalEnvLoadResult(
        path=Path(path),
        loaded=False,
        loaded_env_var_names=[],
        skipped_env_var_names=[],
    )


def _parse_env_line(raw_line: str, *, line_number: int, path: Path) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export ") :].strip()
    if "=" not in line:
        raise LLMProviderConfigError(f"invalid .env line {line_number} in {path}: expected KEY=VALUE")

    name, value = line.split("=", 1)
    name = name.strip()
    value = value.strip()
    if not _ENV_NAME_PATTERN.fullmatch(name):
        raise LLMProviderConfigError(f"invalid .env line {line_number} in {path}: invalid variable name")
    return name, _unquote_value(value, line_number=line_number, path=path)


def _unquote_value(value: str, *, line_number: int, path: Path) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value.startswith(("'", '"')) or value.endswith(("'", '"')):
        raise LLMProviderConfigError(f"invalid .env line {line_number} in {path}: unterminated quoted value")
    return value
