from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ConfigError, load_data_repo_config, load_runtime_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show runtime and data repository configuration.")
    parser.add_argument("--config", type=Path, default=None, help="Path to runtime config TOML")
    parser.add_argument("--code-repo", type=Path, default=Path.cwd(), help="Code repository root")
    return parser.parse_args()


def build_report(*, config_path: Path | None, code_repo: Path) -> dict[str, object]:
    runtime_config = load_runtime_config(config_path=config_path, code_repo=code_repo)
    data_config = load_data_repo_config(runtime_config.data_repo)
    return {
        "ok": True,
        "code_repo": str(runtime_config.code_repo),
        "data_repo": str(runtime_config.data_repo),
        "runtime_config_path": str(runtime_config.runtime_config_path),
        "profile": runtime_config.profile,
        "data_config_path": str(data_config.path),
        "schema_version": data_config.schema_version,
        "paths": data_config.paths,
        "resolved_paths": data_config.resolved_paths,
        "projects": sorted(data_config.projects.keys()),
    }


def main() -> int:
    args = parse_args()
    try:
        report = build_report(config_path=args.config, code_repo=args.code_repo)
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
