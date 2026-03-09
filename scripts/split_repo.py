#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


COPY_TARGETS = (
    "data",
    "today.md",
    "daily",
    "reports",
    "projects",
)

DEFAULT_COMMIT_MESSAGE = "chore(todo): close day {date}"
DEFAULT_README = """# AINative Todo Data Repo

This repository stores the user's task data and generated artifacts.

## First Run

1. Point the code repo runtime config at this directory.
2. Run `python3 -m ainative_todo_service.doctor`.
3. If you want close-day git automation, initialize this directory as a git repo and enable it in `todo.config.toml`.
"""


def repo_root_from(script_path: Path) -> Path:
    return script_path.resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy todo data artifacts into a separate data repository.")
    parser.add_argument(
        "--source",
        type=Path,
        default=repo_root_from(Path(__file__)),
        help="Current combined repository root",
    )
    parser.add_argument("--target", type=Path, required=True, help="Target data repository root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target files")
    parser.add_argument(
        "--remove-source-data",
        action="store_true",
        help="Delete migrated data artifacts from the source repo after a successful copy.",
    )
    parser.add_argument(
        "--runtime-config-out",
        type=Path,
        default=None,
        help="Optional runtime config TOML to write for the code repository.",
    )
    parser.add_argument(
        "--auto-commit-on-close-day",
        action="store_true",
        help="Enable close-day git commit in the generated todo.config.toml.",
    )
    parser.add_argument(
        "--auto-push-on-close-day",
        action="store_true",
        help="Enable close-day git push in the generated todo.config.toml.",
    )
    parser.add_argument(
        "--git-commit-message",
        default=DEFAULT_COMMIT_MESSAGE,
        help="Commit message template for close-day git automation.",
    )
    return parser.parse_args()


def toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_default_todo_config(*, auto_commit: bool, auto_push: bool, commit_message: str) -> str:
    return (
        f"""
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
auto_commit_on_close_day = {"true" if auto_commit else "false"}
auto_push_on_close_day = {"true" if auto_push else "false"}
commit_message = {toml_string(commit_message)}

[defaults.new_task]
project = "MISC"
priority = "P2"
status = "todo"

[projects.UTC]
name = "单测客户端"
file = "unit-test-client.md"
focus = "客户端工程实现、稳定性、性能、监控与离线流程建设。"

[projects.HYP]
name = "半年工作安排"
file = "half-year-plan.md"
focus = "未来半年的工作主线、阶段性交付节奏与整体规划口径。"

[projects.TAR]
name = "团队成员工作安排"
file = "team-arrangement.md"
focus = "个人工作安排与团队成员承接方向的阶段性拆解。"

[projects.HYE]
name = "混元单测评测"
file = "hunyuan-evaluation.md"
focus = "模型评测事项记录、整理与边界维护。"

[projects.AGE]
name = "单测评测"
file = "agent-evaluation.md"
focus = "单元测试代码生成 agent 的评测框架与阶段性输出。"

[projects.MISC]
name = "杂项"
file = "misc.md"
focus = "临时支持、会议、沟通和跨项目事项。"
""".strip()
        + "\n"
    )


def build_runtime_config(data_repo: Path) -> str:
    return f'profile = "default"\ndata_repo = {toml_string(str(data_repo.resolve()))}\n'


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


def remove_source_entry(source_root: Path, name: str) -> None:
    source = source_root / name
    if not source.exists():
        return
    if source.is_dir():
        shutil.rmtree(source)
    else:
        source.unlink()


def write_default_files(
    target_root: Path,
    *,
    force: bool,
    auto_commit_on_close_day: bool,
    auto_push_on_close_day: bool,
    git_commit_message: str,
) -> None:
    todo_config = target_root / "todo.config.toml"
    if not todo_config.exists() or force:
        todo_config.write_text(
            build_default_todo_config(
                auto_commit=auto_commit_on_close_day,
                auto_push=auto_push_on_close_day,
                commit_message=git_commit_message,
            ),
            encoding="utf-8",
        )

    readme = target_root / "README.md"
    if not readme.exists() or force:
        readme.write_text(DEFAULT_README, encoding="utf-8")


def write_runtime_config_file(runtime_config_out: Path, data_repo: Path, force: bool) -> None:
    if runtime_config_out.exists() and not force:
        raise FileExistsError(f"Target already exists: {runtime_config_out}")
    runtime_config_out.parent.mkdir(parents=True, exist_ok=True)
    runtime_config_out.write_text(build_runtime_config(data_repo), encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_root = args.source.resolve()
    target_root = args.target.resolve()
    if source_root == target_root:
        raise ValueError("--source and --target must be different directories")
    target_root.mkdir(parents=True, exist_ok=True)

    for name in COPY_TARGETS:
        copy_entry(source_root, target_root, name, force=args.force)

    write_default_files(
        target_root,
        force=args.force,
        auto_commit_on_close_day=args.auto_commit_on_close_day,
        auto_push_on_close_day=args.auto_push_on_close_day,
        git_commit_message=args.git_commit_message,
    )
    if args.runtime_config_out is not None:
        write_runtime_config_file(args.runtime_config_out.resolve(), target_root, args.force)
    if args.remove_source_data:
        for name in COPY_TARGETS:
            remove_source_entry(source_root, name)

    print(f"Data repository initialized at: {target_root}")
    if args.runtime_config_out is not None:
        print(f"Runtime config written to: {args.runtime_config_out.resolve()}")
    if args.remove_source_data:
        print(f"Source data artifacts removed from: {source_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
