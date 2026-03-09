from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib


RUNTIME_ENV_VAR = "AINATIVE_TODO_CONFIG"
DEFAULT_RUNTIME_CONFIG = Path("~/.config/ainative-todo/config.toml").expanduser()
DATA_CONFIG_FILENAME = "todo.config.toml"
REQUIRED_PATH_KEYS = (
    "task_store",
    "today_file",
    "daily_dir",
    "reports_dir",
    "projects_dir",
)


class ConfigError(RuntimeError):
    """Raised when runtime or data repository configuration is invalid."""


@dataclass(frozen=True)
class RuntimeConfig:
    code_repo: Path
    data_repo: Path
    runtime_config_path: Path
    profile: str = "default"


@dataclass(frozen=True)
class DataRepoConfig:
    data_repo: Path
    path: Path
    raw: dict[str, object]

    @property
    def schema_version(self) -> int:
        return int(self.raw.get("schema_version", 1))

    @property
    def paths(self) -> dict[str, str]:
        value = self.raw.get("paths", {})
        if not isinstance(value, dict):
            raise ConfigError(f"'paths' must be a table in {self.path}")
        return {str(key): str(path_value) for key, path_value in value.items()}

    @property
    def resolved_paths(self) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for key, relative_path in self.paths.items():
            resolved[key] = str((self.data_repo / relative_path).resolve())
        return resolved

    @property
    def projects(self) -> dict[str, dict[str, str]]:
        value = self.raw.get("projects", {})
        if not isinstance(value, dict):
            raise ConfigError(f"'projects' must be a table in {self.path}")
        normalized: dict[str, dict[str, str]] = {}
        for key, item in value.items():
            if not isinstance(item, dict):
                raise ConfigError(f"Project '{key}' must be a table in {self.path}")
            normalized[str(key)] = {str(item_key): str(item_value) for item_key, item_value in item.items()}
        return normalized

    def resolve_path(self, key: str) -> Path:
        relative_path = self.paths.get(key)
        if relative_path is None:
            raise ConfigError(f"Missing path '{key}' in {self.path}")
        return (self.data_repo / relative_path).resolve()


def default_runtime_config_path() -> Path:
    value = os.getenv(RUNTIME_ENV_VAR)
    if value:
        return Path(value).expanduser()
    return DEFAULT_RUNTIME_CONFIG


def _read_toml(path: Path) -> dict[str, object]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


def load_runtime_config(config_path: Path | None = None, code_repo: Path | None = None) -> RuntimeConfig:
    resolved_path = (config_path or default_runtime_config_path()).expanduser().resolve()
    raw = _read_toml(resolved_path)
    data_repo_value = raw.get("data_repo")
    if not data_repo_value:
        raise ConfigError(f"'data_repo' is required in {resolved_path}")

    data_repo = Path(str(data_repo_value)).expanduser().resolve()
    if not data_repo.exists():
        raise ConfigError(f"Configured data_repo does not exist: {data_repo}")

    resolved_code_repo = (code_repo or Path.cwd()).resolve()
    return RuntimeConfig(
        code_repo=resolved_code_repo,
        data_repo=data_repo,
        runtime_config_path=resolved_path,
        profile=str(raw.get("profile", "default")),
    )


def load_data_repo_config(data_repo: Path, filename: str = DATA_CONFIG_FILENAME) -> DataRepoConfig:
    resolved_repo = data_repo.expanduser().resolve()
    path = resolved_repo / filename
    raw = _read_toml(path)
    config = DataRepoConfig(data_repo=resolved_repo, path=path, raw=raw)

    missing_keys = [key for key in REQUIRED_PATH_KEYS if key not in config.paths]
    if missing_keys:
        raise ConfigError(f"Missing required path keys in {path}: {missing_keys}")
    return config
