from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_runtime_config, load_data_repo_config, ConfigError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show runtime and data-repo configuration.")
    parser.add_argument("--config", type=Path, default=None, help="Path to runtime config.toml")
    parser.add_argument("--code-repo", type=Path, default=Path.cwd(), help="Code repository root")
    return parser.parse_args()


def build_report(*, config_path: Path | None, code_repo: Path) -> dict:
    runtime = load_runtime_config(config_path, code_repo=code_repo)
    data_cfg = load_data_repo_config(runtime.data_repo)
    return {
        "ok": True,
        "code_repo": str(runtime.code_repo),
        "data_repo": str(runtime.data_repo),
        "runtime_config_path": str(runtime.runtime_config_path),
        "profile": runtime.profile,
        "data_config_path": str(data_cfg.path),
        "schema_version": data_cfg.schema_version,
        "paths": data_cfg.paths,
        "projects": sorted(data_cfg.projects.keys()),
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
