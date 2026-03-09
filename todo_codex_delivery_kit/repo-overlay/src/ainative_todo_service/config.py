from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


class ConfigError(RuntimeError):
    """Raised when runtime or data-repo configuration is invalid."""


@dataclass(frozen=True)
class RuntimeConfig:
    code_repo: Path
    data_repo: Path
    runtime_config_path: Path
    profile: str = "default"


@dataclass(frozen=True)
class DataRepoConfig:
    path: Path
    raw: dict

    @property
    def schema_version(self) -> int:
        return int(self.raw.get("schema_version", 1))

    @property
    def paths(self) -> dict:
        return dict(self.raw.get("paths", {}))

    @property
    def projects(self) -> dict:
        return dict(self.raw.get("projects", {}))


def default_runtime_config_path() -> Path:
    env = os.getenv("AINATIVE_TODO_CONFIG")
    if env:
        return Path(env).expanduser()
    return Path("~/.config/ainative-todo/config.toml").expanduser()


def _read_toml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


def load_runtime_config(config_path: Path | None = None, code_repo: Path | None = None) -> RuntimeConfig:
    config_path = (config_path or default_runtime_config_path()).expanduser().resolve()
    raw = _read_toml(config_path)
    data_repo_value = raw.get("data_repo")
    if not data_repo_value:
        raise ConfigError(f"'data_repo' is required in {config_path}")
    data_repo = Path(str(data_repo_value)).expanduser().resolve()
    if not data_repo.exists():
        raise ConfigError(f"Configured data_repo does not exist: {data_repo}")

    resolved_code_repo = (code_repo or Path.cwd()).resolve()
    return RuntimeConfig(
        code_repo=resolved_code_repo,
        data_repo=data_repo,
        runtime_config_path=config_path,
        profile=str(raw.get("profile", "default")),
    )


def load_data_repo_config(data_repo: Path, filename: str = "todo.config.toml") -> DataRepoConfig:
    path = data_repo / filename
    raw = _read_toml(path)
    return DataRepoConfig(path=path, raw=raw)
