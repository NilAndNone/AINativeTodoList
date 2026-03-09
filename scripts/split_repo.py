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
auto_commit_on_close_day = false
auto_push_on_close_day = false
commit_message = "chore(todo): close day {date}"

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
""".strip() + "\n"

DEFAULT_README = """# AINative Todo Data Repo

This repository stores the user's task data and generated artifacts.
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


def write_default_files(target_root: Path, force: bool) -> None:
    todo_config = target_root / "todo.config.toml"
    if not todo_config.exists() or force:
        todo_config.write_text(DEFAULT_TODO_CONFIG, encoding="utf-8")

    readme = target_root / "README.md"
    if not readme.exists() or force:
        readme.write_text(DEFAULT_README, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_root = args.source.resolve()
    target_root = args.target.resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    for name in COPY_TARGETS:
        copy_entry(source_root, target_root, name, force=args.force)

    write_default_files(target_root, force=args.force)

    print(f"Data repository initialized at: {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
