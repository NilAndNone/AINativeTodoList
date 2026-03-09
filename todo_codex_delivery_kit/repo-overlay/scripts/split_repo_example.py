#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


COPY_TARGETS = [
    "data",
    "today.md",
    "daily",
    "reports",
    "projects",
]


DEFAULT_TODO_CONFIG = """
schema_version = 1

[paths]
task_store = "data/tasks.csv"
today_file = "today.md"
daily_dir = "daily"
reports_dir = "reports"
projects_dir = "projects"

[storage]
format = "csv"

[workflow]
require_confirm_before_write = true
today_mode = "primary-workbench"

[git]
auto_commit_on_close_day = true
auto_push_on_close_day = true
commit_message = "chore(todo): close day {date}"

[defaults.new_task]
project = "MISC"
priority = "P2"
status = "todo"
""".strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy todo data artifacts into a separate data repository.")
    parser.add_argument("--source", type=Path, required=True, help="Current combined repository root")
    parser.add_argument("--target", type=Path, required=True, help="Target data repository root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target files")
    return parser.parse_args()


def copy_entry(source_root: Path, target_root: Path, name: str, force: bool) -> None:
    source = source_root / name
    if not source.exists():
        return
    target = target_root / name
    if target.exists():
        if not force:
            raise FileExistsError(f"Target already exists: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    if source.is_dir():
        shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    target = args.target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    for name in COPY_TARGETS:
        copy_entry(source, target, name, force=args.force)

    todo_config = target / "todo.config.toml"
    if not todo_config.exists() or args.force:
        todo_config.write_text(DEFAULT_TODO_CONFIG, encoding="utf-8")

    readme = target / "README.md"
    if not readme.exists() or args.force:
        readme.write_text(
            "# AINative Todo Data Repo\n\nThis repository stores the user's task data and generated artifacts.\n",
            encoding="utf-8",
        )

    print(f"Data repository initialized at: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
